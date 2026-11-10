"""Lectura de rutinas y planes de nutrición desde documentos (sin IA).

Formatos: Word (.docx), PDF con texto, Excel (.xlsx), CSV, JSON y texto (.txt / .md).

Todo termina en el mismo formato que la importación por foto, para revisarlo en una
tabla antes de cargarlo en el sistema::

    {
      "es_plan": bool, "observaciones": str, "consejos": str,
      "entrenamiento": [{"etiqueta", "dia_semana", "enfoque",
                         "ejercicios": [{"nombre", "series", "reps", "descanso_seg",
                                         "peso_kg", "rir", "nota"}]}],
      "nutricion": [{"etiqueta", "dia_semana", "comidas": [{"comida", "alimentos", "kcal"}]}],
      "rutina_casa": dict | None,   # solo si el JSON es un respaldo del propio sistema
    }

La lectura es heurística: reconoce encabezados de día ("Lunes", "Día 1"), notaciones
como "4x12" o "4 series de 10", tablas con columnas tipo Ejercicio/Series/Reps o
Comida/Alimentos, y tablas "a lo ancho" con un día por columna.
"""

import io
import json
import re
import unicodedata

import plan_estado as pe

DIAS = pe.DIAS
SIN_DIA = "Sin especificar"
CAMPOS_EJERCICIO = ["nombre", "series", "reps", "descanso_seg", "peso_kg", "rir", "nota"]
TAMANO_MAXIMO = 20 * 1024 * 1024

EXTENSIONES = ["docx", "pdf", "xlsx", "xlsm", "csv", "json", "txt", "md"]


class ErrorDocumento(Exception):
    """Error con un mensaje listo para mostrar al usuario."""


# ==========================================================================
# Utilidades de texto
# ==========================================================================

def _sin_acentos(texto):
    texto = unicodedata.normalize("NFKD", str(texto))
    return "".join(c for c in texto if not unicodedata.combining(c)).lower().strip()


def _limpiar_celda(valor):
    if valor is None:
        return ""
    texto = str(valor).strip()
    if texto.lower() in ("nan", "none", "nat"):
        return ""
    if re.fullmatch(r"-?\d+\.0", texto):
        texto = texto[:-2]
    return texto


DIAS_CLAVE = {_sin_acentos(d): d for d in DIAS}
ABREVIATURAS_DIA = {"lun": "Lunes", "mar": "Martes", "mie": "Miércoles", "mier": "Miércoles", "x": "Miércoles",
                    "jue": "Jueves", "vie": "Viernes", "sab": "Sábado", "dom": "Domingo",
                    "monday": "Lunes", "tuesday": "Martes", "wednesday": "Miércoles", "thursday": "Jueves",
                    "friday": "Viernes", "saturday": "Sábado", "sunday": "Domingo"}


def dia_de_celda(texto):
    """Día si la celda es exactamente un día (o su abreviatura). Útil en encabezados."""
    t = _sin_acentos(texto).strip(" .:-")
    if t in DIAS_CLAVE:
        return DIAS_CLAVE[t]
    return ABREVIATURAS_DIA.get(t)


_RE_ENCABEZADO_DIA = re.compile(
    r"^(?:d[ií]a\s+\d+\s*[-:,(]?\s*)?(lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado|domingo)\b[\s:.\-–)]*(.*)$",
    re.IGNORECASE)
_RE_ENCABEZADO_SESION = re.compile(
    r"^((?:d[ií]a|sesi[oó]n|rutina|entreno|entrenamiento|workout|day|semana\s+\d+\s+d[ií]a)\s*[0-9A-Za-z]{1,2})\b[\s:.\-–)]*(.*)$",
    re.IGNORECASE)


def encabezado_dia(linea):
    """(etiqueta, dia_semana, resto) si la línea abre un día o sesión; si no, None."""
    texto = linea.strip().strip("*#=_ ").strip()
    if not texto or len(texto) > 70:
        return None
    m = _RE_ENCABEZADO_DIA.match(texto)
    if m:
        dia = DIAS_CLAVE[_sin_acentos(m.group(1))]
        return texto, dia, m.group(2).strip(" -:()")
    m = _RE_ENCABEZADO_SESION.match(texto)
    if m and not re.search(r"\d+\s*[xX×]\s*\d+", texto):
        return texto, SIN_DIA, m.group(2).strip(" -:()")
    return None


SECCIONES = {
    "entrenamiento": ["entrenamiento", "rutina", "ejercicios", "training", "workout", "plan de entreno"],
    "nutricion": ["alimentacion", "nutricion", "dieta", "plan alimenticio", "menu", "comidas", "plan nutricional"],
    "consejos": ["consejos", "recomendaciones", "indicaciones generales", "notas", "tips", "observaciones"],
}


def seccion_de(linea):
    t = _sin_acentos(linea).strip(" :*#=-_")
    if not t or len(t) > 45 or re.search(r"\d+\s*x\s*\d+", t):
        return None
    for seccion, claves in SECCIONES.items():
        for clave in claves:
            if t == clave or t.startswith(clave + " ") or t.startswith("plan de " + clave) or t.endswith(" " + clave):
                return seccion
    return None


