"""Rutinas en casa: biblioteca de ejercicios, generador automático y PDF de entrega.

Estructura del plan (se guarda como JSON en ``st.session_state["casa_plan_json"]``)::

    {
      "titulo": "Plan Casa Tonificación",
      "nivel": "Intermedio", "duracion_min": 30,
      "equipo": ["Sin equipo", "Silla o banco"],
      "calentamiento": "...", "enfriamiento": "...", "notas": "...",
      "dias": [
        {"dia": "Lunes", "enfoque": "Tren inferior", "formato": "Circuito ...",
         "ejercicios": [{"nombre": "...", "series": "3", "reps_o_tiempo": "12",
                         "descanso": "20 s", "indicaciones": "...", "zona": "Pierna"}]}
      ]
    }
"""

from fpdf import FPDF
import tempfile
import os

DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

NIVELES = ["Principiante", "Intermedio", "Avanzado"]
DURACIONES = [20, 30, 45, 60]
EQUIPOS = ["Sin equipo", "Silla o banco", "Bandas elásticas", "Mancuernas o botellas",
           "Mochila con peso", "Toalla", "Barra de dominadas"]
ZONAS = ["Pierna", "Glúteo", "Empuje", "Tracción", "Core", "Cardio"]

COLUMNAS_EJERCICIO = ["nombre", "series", "reps_o_tiempo", "descanso", "indicaciones", "zona"]

