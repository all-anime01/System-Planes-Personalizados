"""Puente entre el plan (datos estructurados) y las claves del formulario de Streamlit.

La app guarda cada campo en una clave de ``st.session_state`` (``n_Lunes_0``, ``s_Lunes_0``...).
Este módulo sabe leer esas claves como un plan ordenado y, al revés, convertir un plan
en el diccionario de claves que hay que escribir. Así la importación por foto y el
asistente de IA modifican exactamente los mismos campos que el usuario ve en pantalla.

Las funciones de escritura no tocan el estado: devuelven un diccionario de cambios
``{clave: valor}`` (``None`` = borrar la clave) que la app aplica al inicio del siguiente
ciclo, antes de dibujar los widgets (Streamlit no deja cambiar un widget ya dibujado).
"""

import json

DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
MAX_ITEMS = 20

# Valores que muestra el formulario cuando el campo nunca se tocó
DEFECTOS_EJERCICIO = {"s": "4", "r": "12", "g": "60", "p": "0"}
DEFECTO_CANTIDAD = 4

CLAVE_CAMBIOS = "_cambios_pendientes"
CLAVE_CASA = "casa_plan_json"
# Versión con las ediciones hechas en la tabla (la base solo cambia al generar o importar)
CLAVE_CASA_ACTUAL = "casa_actual_json"
CLAVE_CASA_VERSION = "casa_ver"

# campo lógico -> clave del formulario
CAMPOS_CLIENTE = {
    "nombre": "c_nombre",
    "edad": "c_edad",
    "sexo": "c_sexo",
    "peso_kg": "c_peso",
    "altura_cm": "c_altura",
    "actividad": "c_actividad",
    "objetivo": "k_objetivo",
    "nivel": "k_nivel",
    "dias_entreno": "k_dias_disp",
    "peso_meta_kg": "k_peso_meta",
    "grasa_meta_pct": "k_grasa_meta",
    "plazo": "k_plazo",
    "motivacion": "k_motivacion",
    "limitaciones": "k_limitaciones",
    "cuello_cm": "m_cuello",
    "cintura_cm": "m_cintura",
    "cadera_cm": "m_cadera",
    "grasa_medida_pct": "m_grasa_manual",
}


class VistaEstado:
    """Lectura del estado actual con los cambios todavía no aplicados por encima."""

    def __init__(self, base, pendientes=None):
        self.base = base
        self.pendientes = pendientes if pendientes is not None else {}

    def get(self, clave, defecto=None):
        if clave in self.pendientes:
            valor = self.pendientes[clave]
            return defecto if valor is None else valor
        try:
            if clave in self.base:
                return self.base[clave]
        except Exception:
            pass
        return defecto

    def contiene(self, clave):
        if clave in self.pendientes:
            return self.pendientes[clave] is not None
        try:
            return clave in self.base
        except Exception:
            return False

    def registrar(self, cambios):
        self.pendientes.update(cambios)


def _txt(valor):
    if valor is None:
        return ""
    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)
    return str(valor).strip()


def normalizar_dia(dia):
    """Acepta 'lunes', 'LUN', 'Miercoles'... y devuelve el nombre canónico o None."""
    if not dia:
        return None
    t = str(dia).strip().lower()
    t = t.replace("é", "e").replace("á", "a").replace("ó", "o")
    for d in DIAS:
        base = d.lower().replace("é", "e").replace("á", "a")
        if t == base or (len(t) >= 2 and base.startswith(t)):
            return d
    return None


# ---------------------------------------------------------------- entrenamiento

def leer_rutina_dia(estado, dia):
    n = int(estado.get(f"ne_{dia}", DEFECTO_CANTIDAD) or 0)
    ejercicios = []
    for i in range(min(n, MAX_ITEMS)):
        nombre = _txt(estado.get(f"n_{dia}_{i}", ""))
        if not nombre:
            continue
        ejercicios.append({
            "nombre": nombre,
            "series": _txt(estado.get(f"s_{dia}_{i}", DEFECTOS_EJERCICIO["s"])),
            "reps": _txt(estado.get(f"r_{dia}_{i}", DEFECTOS_EJERCICIO["r"])),
            "descanso_seg": _txt(estado.get(f"g_{dia}_{i}", DEFECTOS_EJERCICIO["g"])),
            "peso_kg": _txt(estado.get(f"p_{dia}_{i}", DEFECTOS_EJERCICIO["p"])),
            "rir": _txt(estado.get(f"rir_{dia}_{i}", "")),
            "nota": _txt(estado.get(f"nt_{dia}_{i}", "")),
        })
    return {"enfoque": _txt(estado.get(f"enf_{dia}", "")), "ejercicios": ejercicios}