COMIDAS_CLAVE = ["desayuno", "media manana", "almuerzo", "comida", "merienda", "cena", "colacion", "snack",
                 "pre entreno", "pre-entreno", "preentreno", "post entreno", "post-entreno", "postentreno",
                 "refrigerio", "onces", "brunch", "antes de dormir", "recena", "lunch", "dinner", "breakfast"]
_RE_KCAL = re.compile(r"(\d{2,4})\s*(?:kcal|calor[ií]as|cal)\b", re.IGNORECASE)


def linea_comida(linea):
    """(comida, alimentos, kcal) si la línea empieza con un tiempo de comida."""
    texto = linea.strip().lstrip("-•*·▪◦> ").strip()
    t = _sin_acentos(texto)
    for clave in sorted(COMIDAS_CLAVE, key=len, reverse=True):
        if t.startswith(clave):
            resto_original = texto[len(clave):]
            m_num = re.match(r"\s*(\d{1,2})\b", resto_original)
            nombre = texto[:len(clave)]
            if m_num:
                nombre += " " + m_num.group(1)
                resto_original = resto_original[m_num.end():]
            if resto_original and resto_original[0].isalpha():
                return None  # "Comidas rápidas..." no es un tiempo de comida
            m_hora = re.match(r"\s*\(?\s*\d{1,2}[:.h]\d{0,2}\s*(?:am|pm|hrs?)?\s*\)?", resto_original, re.I)
            if m_hora:
                resto_original = resto_original[m_hora.end():]
            alimentos = resto_original.strip(" :.-–=")
            kcal = ""
            m = _RE_KCAL.search(alimentos)
            if m:
                kcal = m.group(1)
                alimentos = (alimentos[:m.start()] + alimentos[m.end():]).strip(" ,;()-")
            return nombre.strip().capitalize(), alimentos, kcal
    return None


# ---------------------------------------------------------------- ejercicios

_RE_SXR = re.compile(
    r"(\d{1,2})\s*[xX×*]\s*(\d{1,3}(?:\s*[-–/a]\s*\d{1,3})?(?:\s*(?:s|seg|segundos|\"|''|min)\b)?|al fallo|amrap)",
    re.IGNORECASE)
_RE_SERIES_DE = re.compile(
    r"(\d{1,2})\s*(?:series|sets|serie|vueltas|rondas)\s*(?:de|x|of|×)?\s*"
    r"(\d{1,3}(?:\s*[-–/a]\s*\d{1,3})?(?:\s*(?:s|seg|segundos|min)\b)?)?\s*(?:repeticiones|reps|rep)?",
    re.IGNORECASE)
_RE_REPS = re.compile(r"(\d{1,3}(?:\s*[-–]\s*\d{1,3})?)\s*(?:repeticiones|reps|rep)\b", re.IGNORECASE)
_RE_DESCANSO = re.compile(
    r"(?:descanso|desc\.?|rest|pausa|recuperaci[oó]n)\s*[:\-=]?\s*(\d+(?:[.,]\d+)?)\s*(min|minutos|m|seg|segundos|s|\"|'')?"
    r"|(\d+(?:[.,]\d+)?)\s*(seg|segundos|s|\"|'')\s*(?:de\s+)?(?:descanso|desc|rest)",
    re.IGNORECASE)
_RE_SEG = re.compile(r"(\d{2,3})\s*(?:seg|sec)\b", re.IGNORECASE)
_RE_PESO = re.compile(r"(\d{1,3}(?:[.,]\d+)?)\s*(kg|kgs|kilos|lb|lbs|libras)\b", re.IGNORECASE)
_RE_RIR = re.compile(r"\b(rir|rpe)\s*[:=]?\s*(\d{1,2}(?:\s*[-–]\s*\d{1,2})?)", re.IGNORECASE)
_RE_VINETA = re.compile(r"^\s*(?:[-•*·▪◦>]+|\d{1,2}\s*[.)-]|[a-zA-Z]\d?\s*[.)])\s*")


def segundos(valor):
    """'1 min' -> '60', '90s' -> '90', '1:30' -> '90'. Vacío si no se entiende."""
    t = _sin_acentos(valor).replace(",", ".")
    if not t:
        return ""
    m = re.fullmatch(r"(\d+):(\d{2})", t)
    if m:
        return str(int(m.group(1)) * 60 + int(m.group(2)))
    m = re.search(r"(\d+(?:\.\d+)?)\s*(minutos|minuto|min|''|'|segundos|seg|sec|s|\"|m)?", t)
    if not m:
        return ""
    numero = float(m.group(1))
    unidad = m.group(2) or ""
    if unidad in ("minutos", "minuto", "min", "m", "'") or (not unidad and numero <= 5):
        numero *= 60  # un "2" suelto en una columna de descanso son minutos
    return str(int(round(numero)))