# (nombre, zona, equipo, nivel 1-3, se mide por "reps" o "tiempo", indicación técnica)
BIBLIOTECA = [
    # --- Pierna
    ("Sentadilla libre", "Pierna", "Sin equipo", 1, "reps", "Pies al ancho de hombros. Baja como si te sentaras, pecho arriba y rodillas en línea con la punta de los pies."),
    ("Sentadilla a la silla", "Pierna", "Silla o banco", 1, "reps", "Baja controlado hasta rozar la silla sin dejarte caer y sube empujando el suelo con los talones."),
    ("Zancada alterna hacia atrás", "Pierna", "Sin equipo", 1, "reps", "Da un paso largo atrás y baja la rodilla casi al suelo. El peso queda en la pierna de adelante."),
    ("Sentadilla isométrica en pared", "Pierna", "Sin equipo", 1, "tiempo", "Espalda pegada a la pared y rodillas a 90 grados. Respira lento y mantén la posición."),
    ("Subida al escalón o silla", "Pierna", "Silla o banco", 1, "reps", "Sube apoyando todo el pie y empuja con la pierna de arriba, sin impulsarte con la de abajo."),
    ("Sentadilla con banda", "Pierna", "Bandas elásticas", 1, "reps", "Banda sobre las rodillas: empuja hacia afuera durante todo el recorrido para activar el glúteo."),
    ("Sentadilla goblet", "Pierna", "Mancuernas o botellas", 1, "reps", "Sujeta el peso pegado al pecho. Codos entre las rodillas al bajar y tronco erguido."),
    ("Sentadilla con mochila", "Pierna", "Mochila con peso", 1, "reps", "Mochila bien ajustada a la espalda. Baja hasta paralelo manteniendo la espalda neutra."),
    ("Sentadilla búlgara", "Pierna", "Silla o banco", 2, "reps", "Pie de atrás apoyado en la silla. Baja recto, la rodilla delantera no colapsa hacia adentro."),
    ("Zancada con mancuernas", "Pierna", "Mancuernas o botellas", 2, "reps", "Un peso en cada mano, brazos relajados. Paso largo y tronco recto."),
    ("Sentadilla con salto", "Pierna", "Sin equipo", 2, "reps", "Baja a media sentadilla y salta. Aterriza suave, con rodillas flexionadas y sin ruido."),
    ("Sentadilla a una pierna asistida", "Pierna", "Silla o banco", 3, "reps", "Apóyate ligeramente en la silla y baja con una sola pierna lo más profundo que controles."),
    # --- Glúteo
    ("Puente de glúteo", "Glúteo", "Sin equipo", 1, "reps", "Talones cerca de la cadera. Sube apretando glúteos 2 segundos arriba, sin arquear la zona lumbar."),
    ("Patada de glúteo en cuadrupedia", "Glúteo", "Sin equipo", 1, "reps", "En cuatro apoyos, empuja el talón hacia el techo sin girar la cadera."),
    ("Abducción con banda de pie", "Glúteo", "Bandas elásticas", 1, "reps", "Banda en los tobillos. Lleva la pierna hacia el lado sin inclinar el tronco."),
    ("Peso muerto rumano con mancuernas", "Glúteo", "Mancuernas o botellas", 1, "reps", "Rodillas semiflexionadas, lleva la cadera atrás con la espalda recta hasta sentir el femoral."),
    ("Buenos días con mochila", "Glúteo", "Mochila con peso", 1, "reps", "Manos al pecho, inclina el tronco llevando la cadera atrás y vuelve apretando glúteos."),
    ("Hip thrust en sofá o silla", "Glúteo", "Silla o banco", 2, "reps", "Espalda alta apoyada en el borde. Sube hasta alinear rodillas, cadera y hombros."),
    ("Puente de glúteo a una pierna", "Glúteo", "Sin equipo", 2, "reps", "Una pierna extendida en el aire. Sube sin que la cadera se incline hacia un lado."),
    ("Peso muerto a una pierna", "Glúteo", "Sin equipo", 2, "reps", "Inclínate sobre una pierna llevando la otra atrás. Cadera nivelada y movimiento lento."),
    # --- Empuje
    ("Flexiones con rodillas apoyadas", "Empuje", "Sin equipo", 1, "reps", "Manos un poco más anchas que los hombros. Cuerpo en línea de rodillas a cabeza."),
    ("Flexiones inclinadas en silla", "Empuje", "Silla o banco", 1, "reps", "Manos en el borde de una silla firme contra la pared. Baja el pecho al borde."),
    ("Fondos de tríceps en silla", "Empuje", "Silla o banco", 1, "reps", "Manos en el borde de la silla, codos hacia atrás. Baja hasta 90 grados sin encoger hombros."),
    ("Press de hombro con mancuernas", "Empuje", "Mancuernas o botellas", 1, "reps", "De pie y abdomen firme. Sube los pesos sin arquear la espalda."),
    ("Press de pecho con banda", "Empuje", "Bandas elásticas", 1, "reps", "Banda por detrás de la espalda. Empuja al frente y vuelve controlando la tensión."),
    ("Flexiones", "Empuje", "Sin equipo", 2, "reps", "Cuerpo como una tabla. Codos a 45 grados del tronco y pecho casi al suelo."),
    ("Flexiones declinadas", "Empuje", "Silla o banco", 3, "reps", "Pies sobre la silla. Mantén el abdomen firme para que la cadera no caiga."),
    ("Flexiones en pica", "Empuje", "Sin equipo", 3, "reps", "Cadera alta en V invertida. Lleva la cabeza hacia el suelo entre las manos."),
    ("Flexiones diamante", "Empuje", "Sin equipo", 3, "reps", "Manos juntas formando un rombo bajo el pecho. Codos pegados al cuerpo."),
    # --- Tracción
    ("Superman", "Tracción", "Sin equipo", 1, "reps", "Boca abajo, eleva brazos y piernas a la vez, sostén 2 segundos y baja lento."),
    ("Y-T-W en el suelo", "Tracción", "Sin equipo", 1, "reps", "Boca abajo, eleva los brazos formando las letras Y, T y W apretando omóplatos."),
    ("Tirón isométrico con toalla", "Tracción", "Toalla", 1, "tiempo", "Sujeta la toalla con ambas manos y tira hacia afuera con fuerza, omóplatos atrás."),
    ("Remo con banda", "Tracción", "Bandas elásticas", 1, "reps", "Banda anclada al frente. Lleva los codos atrás pegados al cuerpo y junta omóplatos."),
    ("Jalón con banda", "Tracción", "Bandas elásticas", 1, "reps", "Banda anclada arriba. Tira hacia el pecho llevando los codos hacia las costillas."),
    ("Remo con mancuerna a una mano", "Tracción", "Mancuernas o botellas", 1, "reps", "Apoya una mano en la silla, espalda plana. Lleva el peso hacia la cadera."),
    ("Remo con mochila", "Tracción", "Mochila con peso", 1, "reps", "Inclinado con la espalda recta, tira de la mochila hacia el abdomen."),
    ("Curl de bíceps con mancuernas", "Tracción", "Mancuernas o botellas", 1, "reps", "Codos fijos a los lados del cuerpo. Sube y baja sin balancearte."),
    ("Remo invertido bajo una mesa", "Tracción", "Sin equipo", 2, "reps", "Solo con una mesa muy firme. Cuerpo recto y lleva el pecho hacia el borde."),
    ("Face pull con banda", "Tracción", "Bandas elásticas", 2, "reps", "Tira de la banda hacia la cara abriendo los codos. Ideal para la postura."),
    ("Dominadas", "Tracción", "Barra de dominadas", 3, "reps", "Agarre algo más ancho que los hombros. Sube hasta pasar la barbilla y baja completo."),
    # --- Core
    ("Plancha frontal", "Core", "Sin equipo", 1, "tiempo", "Antebrazos bajo los hombros. Aprieta glúteos y abdomen; la cadera no sube ni cae."),
    ("Plancha lateral", "Core", "Sin equipo", 1, "tiempo", "Codo bajo el hombro y cuerpo en línea. Haz el tiempo indicado por cada lado."),
    ("Dead bug", "Core", "Sin equipo", 1, "reps", "Boca arriba, zona lumbar pegada al suelo. Extiende brazo y pierna contrarios lento."),
    ("Bird dog", "Core", "Sin equipo", 1, "reps", "En cuatro apoyos, extiende brazo y pierna contrarios sin mover la cadera."),
    ("Toques de hombro en plancha", "Core", "Sin equipo", 2, "reps", "Plancha alta con pies separados. Toca el hombro contrario sin balancear la cadera."),
    ("Crunch inverso", "Core", "Sin equipo", 2, "reps", "Boca arriba, lleva las rodillas al pecho despegando la cadera del suelo con control."),
    ("Giros rusos", "Core", "Sin equipo", 2, "reps", "Sentado con el tronco inclinado atrás, gira de lado a lado llevando las manos al suelo."),
    ("Hollow hold", "Core", "Sin equipo", 3, "tiempo", "Boca arriba, eleva hombros y piernas formando una banana. Lumbar pegada al suelo."),
    # --- Cardio
    ("Jumping jacks", "Cardio", "Sin equipo", 1, "tiempo", "Abre y cierra piernas y brazos a ritmo constante. Sin impacto: da un paso al lado."),
    ("Rodillas al pecho", "Cardio", "Sin equipo", 1, "tiempo", "Corre en el sitio subiendo las rodillas a la altura de la cadera."),
    ("Comba imaginaria", "Cardio", "Sin equipo", 1, "tiempo", "Saltitos cortos sobre la punta de los pies girando las muñecas."),
    ("Escaladores", "Cardio", "Sin equipo", 2, "tiempo", "Plancha alta y lleva las rodillas al pecho alternando, sin subir la cadera."),
    ("Saltos de patinador", "Cardio", "Sin equipo", 2, "tiempo", "Salta de lado a lado aterrizando sobre una pierna, como un patinador."),
    ("Burpees", "Cardio", "Sin equipo", 3, "reps", "Baja al suelo, flexión opcional, vuelve a ponerte de pie y salta. Ritmo sostenible."),
]