def cambios_rutina_dia(estado, dia, enfoque, ejercicios, modo="reemplazar"):
    """Claves a escribir para dejar el día con esos ejercicios.

    modo='reemplazar' borra lo anterior; modo='agregar' los pone al final de lo existente.
    ``enfoque`` vacío o None conserva el enfoque actual.
    """
    dia = normalizar_dia(dia)
    if not dia:
        raise ValueError("Día no reconocido")

    nuevos = [e for e in (ejercicios or []) if _txt(e.get("nombre"))]
    if modo == "agregar":
        lista = leer_rutina_dia(estado, dia)["ejercicios"] + nuevos
    else:
        lista = nuevos
    lista = lista[:MAX_ITEMS]

    cambios = {}
    if enfoque is not None and _txt(enfoque):
        cambios[f"enf_{dia}"] = _txt(enfoque)
    elif modo == "reemplazar" and not lista:
        cambios[f"enf_{dia}"] = ""

    cambios[f"ne_{dia}"] = max(1, len(lista))
    for i, e in enumerate(lista):
        cambios[f"n_{dia}_{i}"] = _txt(e.get("nombre"))
        cambios[f"s_{dia}_{i}"] = _txt(e.get("series")) or DEFECTOS_EJERCICIO["s"]
        cambios[f"r_{dia}_{i}"] = _txt(e.get("reps")) or DEFECTOS_EJERCICIO["r"]
        cambios[f"g_{dia}_{i}"] = _txt(e.get("descanso_seg")) or DEFECTOS_EJERCICIO["g"]
        cambios[f"p_{dia}_{i}"] = _txt(e.get("peso_kg")) or DEFECTOS_EJERCICIO["p"]
        cambios[f"rir_{dia}_{i}"] = _txt(e.get("rir"))
        cambios[f"nt_{dia}_{i}"] = _txt(e.get("nota"))
    # Lo que sobra de la versión anterior se borra para que no reaparezca
    for i in range(len(lista), MAX_ITEMS):
        for pref in ("n", "s", "r", "g", "p", "rir", "nt"):
            if estado.contiene(f"{pref}_{dia}_{i}"):
                cambios[f"{pref}_{dia}_{i}"] = None
    return cambios


# ---------------------------------------------------------------- nutrición

def leer_comidas_dia(estado, dia):
    n = int(estado.get(f"nc_{dia}", DEFECTO_CANTIDAD) or 0)
    comidas = []
    for i in range(min(n, MAX_ITEMS)):
        comida = _txt(estado.get(f"t_{dia}_{i}", ""))
        alimentos = _txt(estado.get(f"d_{dia}_{i}", ""))
        if not comida and not alimentos:
            continue
        comidas.append({"comida": comida, "alimentos": alimentos,
                        "kcal": _txt(estado.get(f"kc_{dia}_{i}", ""))})
    return comidas


def cambios_comidas_dia(estado, dia, comidas, modo="reemplazar"):
    dia = normalizar_dia(dia)
    if not dia:
        raise ValueError("Día no reconocido")
    nuevas = [c for c in (comidas or []) if _txt(c.get("comida")) or _txt(c.get("alimentos"))]
    lista = (leer_comidas_dia(estado, dia) + nuevas) if modo == "agregar" else nuevas
    lista = lista[:MAX_ITEMS]

    cambios = {f"nc_{dia}": max(1, len(lista))}
    for i, c in enumerate(lista):
        cambios[f"t_{dia}_{i}"] = _txt(c.get("comida"))
        cambios[f"d_{dia}_{i}"] = _txt(c.get("alimentos"))
        cambios[f"kc_{dia}_{i}"] = _txt(c.get("kcal"))
    for i in range(len(lista), MAX_ITEMS):
        for pref in ("t", "d", "kc"):
            if estado.contiene(f"{pref}_{dia}_{i}"):
                cambios[f"{pref}_{dia}_{i}"] = None
    return cambios


# ---------------------------------------------------------------- cliente

def leer_cliente(estado):
    return {campo: estado.get(clave, "") for campo, clave in CAMPOS_CLIENTE.items()}


def cambios_cliente(campos, opciones_validas=None):
    """``campos`` = {campo_logico: valor}. Valida contra las listas cerradas de la app.

    Devuelve (cambios, errores).
    """
    opciones_validas = opciones_validas or {}
    cambios, errores = {}, []
    for campo, valor in campos.items():
        clave = CAMPOS_CLIENTE.get(campo)
        if not clave:
            errores.append(f"Campo desconocido: {campo}")
            continue
        if campo == "dias_entreno":
            try:
                cambios[clave] = max(1, min(7, int(float(str(valor).replace(",", ".")))))
            except ValueError:
                errores.append(f"'dias_entreno' debe ser un número de 1 a 7 (recibido: {valor})")
            continue
        validas = opciones_validas.get(campo)
        if validas:
            elegido = next((v for v in validas if v.lower() == _txt(valor).lower()), None)
            if elegido is None:
                elegido = next((v for v in validas if _txt(valor).lower() in v.lower()), None)
            if elegido is None:
                errores.append(f"'{valor}' no es válido para {campo}. Opciones: {', '.join(validas)}")
                continue
            cambios[clave] = elegido
        else:
            cambios[clave] = _txt(valor)
    return cambios, errores


# ---------------------------------------------------------------- rutina en casa

def leer_rutina_casa(estado):
    texto = estado.get(CLAVE_CASA_ACTUAL, "") or estado.get(CLAVE_CASA, "")
    if not texto:
        return None
    try:
        return json.loads(texto)
    except (TypeError, ValueError):
        return None


def cambios_rutina_casa(estado, plan):
    """Guarda el plan de casa y cambia la versión para que los editores se reinicien."""
    version = int(estado.get(CLAVE_CASA_VERSION, 0) or 0) + 1
    return {CLAVE_CASA: json.dumps(plan, ensure_ascii=False), CLAVE_CASA_ACTUAL: None,
            CLAVE_CASA_VERSION: version}