def kilos(valor):
    t = _sin_acentos(valor).replace(",", ".")
    m = re.search(r"(\d+(?:\.\d+)?)", t)
    if not m:
        return ""
    numero = float(m.group(1))
    if re.search(r"\b(lb|lbs|libras)\b", t):
        numero = round(numero * 0.4536 * 2) / 2
    return str(int(numero)) if float(numero).is_integer() else str(numero)


def _limpiar_nombre(texto):
    texto = _RE_VINETA.sub("", texto)
    texto = re.sub(r"\s{2,}", " ", texto)
    texto = texto.strip(" -–:|,;.()[]/")
    if texto and texto.isupper() and len(texto) > 3:
        texto = texto.capitalize()
    return texto[:120]


def parsear_ejercicio(linea, exigir_numeros=True):
    """Convierte 'Sentadilla 4x12 descanso 90s 60kg' en un ejercicio. None si no lo parece."""
    original = linea.strip()
    if not original or len(original) > 220:
        return None
    resto = original
    ej = {c: "" for c in CAMPOS_EJERCICIO}
    encontrado = False

    for patron, accion in ((_RE_DESCANSO, "descanso"), (_RE_PESO, "peso"), (_RE_RIR, "rir")):
        m = patron.search(resto)
        if not m:
            continue
        if accion == "descanso":
            numero = m.group(1) or m.group(3)
            unidad = (m.group(2) or m.group(4) or "").lower()
            ej["descanso_seg"] = segundos(numero + (" min" if unidad.startswith("m") else " s"))
        elif accion == "peso":
            ej["peso_kg"] = kilos(m.group(0))
        else:
            if m.group(1).lower() == "rir":
                ej["rir"] = re.sub(r"\s", "", m.group(2))
            else:
                ej["nota"] = f"RPE {m.group(2)}"
        resto = resto[:m.start()] + " " + resto[m.end():]

    def _separar(m):
        """Lo que va antes de '4x12' es el nombre; lo de después ('cada pierna') va a la nota."""
        antes, despues = resto[:m.start()], resto[m.end():]
        limpio = re.sub(r"\b(?:sets?|series|reps?|repeticiones)\b", " ", despues, flags=re.IGNORECASE).strip(" -|,;.")
        if re.search(r"[a-zA-Záéíóúñ]{3,}", antes) and re.search(r"[a-zA-Záéíóúñ]{3,}", limpio):
            ej["nota"] = (ej["nota"] + " " + limpio).strip()
            return antes
        return antes + " " + despues

    m = _RE_SXR.search(resto)
    if m:
        ej["series"], ej["reps"] = m.group(1), re.sub(r"\s+", " ", m.group(2)).replace("segundos", "s").replace("seg", "s")
        resto = _separar(m)
        encontrado = True
    else:
        m = _RE_SERIES_DE.search(resto)
        if m:
            ej["series"] = m.group(1)
            if m.group(2):
                ej["reps"] = re.sub(r"\s+", " ", m.group(2))
            resto = _separar(m)
            encontrado = True
        m = _RE_REPS.search(resto)
        if m and not ej["reps"]:
            ej["reps"] = re.sub(r"\s+", "", m.group(1))
            resto = resto[:m.start()] + " " + resto[m.end():]
            encontrado = True
    if not ej["descanso_seg"]:
        m = _RE_SEG.search(resto)
        if m and encontrado:
            ej["descanso_seg"] = m.group(1)
            resto = resto[:m.start()] + " " + resto[m.end():]

    # Texto entre paréntesis o tras un separador largo se toma como nota
    m = re.search(r"\(([^)]{3,})\)", resto)
    if m:
        ej["nota"] = (ej["nota"] + " " + m.group(1)).strip()
        resto = resto[:m.start()] + " " + resto[m.end():]
    resto = re.sub(r"\b(?:sets?|series|reps?|repeticiones|seg|kg)\b", " ", resto, flags=re.IGNORECASE)
    partes = re.split(r"\s[|–]\s|\s-\s(?=[a-záéíóú])", resto, maxsplit=1)
    nombre = _limpiar_nombre(partes[0])
    if len(partes) > 1 and len(partes[1].strip()) > 2:
        ej["nota"] = (ej["nota"] + " " + partes[1].strip(" -|")).strip()

    if not encontrado and exigir_numeros:
        return None
    if not nombre or not re.search(r"[a-zA-Záéíóúñ]{3,}", nombre):
        return ej if encontrado else None  # solo detalle: el nombre puede estar en la línea anterior
    ej["nombre"] = nombre
    return ej


# ==========================================================================
# Acumulador de resultados
# ==========================================================================