CALENTAMIENTO_BASE = (
    "5 minutos: 1 min de marcha en el sitio, 10 círculos de brazos hacia adelante y hacia atrás, "
    "10 rotaciones de cadera, 10 sentadillas lentas sin peso y 30 s de jumping jacks suaves."
)
ENFRIAMIENTO_BASE = (
    "5 minutos: estira cuádriceps, femorales, glúteos, pecho y espalda 30 s cada uno. "
    "Termina con 1 minuto de respiración profunda: 4 s inhalando y 6 s exhalando."
)

DIAS_POR_FRECUENCIA = {
    1: ["Miércoles"],
    2: ["Lunes", "Jueves"],
    3: ["Lunes", "Miércoles", "Viernes"],
    4: ["Lunes", "Martes", "Jueves", "Viernes"],
    5: ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"],
    6: ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"],
    7: DIAS,
}

PLANTILLAS_DIA = {
    "full": ("Cuerpo completo", ["Pierna", "Empuje", "Glúteo", "Tracción", "Core", "Cardio", "Pierna", "Core"]),
    "inferior": ("Tren inferior y core", ["Pierna", "Glúteo", "Pierna", "Core", "Glúteo", "Cardio", "Core", "Pierna"]),
    "superior": ("Tren superior y cardio", ["Empuje", "Tracción", "Empuje", "Core", "Tracción", "Cardio", "Empuje", "Core"]),
    "metabolico": ("Full body metabólico", ["Cardio", "Pierna", "Empuje", "Cardio", "Glúteo", "Core", "Cardio", "Tracción"]),
}

EJERCICIOS_POR_DURACION = {20: 5, 30: 6, 45: 7, 60: 8}

PRESCRIPCION = {
    # series, reps, tiempo
    "Principiante": (3, "10-12", "30 s"),
    "Intermedio": (3, "12-15", "40 s"),
    "Avanzado": (4, "15-20", "45 s"),
}

OBJETIVOS_CIRCUITO = ("Pérdida de grasa", "Recomposición corporal", "Rendimiento deportivo")

PROGRESION_CASA = {
    "Principiante": "Semana 1-2: aprende la técnica con el número de series indicado. Semana 3-4: suma 2 repeticiones o 5 segundos por ejercicio. Si todo se siente fácil, pasa a la versión más difícil del ejercicio.",
    "Intermedio": "Cada semana suma 1-2 repeticiones o 5 segundos. Al llegar al tope del rango, reduce el descanso 5 segundos o agrega una vuelta más al circuito.",
    "Avanzado": "Alterna semanas de volumen (más repeticiones) y de intensidad (versiones más difíciles, tempo lento de 3 s al bajar). Cada 4 semanas haz una semana suave para recuperar.",
}