class _Plan:
    def __init__(self):
        self.entreno = []      # bloques en orden
        self.nutri = []
        self.consejos = []
        self.sin_usar = 0

    def _bloque(self, lista, etiqueta, dia, **extra):
        clave = (dia, etiqueta) if dia == SIN_DIA else (dia, None)
        for b in lista:
            if b["_clave"] == clave:
                for k, v in extra.items():
                    if v and not b.get(k):
                        b[k] = v
                return b
        b = {"_clave": clave, "etiqueta": etiqueta, "dia_semana": dia, **extra}
        lista.append(b)
        return b

    def bloque_entreno(self, etiqueta, dia, enfoque=""):
        b = self._bloque(self.entreno, etiqueta, dia, enfoque=enfoque)
        b.setdefault("ejercicios", [])
        return b

    def bloque_nutri(self, etiqueta, dia):
        b = self._bloque(self.nutri, etiqueta, dia)
        b.setdefault("comidas", [])
        return b

    def resultado(self, observaciones=""):
        entreno = [{k: v for k, v in b.items() if k != "_clave"} for b in self.entreno
                   if b["ejercicios"] or _sin_acentos(b.get("enfoque", "")).startswith("descanso")]
        nutri = [{k: v for k, v in b.items() if k != "_clave"} for b in self.nutri if b["comidas"]]
        for b in entreno:
            b.setdefault("enfoque", "")
            b["ejercicios"] = [{c: _limpiar_celda(e.get(c, "")) for c in CAMPOS_EJERCICIO} for e in b["ejercicios"]]
        consejos = "\n".join(self.consejos).strip()
        notas = [observaciones] if observaciones else []
        if self.sin_usar:
            notas.append(f"{self.sin_usar} líneas no se reconocieron como ejercicio ni comida; revisa que no falte nada.")
        return {
            "es_plan": bool(entreno or nutri or consejos),
            "observaciones": " ".join(notas),
            "entrenamiento": entreno, "nutricion": nutri, "consejos": consejos, "rutina_casa": None,
        }


# ==========================================================================
# Texto libre (Word, PDF, TXT)
# ==========================================================================

ALIAS_COLUMNAS = {
    "dia": ["dia", "dias", "day", "jornada", "sesion", "fecha"],
    "enfoque": ["enfoque", "grupo muscular", "musculo", "musculos", "grupo", "focus", "zona", "tipo"],
    "nombre": ["ejercicio", "ejercicios", "exercise", "movimiento", "nombre del ejercicio", "nombre"],
    "series": ["series", "serie", "sets", "set", "vueltas", "rondas"],
    "reps": ["reps", "repeticiones", "repeticion", "rep", "rango", "tiempo", "duracion", "reps/tiempo"],
    "descanso_seg": ["descanso", "desc", "rest", "pausa", "recuperacion", "descanso (s)", "descanso (seg)"],
    "peso_kg": ["peso", "kg", "carga", "weight", "peso (kg)", "kilos"],
    "rir": ["rir", "rpe", "intensidad"],
    "nota": ["nota", "notas", "observaciones", "observacion", "tecnica", "comentario", "comentarios",
             "indicaciones", "detalle", "tempo"],
    "comida": ["comida", "comidas", "tiempo de comida", "momento", "meal", "horario", "toma", "hora"],
    "alimentos": ["alimentos", "alimento", "menu", "descripcion", "opcion", "opciones", "platillo", "food",
                  "porcion", "porciones", "que comer", "contenido"],
    "kcal": ["kcal", "calorias", "cal", "energia", "calorias (kcal)"],
}


def _campo_columna(texto):
    t = _sin_acentos(texto).strip(" .:*")
    t = re.sub(r"\s+", " ", t)
    if not t:
        return None
    for campo, alias in ALIAS_COLUMNAS.items():
        if t in alias:
            return campo
    for campo, alias in ALIAS_COLUMNAS.items():
        if any(t.startswith(a + " ") or t.startswith(a + "(") for a in alias if len(a) > 3):
            return campo
    return None


def interpretar_texto(lineas, plan=None, titulo=""):
    plan = plan or _Plan()
    seccion = None
    etiqueta, dia, enfoque = (titulo, pe.normalizar_dia(titulo) or SIN_DIA, "") if titulo else ("", SIN_DIA, "")
    nombre_pendiente = None
    ultima_comida = None
    columnas_texto = None   # orden de columnas numéricas si el PDF trae una tabla como texto

    for bruta in lineas:
        linea = re.sub(r"[\t ]+", " ", str(bruta)).strip()
        if not linea:
            continue

        nueva = seccion_de(linea)
        if nueva:
            seccion, ultima_comida, nombre_pendiente = nueva, None, None
            etiqueta, dia, enfoque = "", SIN_DIA, ""
            columnas_texto = None
            continue

        cab = encabezado_dia(linea)
        if cab and seccion != "consejos":
            etiqueta, dia, enfoque = cab
            ultima_comida, nombre_pendiente = None, None
            if seccion != "nutricion" and enfoque:
                plan.bloque_entreno(etiqueta, dia, enfoque)
            continue

        if seccion == "consejos":
            plan.consejos.append(linea)
            continue

        # Encabezado de tabla convertido a texto: "Ejercicio Series Reps Descanso"
        palabras = [_campo_columna(p) for p in re.split(r"\s{1,}|\|", linea)]
        if palabras.count(None) <= 1 and sum(1 for p in palabras if p in ("series", "reps", "descanso_seg", "peso_kg", "rir")) >= 2:
            columnas_texto = [p for p in palabras if p in ("series", "reps", "descanso_seg", "peso_kg", "rir")]
            continue

        comida = linea_comida(linea) if seccion != "entrenamiento" else None
        if comida:
            b = plan.bloque_nutri(etiqueta or "Plan diario", dia)
            b["comidas"].append({"comida": comida[0], "alimentos": comida[1], "kcal": comida[2]})
            ultima_comida = b["comidas"][-1]
            continue

        if columnas_texto:
            m = re.match(r"^(.*?[A-Za-zÁÉÍÓÚáéíóúñÑ)\]])\s+((?:[\d.,/\-–]+\s*(?:s|seg|kg|min|\")?\s*){2,})$", linea)
            if m:
                valores = re.findall(r"[\d.,/\-–]+\s*(?:s|seg|kg|min|\")?", m.group(2))
                ej = {c: "" for c in CAMPOS_EJERCICIO}
                ej["nombre"] = _limpiar_nombre(m.group(1))
                for campo, valor in zip(columnas_texto, valores):
                    valor = valor.strip()
                    ej[campo] = segundos(valor) if campo == "descanso_seg" else kilos(valor) if campo == "peso_kg" else valor
                if ej["nombre"]:
                    plan.bloque_entreno(etiqueta or "Rutina", dia, enfoque)["ejercicios"].append(ej)
                    continue

        ej = parsear_ejercicio(linea) if seccion != "nutricion" else None
        if ej:
            if not ej["nombre"] and nombre_pendiente:
                ej["nombre"] = nombre_pendiente
            if ej["nombre"]:
                plan.bloque_entreno(etiqueta or "Rutina", dia, enfoque)["ejercicios"].append(ej)
                nombre_pendiente = None
                ultima_comida = None
                continue

        es_vineta = bool(_RE_VINETA.match(bruta if isinstance(bruta, str) else "")) or linea[:1] in "-•*·▪◦"
        if ultima_comida is not None and (es_vineta or seccion == "nutricion"):
            extra = _RE_VINETA.sub("", linea).strip()
            ultima_comida["alimentos"] = (ultima_comida["alimentos"] + ", " + extra).strip(", ")
            continue
        if seccion == "entrenamiento" and es_vineta and dia != SIN_DIA or (seccion == "entrenamiento" and es_vineta and etiqueta):
            nombre = _limpiar_nombre(linea)
            if nombre:
                ej = {c: "" for c in CAMPOS_EJERCICIO}
                ej["nombre"] = nombre
                plan.bloque_entreno(etiqueta or "Rutina", dia, enfoque)["ejercicios"].append(ej)
                continue
        if len(linea) <= 60 and re.search(r"[a-zA-Z]{3,}", linea) and not re.search(r"\d", linea):
            # Dos líneas de solo texto seguidas tras el día: la primera era el enfoque
            # ("LUNES" / "PIERNA - CUADRICEPS" / "SENTADILLA" / "4 SETS | 12 REPS")
            if nombre_pendiente and not enfoque and etiqueta:
                enfoque = nombre_pendiente
            nombre_pendiente = _limpiar_nombre(linea)
            continue
        plan.sin_usar += 1
    return plan


# ==========================================================================
# Tablas (Excel, CSV, Word)
# ==========================================================================

def _detectar_encabezado(filas):
    for i, fila in enumerate(filas[:8]):
        campos = [_campo_columna(c) for c in fila]
        reconocidos = [c for c in campos if c]
        if "nombre" in reconocidos and len(reconocidos) >= 2:
            return i, campos, "entreno"
        if ("alimentos" in reconocidos or "comida" in reconocidos) and len(reconocidos) >= 2:
            return i, campos, "nutri"
        dias = [dia_de_celda(c) for c in fila]
        if sum(1 for d in dias if d) >= 2:
            return i, dias, "ancha"
    return None