CONSEJOS_SEGURIDAD = [
    "Entrena en un espacio despejado, con buen calzado o descalzo sobre superficie antideslizante.",
    "Usa solo sillas y mesas firmes; apóyalas contra la pared antes de usarlas.",
    "La técnica va antes que la velocidad: si la postura se pierde, descansa unos segundos.",
    "Hidrátate antes, durante y después de la sesión.",
    "Si sientes dolor agudo (no cansancio muscular), detén el ejercicio y consulta a tu coach.",
]


def _nivel_idx(nivel):
    return {"Principiante": 1, "Intermedio": 2, "Avanzado": 3}.get(nivel, 2)


def buscar_en_biblioteca(nombre):
    nombre = (nombre or "").strip().lower()
    for item in BIBLIOTECA:
        if item[0].lower() == nombre:
            return item
    return None


def plantillas_para(frecuencia):
    if frecuencia <= 3:
        return ["full"] * frecuencia
    if frecuencia == 4:
        return ["inferior", "superior", "inferior", "superior"]
    ciclo = ["inferior", "superior", "metabolico"]
    return [ciclo[i % 3] for i in range(frecuencia)]


def generar_rutina_casa(frecuencia=3, nivel="Intermedio", duracion_min=30,
                        equipo=None, objetivo="Pérdida de grasa", titulo=None):
    """Arma una rutina completa a partir de la biblioteca, sin necesitar IA."""
    frecuencia = max(1, min(7, int(frecuencia)))
    equipo = set(equipo or []) | {"Sin equipo"}
    n_idx = _nivel_idx(nivel)
    series, reps, tiempo = PRESCRIPCION.get(nivel, PRESCRIPCION["Intermedio"])
    n_ejercicios = EJERCICIOS_POR_DURACION.get(int(duracion_min), 6)
    circuito = objetivo in OBJETIVOS_CIRCUITO

    if circuito:
        formato = (f"Circuito: haz los ejercicios seguidos con 20 s de pausa entre uno y otro. "
                   f"Repite {series} vueltas y descansa 90 s entre vueltas.")
        descanso = "20 s"
    else:
        formato = (f"Series: completa las {series} series de cada ejercicio antes de pasar al siguiente. "
                   f"Descanso de 45-60 s entre series.")
        descanso = "45-60 s"

    dias_plan = []
    for idx_dia, (dia, plantilla) in enumerate(zip(DIAS_POR_FRECUENCIA[frecuencia], plantillas_para(frecuencia))):
        enfoque, zonas = PLANTILLAS_DIA[plantilla]
        usados, ejercicios = set(), []
        uso_por_zona = {}
        for zona in zonas[:n_ejercicios]:
            candidatos = [b for b in BIBLIOTECA
                          if b[1] == zona and b[2] in equipo and b[3] <= n_idx and b[0] not in usados]
            if not candidatos:
                continue
            # Primero lo más desafiante permitido para el nivel; la rotación varía los días
            candidatos.sort(key=lambda b: (-b[3], b[0]))
            k = uso_por_zona.get(zona, 0)
            elegido = candidatos[(idx_dia * 2 + k) % len(candidatos)]
            uso_por_zona[zona] = k + 1
            usados.add(elegido[0])
            ejercicios.append({
                "nombre": elegido[0],
                "series": str(series),
                "reps_o_tiempo": tiempo if elegido[4] == "tiempo" else reps,
                "descanso": descanso,
                "indicaciones": elegido[5],
                "zona": elegido[1],
            })
        dias_plan.append({"dia": dia, "enfoque": enfoque, "formato": formato, "ejercicios": ejercicios})

    return {
        "titulo": titulo or f"Plan personalizado - {objetivo}",
        "nivel": nivel,
        "duracion_min": int(duracion_min),
        "equipo": sorted(equipo, key=lambda e: EQUIPOS.index(e) if e in EQUIPOS else 99),
        "objetivo": objetivo,
        "calentamiento": CALENTAMIENTO_BASE,
        "enfriamiento": ENFRIAMIENTO_BASE,
        "notas": "",
        "dias": dias_plan,
    }


def plan_vacio():
    return {"titulo": "Rutina en casa", "nivel": "Intermedio", "duracion_min": 30,
            "equipo": ["Sin equipo"], "objetivo": "", "calentamiento": CALENTAMIENTO_BASE,
            "enfriamiento": ENFRIAMIENTO_BASE, "notas": "", "dias": []}