def interpretar_tabla(filas, plan=None, titulo=""):
    plan = plan or _Plan()
    filas = [[_limpiar_celda(c) for c in f] for f in filas]
    filas = [f for f in filas if any(f)]
    if not filas:
        return plan
    encontrado = _detectar_encabezado(filas)
    dia_titulo = pe.normalizar_dia(titulo.split()[0]) if titulo.strip() else None
    etiqueta_base = titulo.strip() or "Rutina"

    if not encontrado:
        lineas = []
        for f in filas:
            lineas.append(" ".join(c for c in f if c))
        return interpretar_texto(lineas, plan, titulo)

    inicio, campos, tipo = encontrado
    cuerpo = filas[inicio + 1:]

    if tipo == "ancha":
        columnas_dia = [(j, d) for j, d in enumerate(campos) if d]
        primera_col = [f[0] for f in cuerpo if f]
        es_nutri = sum(1 for c in primera_col if linea_comida(c + ":")) >= max(1, len(primera_col) // 2)
        for j, dia in columnas_dia:
            for f in cuerpo:
                if j >= len(f) or not f[j]:
                    continue
                if es_nutri:
                    comida = f[0] if columnas_dia[0][0] > 0 else ""
                    m = _RE_KCAL.search(f[j])
                    plan.bloque_nutri(dia, dia)["comidas"].append({
                        "comida": comida, "alimentos": _RE_KCAL.sub("", f[j]).strip(" ,;()"),
                        "kcal": m.group(1) if m else ""})
                else:
                    for parte in re.split(r"\n|;", f[j]):
                        if _sin_acentos(parte).startswith("descanso") and len(parte) < 20:
                            plan.bloque_entreno(dia, dia, "Descanso")
                            continue
                        ej = parsear_ejercicio(parte, exigir_numeros=False)
                        if ej and ej["nombre"]:
                            plan.bloque_entreno(dia, dia)["ejercicios"].append(ej)
        return plan

    idx = {}
    for j, campo in enumerate(campos):
        if campo and campo not in idx:
            idx[campo] = j

    def celda(fila, campo):
        j = idx.get(campo)
        return fila[j] if j is not None and j < len(fila) else ""

    dia_actual, etiqueta_actual, enfoque_actual = dia_titulo or SIN_DIA, etiqueta_base, ""
    for f in cuerpo:
        texto_dia = celda(f, "dia")
        if texto_dia:
            dia_actual = pe.normalizar_dia(texto_dia.split()[0]) or dia_de_celda(texto_dia) or SIN_DIA
            etiqueta_actual = texto_dia
            enfoque_actual = ""
        if celda(f, "enfoque"):
            enfoque_actual = celda(f, "enfoque")

        if tipo == "entreno":
            nombre = celda(f, "nombre")
            if not nombre:
                continue
            fila_encabezado = encabezado_dia(nombre)
            if fila_encabezado and not any(celda(f, c) for c in ("series", "reps")):
                etiqueta_actual, dia_actual, enfoque_actual = fila_encabezado
                continue
            ej = {c: celda(f, c) for c in CAMPOS_EJERCICIO}
            ej["nombre"] = _limpiar_nombre(nombre)
            if ej["series"] and not ej["reps"]:
                m = _RE_SXR.search(ej["series"])
                if m:
                    ej["series"], ej["reps"] = m.group(1), m.group(2)
            ej["descanso_seg"] = segundos(ej["descanso_seg"]) if ej["descanso_seg"] else ""
            ej["peso_kg"] = kilos(ej["peso_kg"]) if ej["peso_kg"] else ""
            if ej["nombre"]:
                plan.bloque_entreno(etiqueta_actual, dia_actual, enfoque_actual)["ejercicios"].append(ej)
        else:
            comida, alimentos = celda(f, "comida"), celda(f, "alimentos")
            if not (comida or alimentos):
                continue
            kcal = celda(f, "kcal")
            m = re.search(r"\d+", kcal)
            plan.bloque_nutri(etiqueta_actual if dia_actual != SIN_DIA or texto_dia else (titulo or "Plan diario"),
                              dia_actual)["comidas"].append(
                {"comida": comida, "alimentos": alimentos, "kcal": m.group(0) if m else ""})
    return plan


# ==========================================================================
# JSON
# ==========================================================================

ALIAS_JSON = {campo: set(alias) for campo, alias in ALIAS_COLUMNAS.items()}
ALIAS_JSON["nombre"] |= {"name", "titulo", "exercise_name"}
ALIAS_JSON["series"] |= {"sets"}
ALIAS_JSON["reps"] |= {"repetitions", "reps_o_tiempo"}
ALIAS_JSON["descanso_seg"] |= {"rest_seconds", "descanso_segundos", "rest_sec"}
ALIAS_JSON["comida"] |= {"tipo", "meal_name"}
ALIAS_JSON["alimentos"] |= {"items", "foods", "detalle"}


def _clave_campo(clave):
    t = _sin_acentos(clave).replace("_", " ").strip()
    for campo, alias in ALIAS_JSON.items():
        if t in alias or t.replace(" ", "_") in alias:
            return campo
    return None


def _a_texto(valor):
    if isinstance(valor, list):
        return ", ".join(_a_texto(v) for v in valor if v not in (None, ""))
    if isinstance(valor, dict):
        return ", ".join(f"{k}: {_a_texto(v)}" for k, v in valor.items())
    return _limpiar_celda(valor)


def _es_respaldo_sistema(data):
    return isinstance(data, dict) and any(
        re.fullmatch(r"(n|enf|ne|t|d|nc)_(" + "|".join(DIAS) + r")(_\d+)?", str(k)) for k in data)


def interpretar_respaldo(data):
    estado = pe.VistaEstado(data)
    plan = _Plan()
    for dia in DIAS:
        rutina = pe.leer_rutina_dia(estado, dia)
        if rutina["ejercicios"] or rutina["enfoque"]:
            b = plan.bloque_entreno(dia, dia, rutina["enfoque"])
            b["ejercicios"].extend(rutina["ejercicios"])
        comidas = pe.leer_comidas_dia(estado, dia)
        if comidas:
            plan.bloque_nutri(dia, dia)["comidas"].extend(comidas)
    if str(data.get("k_consejos", "")).strip():
        plan.consejos.append(str(data["k_consejos"]).strip())
    resultado = plan.resultado("Plantilla exportada desde Coach System Pro.")
    resultado["rutina_casa"] = pe.leer_rutina_casa(estado)
    if resultado["rutina_casa"]:
        resultado["es_plan"] = True
    return resultado


def interpretar_json(data):
    if _es_respaldo_sistema(data):
        return interpretar_respaldo(data)
    plan = _Plan()

    def recorrer(obj, etiqueta, dia, enfoque, seccion):
        if isinstance(obj, dict):
            campos = {_clave_campo(k): v for k, v in obj.items() if _clave_campo(k)}
            # ¿Es un ejercicio?
            if "nombre" in campos and any(c in campos for c in ("series", "reps", "descanso_seg", "peso_kg")) \
                    and seccion != "nutricion":
                ej = {c: _a_texto(campos.get(c, "")) for c in CAMPOS_EJERCICIO}
                ej["descanso_seg"] = segundos(ej["descanso_seg"]) if ej["descanso_seg"] else ""
                ej["peso_kg"] = kilos(ej["peso_kg"]) if ej["peso_kg"] else ""
                ej["nombre"] = _limpiar_nombre(ej["nombre"])
                plan.bloque_entreno(etiqueta or "Rutina", dia, enfoque)["ejercicios"].append(ej)
                return
            # ¿Es una comida? ({"comida": "Desayuno", "alimentos": "..."}). Si "comida" trae una
            # lista es un contenedor ({"comidas": [...]}) y se recorre más abajo.
            es_comida = (("comida" in campos or "alimentos" in campos)
                         and seccion != "entrenamiento"
                         and not isinstance(campos.get("comida"), (list, dict))
                         and not ("alimentos" not in campos and isinstance(campos.get("comida"), str)
                                  and len(obj) == 1))
            if es_comida:
                kcal = re.search(r"\d+", _a_texto(campos.get("kcal", "")))
                plan.bloque_nutri(etiqueta or "Plan diario", dia)["comidas"].append({
                    "comida": _a_texto(campos.get("comida", "")), "alimentos": _a_texto(campos.get("alimentos", "")),
                    "kcal": kcal.group(0) if kcal else ""})
                return
            if "dia" in campos and isinstance(campos["dia"], str):
                etiqueta = campos["dia"]
                dia = pe.normalizar_dia(campos["dia"].split()[0] if campos["dia"].split() else "") or SIN_DIA
            if "enfoque" in campos and isinstance(campos["enfoque"], str):
                enfoque = campos["enfoque"]
            for clave, valor in obj.items():
                t = _sin_acentos(clave)
                nueva_seccion = seccion
                for nombre_seccion, claves in SECCIONES.items():
                    if any(c in t for c in claves) or (nombre_seccion == "nutricion" and t in ("meals", "diet", "nutrition")) \
                            or (nombre_seccion == "entrenamiento" and t in ("exercises", "routine", "workouts")):
                        nueva_seccion = nombre_seccion
                        break
                if nueva_seccion == "consejos" and isinstance(valor, (str, list)):
                    plan.consejos.append(_a_texto(valor) if isinstance(valor, str) else "\n".join(_a_texto(v) for v in valor))
                    continue
                dia_clave = dia_de_celda(clave) or (pe.normalizar_dia(clave) if 3 <= len(clave) <= 12 else None)
                comida_clave = linea_comida(clave + ":") if nueva_seccion != "entrenamiento" else None
                if comida_clave and isinstance(valor, (str, list)) and not dia_clave:
                    alimentos = _a_texto(valor)
                    kcal = _RE_KCAL.search(alimentos)
                    plan.bloque_nutri(etiqueta or "Plan diario", dia)["comidas"].append({
                        "comida": comida_clave[0], "alimentos": _RE_KCAL.sub("", alimentos).strip(" ,;()"),
                        "kcal": kcal.group(1) if kcal else ""})
                elif dia_clave:
                    recorrer(valor, clave, dia_clave, "" if isinstance(valor, (list, dict)) else enfoque, nueva_seccion)
                elif isinstance(valor, (list, dict)):
                    recorrer(valor, etiqueta, dia, enfoque, nueva_seccion)
                elif isinstance(valor, str) and nueva_seccion != seccion and nueva_seccion != "consejos":
                    recorrer([valor], etiqueta, dia, enfoque, nueva_seccion)
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, str):
                    if seccion == "nutricion":
                        comida = linea_comida(item)
                        plan.bloque_nutri(etiqueta or "Plan diario", dia)["comidas"].append(
                            {"comida": comida[0], "alimentos": comida[1], "kcal": comida[2]} if comida
                            else {"comida": "", "alimentos": item, "kcal": ""})
                    else:
                        ej = parsear_ejercicio(item, exigir_numeros=False)
                        if ej and ej["nombre"]:
                            plan.bloque_entreno(etiqueta or "Rutina", dia, enfoque)["ejercicios"].append(ej)
                else:
                    recorrer(item, etiqueta, dia, enfoque, seccion)

    recorrer(data, "", SIN_DIA, "", None)
    return plan.resultado()


# ==========================================================================
# Lectura de archivos
# ==========================================================================

def _leer_docx(datos):
    import docx
    documento = docx.Document(io.BytesIO(datos))
    plan = _Plan()
    lineas, ultimo_titulo = [], ""
    for bloque in documento.iter_inner_content():
        if isinstance(bloque, docx.table.Table):
            filas = []
            for fila in bloque.rows:
                celdas, vistas = [], set()
                for c in fila.cells:  # las celdas combinadas se repiten
                    if id(c._tc) in vistas:
                        celdas.append("")
                        continue
                    vistas.add(id(c._tc))
                    celdas.append(c.text.strip())
                filas.append(celdas)
            interpretar_tabla(filas, plan, ultimo_titulo)
        else:
            texto = bloque.text.strip()
            if not texto:
                continue
            for parte in texto.split("\n"):
                es_lista = bloque.style is not None and "list" in (bloque.style.name or "").lower()
                lineas.append(("- " + parte) if es_lista else parte)
            if len(texto) <= 60:
                ultimo_titulo = texto
    interpretar_texto(lineas, plan)
    return plan.resultado(), "\n".join(lineas)


def _leer_pdf(datos):
    import pypdfium2 as pdfium
    try:
        documento = pdfium.PdfDocument(datos)
    except Exception as e:
        raise ErrorDocumento("No se pudo abrir el PDF. ¿Está protegido con contraseña o dañado?") from e
    paginas = []
    for pagina in documento:
        paginas.append(pagina.get_textpage().get_text_range())
    documento.close()
    texto = "\n".join(paginas).replace("\r", "\n")
    if len(re.sub(r"\s", "", texto)) < 20:
        raise ErrorDocumento("Este PDF no tiene texto (parece una foto o un escaneo). Usa "
                             "📸 Importar desde foto en la pestaña Entrenamiento, o la lectura con IA.")
    plan = interpretar_texto(texto.split("\n"))
    return plan.resultado(), texto