def normalizar_plan(plan):
    """Completa campos faltantes para que la interfaz y el PDF nunca fallen."""
    base = plan_vacio()
    base.update({k: v for k, v in (plan or {}).items() if v is not None})
    dias = []
    for d in base.get("dias") or []:
        if d.get("dia") not in DIAS:
            continue
        ejercicios = []
        for e in d.get("ejercicios") or []:
            fila = {c: str(e.get(c, "") or "").strip() for c in COLUMNAS_EJERCICIO}
            if fila["nombre"]:
                ejercicios.append(fila)
        dias.append({"dia": d["dia"], "enfoque": str(d.get("enfoque", "") or ""),
                     "formato": str(d.get("formato", "") or ""), "ejercicios": ejercicios})
    dias.sort(key=lambda d: DIAS.index(d["dia"]))
    base["dias"] = dias
    try:
        base["duracion_min"] = int(base.get("duracion_min") or 30)
    except (TypeError, ValueError):
        base["duracion_min"] = 30
    if isinstance(base.get("equipo"), str):
        base["equipo"] = [base["equipo"]]
    return base


# ==========================================================================
# PDF PROFESIONAL
# ==========================================================================

def _t(texto):
    if texto is None:
        return ""
    texto = str(texto).replace("•", "-").replace("–", "-").replace("—", "-").replace("’", "'")
    return texto.encode("latin-1", "ignore").decode("latin-1")


def _mezcla(c1, c2, t):
    return tuple(int(round(a + (b - a) * t)) for a, b in zip(c1, c2))