def _leer_excel(datos, nombre):
    import pandas as pd
    if nombre.endswith(".csv"):
        for codificacion in ("utf-8-sig", "latin-1"):
            try:
                hojas = {"": pd.read_csv(io.BytesIO(datos), header=None, dtype=str, sep=None,
                                         engine="python", encoding=codificacion)}
                break
            except UnicodeDecodeError:
                continue
    else:
        try:
            hojas = pd.read_excel(io.BytesIO(datos), sheet_name=None, header=None, dtype=str)
        except Exception as e:
            raise ErrorDocumento("No se pudo leer el Excel. Guárdalo como .xlsx e inténtalo de nuevo.") from e
    plan = _Plan()
    textos = []
    for nombre_hoja, df in hojas.items():
        filas = df.fillna("").values.tolist()
        titulo = "" if re.fullmatch(r"(hoja|sheet)\s*\d*", _sin_acentos(nombre_hoja or "hoja")) else str(nombre_hoja)
        interpretar_tabla(filas, plan, titulo)
        textos.append(f"[{nombre_hoja}]\n" + "\n".join(" | ".join(_limpiar_celda(c) for c in f) for f in filas))
    return plan.resultado(), "\n\n".join(textos)


def leer_documento(nombre, datos):
    """Devuelve (resultado, texto_extraido). El texto sirve para la lectura con IA."""
    if len(datos) > TAMANO_MAXIMO:
        raise ErrorDocumento("El archivo supera 20 MB.")
    nombre = (nombre or "").lower()
    extension = nombre.rsplit(".", 1)[-1] if "." in nombre else ""
    if extension in ("doc", "xls"):
        raise ErrorDocumento(f"El formato .{extension} es antiguo. Ábrelo y guárdalo como "
                             f".{'docx' if extension == 'doc' else 'xlsx'}.")
    if extension == "docx":
        return _leer_docx(datos)
    if extension == "pdf":
        return _leer_pdf(datos)
    if extension in ("xlsx", "xlsm", "csv"):
        return _leer_excel(datos, nombre)
    if extension == "json":
        try:
            data = json.loads(datos.decode("utf-8-sig"))
        except (UnicodeDecodeError, ValueError) as e:
            raise ErrorDocumento("El JSON no es válido.") from e
        return interpretar_json(data), json.dumps(data, ensure_ascii=False, indent=1)
    if extension in ("txt", "md"):
        try:
            texto = datos.decode("utf-8-sig")
        except UnicodeDecodeError:
            texto = datos.decode("latin-1")
        return interpretar_texto(texto.splitlines()).resultado(), texto
    raise ErrorDocumento("Formato no soportado. Usa Word (.docx), PDF, Excel (.xlsx), CSV, JSON o TXT.")