def generar_pdf_rutina_casa(plan, cliente, config, paleta, logo_bytes=None):
    """PDF de entrega de la rutina en casa.

    paleta: dict con 'bg', 'texto', 'acento', 'caja' (tuplas RGB) y 'sobre_acento'
    (color del texto encima del acento).
    """
    plan = normalizar_plan(plan)
    bg, texto, acento, caja = paleta["bg"], paleta["texto"], paleta["acento"], paleta["caja"]
    sobre_acento = paleta["sobre_acento"]
    suave = _mezcla(texto, bg, 0.45)          # texto secundario
    borde = _mezcla(texto, caja, 0.82)        # borde fino de tarjetas
    acento_suave = _mezcla(acento, caja, 0.80)

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(False)
    pdf.set_margins(15, 15, 15)
    W, H = pdf.w, pdf.h
    ANCHO = W - 30
    LIMITE = H - 22

    logo_path = None
    if logo_bytes:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                tmp.write(logo_bytes)
                logo_path = tmp.name
        except Exception:
            logo_path = None

    def fuente(estilo="", tam=10):
        pdf.set_font("Helvetica", estilo, tam)

    def lineas(txt, ancho, estilo="", tam=9):
        fuente(estilo, tam)
        if not txt:
            return 0
        return len(pdf.multi_cell(ancho, 4, _t(txt), dry_run=True, output="LINES"))

    def nueva_pagina():
        pdf.add_page()
        pdf.set_fill_color(*bg)
        pdf.rect(0, 0, W, H, "F")

    def pie():
        pdf.set_draw_color(*borde)
        pdf.set_line_width(0.2)
        pdf.line(15, H - 14, W - 15, H - 14)
        fuente("B", 8)
        pdf.set_text_color(*suave)
        pdf.set_xy(15, H - 12)
        pdf.cell(ANCHO / 2, 5, _t(config.get("entrenador", "")).upper())
        pdf.set_xy(15 + ANCHO / 2, H - 12)
        pdf.cell(ANCHO / 2, 5, _t(f"{config.get('redes', '')}   |   {pdf.page_no()}"), align="R")

    def encabezado_seccion(titulo, subtitulo=""):
        nueva_pagina()
        pdf.set_fill_color(*acento)
        pdf.rect(0, 0, W, 30, "F")
        if logo_path:
            try:
                pdf.image(logo_path, x=W - 15 - 18, y=6, h=18)
            except Exception:
                pass
        pdf.set_text_color(*sobre_acento)
        fuente("B", 22)
        pdf.set_xy(15, 7)
        pdf.cell(ANCHO - 25, 10, _t(titulo).upper())
        if subtitulo:
            fuente("", 10)
            pdf.set_xy(15, 18)
            pdf.cell(ANCHO - 25, 6, _t(subtitulo))
        return 38

    def caja_texto(y, titulo, cuerpo, franja=True):
        n = lineas(cuerpo, ANCHO - 14, "", 9)
        alto = 13 + n * 4
        if y + alto > LIMITE:
            pie()
            y = encabezado_seccion("Continuación")
        pdf.set_fill_color(*caja)
        pdf.set_draw_color(*borde)
        pdf.rect(15, y, ANCHO, alto, "DF", round_corners=True, corner_radius=2)
        if franja:
            pdf.set_fill_color(*acento)
            pdf.rect(15, y, 2.2, alto, "F")
        pdf.set_text_color(*(texto if paleta.get("acento_ilegible") else acento))
        fuente("B", 8.5)
        pdf.set_xy(21, y + 3.5)
        pdf.cell(ANCHO - 12, 4, _t(titulo).upper())
        pdf.set_text_color(*texto)
        fuente("", 9)
        pdf.set_xy(21, y + 9)
        pdf.multi_cell(ANCHO - 14, 4, _t(cuerpo), align="L")
        return y + alto + 5

    def dos_cajas(y, izquierda, derecha):
        """Dos recuadros lado a lado con la misma altura (titulo, cuerpo)."""
        ancho_c = (ANCHO - 5) / 2
        n = max(lineas(izquierda[1], ancho_c - 12, "", 8.5), lineas(derecha[1], ancho_c - 12, "", 8.5))
        alto = 12 + n * 3.8
        for i, (titulo, cuerpo) in enumerate((izquierda, derecha)):
            x = 15 + i * (ancho_c + 5)
            pdf.set_fill_color(*caja)
            pdf.set_draw_color(*borde)
            pdf.rect(x, y, ancho_c, alto, "DF", round_corners=True, corner_radius=2)
            pdf.set_fill_color(*acento)
            pdf.rect(x, y, 2.2, alto, "F")
            pdf.set_text_color(*(texto if paleta.get("acento_ilegible") else acento))
            fuente("B", 8)
            pdf.set_xy(x + 6, y + 3.2)
            pdf.cell(ancho_c - 10, 4, _t(titulo).upper())
            pdf.set_text_color(*texto)
            fuente("", 8.5)
            pdf.set_xy(x + 6, y + 8.5)
            pdf.multi_cell(ancho_c - 12, 3.8, _t(cuerpo), align="L")
        return y + alto + 5

    # ------------------------------------------------------------ PORTADA
    nueva_pagina()
    alto_banda = 100
    pdf.set_fill_color(*acento)
    pdf.rect(0, 0, W, alto_banda, "F")
    # Círculos decorativos
    pdf.set_fill_color(*_mezcla(acento, sobre_acento, 0.10))
    pdf.ellipse(W - 85, -35, 120, 120, "F")
    pdf.set_fill_color(*_mezcla(acento, sobre_acento, 0.18))
    pdf.ellipse(W - 45, 45, 70, 70, "F")
    # Recorta lo que se sale de la banda
    pdf.set_fill_color(*bg)
    pdf.rect(0, alto_banda, W, H - alto_banda, "F")

    if logo_path:
        try:
            pdf.image(logo_path, x=15, y=12, h=24)
        except Exception:
            pass

    pdf.set_text_color(*sobre_acento)
    fuente("B", 9)
    pdf.set_xy(15, 44)
    pdf.cell(ANCHO, 5, _t("P R O G R A M A   D E   E N T R E N A M I E N T O"))
    fuente("B", 36)
    pdf.set_xy(15, 51)
    pdf.cell(ANCHO, 15, "RUTINA EN CASA")
    fuente("", 12)
    pdf.set_xy(15, 67)
    pdf.cell(ANCHO, 6, _t(plan["titulo"]))
    fuente("", 8.5)
    pdf.set_xy(15, 80)
    pdf.cell(ANCHO, 4, "PREPARADO PARA")
    fuente("B", 16)
    pdf.set_xy(15, 85)
    pdf.cell(ANCHO, 8, _t(cliente.get("nombre") or "Cliente").upper())

    # Tarjetas de datos clave
    y = alto_banda + 10
    dias_entreno = plan["dias"]
    equipo_txt = ", ".join(e for e in plan["equipo"] if e != "Sin equipo") or "Sin equipo"
    datos = [
        (str(len(dias_entreno)), "DÍAS POR SEMANA"),
        (f"{plan['duracion_min']} min", "POR SESIÓN"),
        (plan["nivel"], "NIVEL"),
        (str(sum(len(d["ejercicios"]) for d in dias_entreno)), "EJERCICIOS EN TOTAL"),
    ]
    ancho_t = (ANCHO - 3 * 4) / 4
    for i, (valor, etiqueta) in enumerate(datos):
        x = 15 + i * (ancho_t + 4)
        pdf.set_fill_color(*caja)
        pdf.set_draw_color(*borde)
        pdf.rect(x, y, ancho_t, 26, "DF", round_corners=True, corner_radius=2)
        pdf.set_fill_color(*acento)
        pdf.rect(x + 6, y, ancho_t - 12, 1.6, "F")
        pdf.set_text_color(*texto)
        fuente("B", 15 if len(valor) < 9 else 11)
        pdf.set_xy(x, y + 6)
        pdf.cell(ancho_t, 8, _t(valor), align="C")
        pdf.set_text_color(*suave)
        fuente("B", 6.5)
        pdf.set_xy(x, y + 16)
        pdf.cell(ancho_t, 4, _t(etiqueta), align="C")

    # Semana
    y += 36
    pdf.set_text_color(*texto)
    fuente("B", 11)
    pdf.set_xy(15, y)
    pdf.cell(ANCHO, 6, "TU SEMANA")
    y += 9
    ancho_d = (ANCHO - 6 * 2) / 7
    por_dia = {d["dia"]: d for d in dias_entreno}
    for i, dia in enumerate(DIAS):
        x = 15 + i * (ancho_d + 2)
        entreno = por_dia.get(dia)
        pdf.set_draw_color(*borde)
        pdf.set_fill_color(*(acento if entreno else caja))
        pdf.rect(x, y, ancho_d, 9, "DF", round_corners=True, corner_radius=1.5)
        pdf.set_text_color(*(sobre_acento if entreno else suave))
        fuente("B", 8)
        pdf.set_xy(x, y + 2.5)
        pdf.cell(ancho_d, 4, _t(dia[:3]).upper(), align="C")
        pdf.set_fill_color(*caja)
        pdf.rect(x, y + 10, ancho_d, 26, "DF", round_corners=True, corner_radius=1.5)
        pdf.set_text_color(*(texto if entreno else suave))
        fuente("B" if entreno else "I", 6.8)
        pdf.set_xy(x + 1, y + 13)
        etiqueta = entreno["enfoque"] if entreno else "Descanso activo: camina 20-30 min"
        pdf.multi_cell(ancho_d - 2, 3.3, _t(etiqueta)[:70], align="C")
    y += 44

    # Cómo usar
    pasos = [
        "Haz siempre el calentamiento antes de empezar y el estiramiento al terminar.",
        "Sigue el orden de los ejercicios y respeta los descansos indicados.",
        "Marca cada sesión completada en la hoja de seguimiento de la última página.",
        "Prioriza la técnica: lee la indicación de cada ejercicio antes de hacerlo.",
    ]
    pdf.set_text_color(*texto)
    fuente("B", 11)
    pdf.set_xy(15, y)
    pdf.cell(ANCHO, 6, _t("CÓMO USAR ESTA RUTINA"))
    y += 9
    for i, paso in enumerate(pasos):
        pdf.set_fill_color(*acento)
        pdf.ellipse(15, y, 7, 7, "F")
        pdf.set_text_color(*sobre_acento)
        fuente("B", 9)
        pdf.set_xy(15, y + 1.5)
        pdf.cell(7, 4, str(i + 1), align="C")
        pdf.set_text_color(*texto)
        fuente("", 9.5)
        pdf.set_xy(26, y + 1.4)
        pdf.cell(ANCHO - 11, 4.5, _t(paso))
        y += 10

    y += 2
    pdf.set_text_color(*suave)
    fuente("", 8.5)
    pdf.set_xy(15, y)
    pdf.multi_cell(ANCHO, 4.2, _t(
        f"Material: {equipo_txt}.   Vigencia: {config.get('fecha_inicio', '')} a {config.get('fecha_fin', '')}."))
    pie()

    # ------------------------------------------------------------ DÍAS
    for d in dias_entreno:
        sub = f"{d['enfoque']}   |   {plan['duracion_min']} min   |   {len(d['ejercicios'])} ejercicios"
        y = encabezado_seccion(d["dia"], sub)

        if d.get("formato"):
            fuente("I", 9)
            n = lineas(d["formato"], ANCHO - 10, "I", 9)
            alto = n * 4 + 6
            pdf.set_fill_color(*acento_suave)
            pdf.rect(15, y, ANCHO, alto, "F", round_corners=True, corner_radius=2)
            pdf.set_text_color(*(texto if paleta.get("oscuro") else _mezcla(texto, acento, 0.25)))
            pdf.set_xy(20, y + 3)
            fuente("I", 9)
            pdf.multi_cell(ANCHO - 10, 4, _t(d["formato"]), align="L")
            y += alto + 5

        y = dos_cajas(y, ("Antes: calentamiento", plan["calentamiento"]),
                      ("Al terminar: vuelta a la calma", plan["enfriamiento"]))

        for num, e in enumerate(d["ejercicios"], start=1):
            ancho_txt = ANCHO - 22 - 50
            n = lineas(e["indicaciones"], ancho_txt, "", 8.5)
            alto = max(21, 14 + n * 4)
            if y + alto > LIMITE:
                pie()
                y = encabezado_seccion(d["dia"] + " (cont.)", d["enfoque"])
            pdf.set_fill_color(*caja)
            pdf.set_draw_color(*borde)
            pdf.rect(15, y, ANCHO, alto, "DF", round_corners=True, corner_radius=2.5)
            # Número
            pdf.set_fill_color(*acento)
            pdf.ellipse(20, y + 4.5, 11, 11, "F")
            pdf.set_text_color(*sobre_acento)
            fuente("B", 12)
            pdf.set_xy(20, y + 7.5)
            pdf.cell(11, 5, str(num), align="C")
            # Zona + nombre
            if e.get("zona"):
                pdf.set_text_color(*suave)
                fuente("B", 6.5)
                pdf.set_xy(37, y + 3.5)
                pdf.cell(ancho_txt, 3, _t(e["zona"]).upper())
            pdf.set_text_color(*texto)
            fuente("B", 11)
            pdf.set_xy(37, y + 6.8)
            pdf.cell(ancho_txt, 5, _t(e["nombre"]))
            # Indicaciones
            if e.get("indicaciones"):
                pdf.set_text_color(*suave)
                fuente("", 8.5)
                pdf.set_xy(37, y + 12.6)
                pdf.multi_cell(ancho_txt, 4, _t(e["indicaciones"]), align="L")
            # Prescripción
            x_p = 15 + ANCHO - 48
            series = e.get("series", "")
            cantidad = e.get("reps_o_tiempo", "")
            principal = f"{series} x {cantidad}" if series and cantidad else (cantidad or series)
            pdf.set_fill_color(*acento)
            pdf.rect(x_p, y + 4.5, 42, 9, "F", round_corners=True, corner_radius=2)
            pdf.set_text_color(*sobre_acento)
            fuente("B", 11)
            pdf.set_xy(x_p, y + 6.5)
            pdf.cell(42, 5, _t(principal), align="C")
            if e.get("descanso"):
                pdf.set_text_color(*suave)
                fuente("", 7.5)
                pdf.set_xy(x_p, y + 14.5)
                pdf.cell(42, 4, _t(f"Descanso {e['descanso']}"), align="C")
            y += alto + 3

        pie()

    # ------------------------------------------------------------ SEGUIMIENTO
    y = encabezado_seccion("Seguimiento", "Marca cada sesión completada y anota cómo te sentiste")
    semanas = 4
    col_dia = 62
    col_sem = (ANCHO - col_dia) / semanas
    pdf.set_draw_color(*borde)
    pdf.set_fill_color(*acento)
    pdf.rect(15, y, ANCHO, 9, "F", round_corners=True, corner_radius=1.5)
    pdf.set_text_color(*sobre_acento)
    fuente("B", 8.5)
    pdf.set_xy(18, y + 2.5)
    pdf.cell(col_dia - 3, 4, _t("SESIÓN"))
    for s in range(semanas):
        pdf.set_xy(15 + col_dia + s * col_sem, y + 2.5)
        pdf.cell(col_sem, 4, f"SEMANA {s + 1}", align="C")
    y += 11
    for i, d in enumerate(dias_entreno):
        pdf.set_fill_color(*(caja if i % 2 == 0 else bg))
        pdf.rect(15, y, ANCHO, 11, "DF")
        pdf.set_text_color(*texto)
        fuente("B", 9)
        pdf.set_xy(18, y + 2)
        pdf.cell(col_dia - 3, 4, _t(d["dia"]))
        pdf.set_text_color(*suave)
        fuente("", 7)
        pdf.set_xy(18, y + 6)
        pdf.cell(col_dia - 3, 3.5, _t(d["enfoque"])[:40])
        for s in range(semanas):
            cx = 15 + col_dia + s * col_sem + col_sem / 2 - 3
            pdf.set_draw_color(*_mezcla(texto, bg, 0.3))
            pdf.rect(cx, y + 2.5, 6, 6, "D", round_corners=True, corner_radius=1)
        pdf.set_draw_color(*borde)
        y += 11
    y += 7

    y = caja_texto(y, f"Cómo progresar ({plan['nivel']})",
                   PROGRESION_CASA.get(plan["nivel"], PROGRESION_CASA["Intermedio"]))
    y = caja_texto(y, "Seguridad", "\n".join("- " + c for c in CONSEJOS_SEGURIDAD))
    if plan.get("notas"):
        y = caja_texto(y, "Notas de tu coach", plan["notas"])

    if y + 20 < LIMITE:
        y = max(y + 6, LIMITE - 16)
        pdf.set_draw_color(*suave)
        pdf.line(W - 15 - 70, y, W - 15, y)
        pdf.set_text_color(*suave)
        fuente("", 8)
        pdf.set_xy(W - 15 - 70, y + 1.5)
        pdf.cell(70, 4, _t(config.get("entrenador", "Tu coach")), align="C")
    pie()

    if logo_path:
        try:
            os.remove(logo_path)
        except OSError:
            pass
    return bytes(pdf.output())
