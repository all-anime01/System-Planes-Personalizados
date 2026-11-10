"""Integración con Claude: lectura de rutinas desde fotos y asistente con herramientas.

- ``extraer_rutina_de_imagenes``: una sola llamada con visión + salida estructurada
  (JSON validado por esquema) que transcribe una rutina escrita a mano o impresa.
- ``ejecutar_turno_asistente``: bucle de uso de herramientas. El modelo decide qué
  herramienta llamar; la app ejecuta cada una contra el plan (ver ``plan_estado``).

La clave de API se toma de ``ANTHROPIC_API_KEY`` (variable de entorno o secrets de
Streamlit) o de la que el usuario escriba en el panel lateral.
"""

import base64
import io
import json

import anthropic
from PIL import Image, ImageOps

MODELO = "claude-opus-5-5"
# Si el modelo principal declina una petición, la API la reintenta sola con el modelo
# de respaldo adecuado dentro de la misma llamada.
BETAS = ["server-side-fallback-2026-07-01"]
LADO_MAX_IMAGEN = 1568

DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


class ErrorIA(Exception):
    """Error con un mensaje listo para mostrar al usuario."""


def crear_cliente(api_key=None):
    try:
        return anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
    except Exception as e:  # sin credenciales configuradas
        raise ErrorIA("Falta la clave de API de Anthropic. Agrégala en el panel lateral "
                      "(🤖 Inteligencia Artificial).") from e


def _crear_mensaje(cliente, **kwargs):
    try:
        return cliente.beta.messages.create(
            model=MODELO, betas=BETAS, fallbacks="default", **kwargs)
    except anthropic.AuthenticationError as e:
        raise ErrorIA("La clave de API no es válida. Revísala en el panel lateral.") from e
    except anthropic.PermissionDeniedError as e:
        raise ErrorIA("La clave de API no tiene permiso para usar este modelo.") from e
    except anthropic.RateLimitError as e:
        raise ErrorIA("Se alcanzó el límite de uso de la API. Espera un minuto y vuelve a intentar.") from e
    except anthropic.BadRequestError as e:
        raise ErrorIA(f"La petición fue rechazada: {e.message}") from e
    except anthropic.APIStatusError as e:
        raise ErrorIA(f"El servicio de IA respondió con un error ({e.status_code}). Intenta de nuevo.") from e
    except anthropic.APIConnectionError as e:
        raise ErrorIA("No hay conexión con el servicio de IA. Revisa tu internet.") from e
    except anthropic.AnthropicError as e:  # p. ej. no hay ninguna credencial configurada
        raise ErrorIA("No se pudo conectar con la IA. Revisa la clave de API en el panel lateral.") from e


def _texto_respuesta(respuesta):
    return "".join(b.text for b in respuesta.content if b.type == "text").strip()


def _revisar_parada(respuesta):
    if respuesta.stop_reason == "refusal":
        raise ErrorIA("La IA no pudo procesar esta petición. Reformúlala o revisa el contenido.")
    if respuesta.stop_reason == "max_tokens":
        raise ErrorIA("La respuesta fue demasiado larga y quedó cortada. Divide la tarea en partes más pequeñas.")


# ==========================================================================
# 📸 LECTURA DE RUTINAS DESDE FOTOS
# ==========================================================================

def preparar_imagen(datos):
    """Endereza según EXIF, reduce a un tamaño razonable y devuelve (base64, media_type)."""
    try:
        img = Image.open(io.BytesIO(datos))
        img = ImageOps.exif_transpose(img)
    except Exception as e:
        raise ErrorIA("No se pudo abrir la imagen. Usa una foto en JPG, PNG o WEBP.") from e
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    img.thumbnail((LADO_MAX_IMAGEN, LADO_MAX_IMAGEN))
    salida = io.BytesIO()
    img.save(salida, format="JPEG", quality=88)
    return base64.standard_b64encode(salida.getvalue()).decode("ascii"), "image/jpeg"


_ESQUEMA_EJERCICIO = {
    "type": "object",
    "properties": {
        "nombre": {"type": "string"},
        "series": {"type": "string"},
        "reps": {"type": "string"},
        "descanso_seg": {"type": "string"},
        "peso_kg": {"type": "string"},
        "rir": {"type": "string"},
        "nota": {"type": "string"},
    },
    "required": ["nombre", "series", "reps", "descanso_seg", "peso_kg", "rir", "nota"],
    "additionalProperties": False,
}

ESQUEMA_EXTRACCION = {
    "type": "object",
    "properties": {
        "es_rutina": {"type": "boolean"},
        "observaciones": {"type": "string"},
        "bloques": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "etiqueta": {"type": "string"},
                    "dia_semana": {"type": "string", "enum": DIAS + ["Sin especificar"]},
                    "enfoque": {"type": "string"},
                    "ejercicios": {"type": "array", "items": _ESQUEMA_EJERCICIO},
                },
                "required": ["etiqueta", "dia_semana", "enfoque", "ejercicios"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["es_rutina", "observaciones", "bloques"],
    "additionalProperties": False,
}

PROMPT_EXTRACCION = """Eres el asistente de un entrenador personal. Las imágenes adjuntas son fotos de una rutina de entrenamiento escrita en una hoja, un cuaderno, una pizarra o una impresión. Transcríbela a datos estructurados para cargarla en el sistema de planes del entrenador.

Cómo transcribir:
- Cada día o sesión de la rutina es un bloque. En "etiqueta" copia el título tal como aparece ("Día 1", "Lunes", "Rutina A", "Pierna"...).
- "dia_semana": el día de la semana solo si está escrito o abreviado (L, Lun, Mar, X, Mié...). Si la sesión no indica día ("Día 1", "Rutina A"), usa "Sin especificar"; el entrenador lo asignará.
- "enfoque": el grupo muscular u objetivo de la sesión si aparece (ej. "Pierna - Cuádriceps"); si no aparece pero es evidente por los ejercicios, resúmelo en pocas palabras.
- Escribe el nombre de cada ejercicio completo y con la ortografía correcta en español ("press banca" → "Press de banca", "sentadia" → "Sentadilla", "jalon al pecho" → "Jalón al pecho"). Mantén el nombre en inglés solo si así se usa habitualmente (ej. "Hip thrust").
- Descompón notaciones como "4x12", "4 x 10-12", "3 series de 15": "series" = 4, "reps" = "12" o "10-12". Si la cantidad es tiempo ("30 seg", "1 min"), ponlo en "reps" con su unidad ("30 s").
- "descanso_seg": solo dígitos en segundos ("1 min" → "60", "90''" → "90").
- "peso_kg": solo el número en kg si aparece; si está en libras, conviértelo a kg redondeando a 0.5.
- "rir": solo si aparece RIR o RPE (si es RPE, anótalo en la nota en vez de convertirlo).
- "nota": superseries, tempo, técnica, dropsets u otras indicaciones escritas junto al ejercicio.
- Lo que no esté escrito queda como cadena vacía. No inventes series, repeticiones ni pesos.
- Si algo es ilegible, transcribe tu mejor lectura y menciónalo en "observaciones" para que el entrenador lo revise.
- Si varias imágenes son páginas de la misma rutina, únelas en el orden lógico sin duplicar.
- Si la imagen no contiene una rutina de entrenamiento, pon "es_rutina" en false, "bloques" vacío y explica en "observaciones" qué se ve.

"observaciones": una o dos frases en español con lo que el entrenador debería revisar (palabras dudosas, datos que faltan). Vacío si todo se leyó con claridad."""


def extraer_rutina_de_imagenes(cliente, imagenes, indicaciones_extra=""):
    """``imagenes``: lista de bytes. Devuelve el dict validado por ``ESQUEMA_EXTRACCION``."""
    if not imagenes:
        raise ErrorIA("Agrega al menos una foto de la rutina.")
    contenido = []
    for datos in imagenes:
        b64, media_type = preparar_imagen(datos)
        contenido.append({"type": "image",
                          "source": {"type": "base64", "media_type": media_type, "data": b64}})
    texto = PROMPT_EXTRACCION
    if indicaciones_extra.strip():
        texto += "\n\nIndicaciones del entrenador para esta foto: " + indicaciones_extra.strip()
    contenido.append({"type": "text", "text": texto})

    respuesta = _crear_mensaje(
        cliente,
        max_tokens=16000,
        output_config={"effort": "medium",
                       "format": {"type": "json_schema", "schema": ESQUEMA_EXTRACCION}},
        messages=[{"role": "user", "content": contenido}],
    )
    _revisar_parada(respuesta)
    try:
        return json.loads(_texto_respuesta(respuesta))
    except ValueError as e:
        raise ErrorIA("La respuesta de la IA no tuvo el formato esperado. Intenta de nuevo.") from e


# ==========================================================================
# 🤖 ASISTENTE CON HERRAMIENTAS
# ==========================================================================

def _obj(propiedades, requeridos=None):
    return {"type": "object", "properties": propiedades,
            "required": requeridos if requeridos is not None else list(propiedades),
            "additionalProperties": False}


_DIA = {"type": "string", "enum": DIAS}
_MODO = {"type": "string", "enum": ["reemplazar", "agregar"],
         "description": "'reemplazar' sustituye lo que había ese día; 'agregar' lo suma al final."}


def definir_herramientas(campos_cliente, opciones):
    """Herramientas del asistente. ``opciones`` trae las listas cerradas de la app."""
    ejercicio_gym = _obj({
        "nombre": {"type": "string"},
        "series": {"type": "string"},
        "reps": {"type": "string", "description": "Ej. '12', '8-10' o '30 s'"},
        "descanso_seg": {"type": "string", "description": "Solo dígitos, en segundos"},
        "peso_kg": {"type": "string", "description": "Número en kg o '0' si no aplica"},
        "rir": {"type": "string", "description": "Reps en reserva o cadena vacía"},
        "nota": {"type": "string", "description": "Técnica, tempo o superserie; puede ir vacía"},
    })
    ejercicio_casa = _obj({
        "nombre": {"type": "string"},
        "series": {"type": "string", "description": "Series o vueltas del circuito"},
        "reps_o_tiempo": {"type": "string", "description": "Ej. '12', '10-12' o '40 s'"},
        "descanso": {"type": "string", "description": "Ej. '20 s' o '45-60 s'"},
        "indicaciones": {"type": "string", "description": "Indicación técnica breve y clara para el cliente"},
        "zona": {"type": "string", "enum": opciones["zonas_casa"]},
    })
    herramientas = [
        {
            "name": "ver_plan",
            "description": ("Devuelve el estado actual del plan del cliente tal como está cargado en el sistema. "
                            "Úsala antes de modificar algo y siempre que necesites datos del cliente."),
            "input_schema": _obj({"seccion": {
                "type": "string",
                "enum": ["todo", "cliente", "calculos", "entrenamiento", "nutricion", "consejos", "rutina_casa"]}}),
        },
        {
            "name": "actualizar_cliente",
            "description": ("Cambia datos del perfil del cliente u objetivos. Para campos con opciones cerradas usa "
                            "exactamente uno de estos valores: "
                            + "; ".join(f"{k}: {', '.join(v)}" for k, v in opciones["cliente"].items())),
            "input_schema": _obj({"cambios": {
                "type": "array",
                "items": _obj({"campo": {"type": "string", "enum": list(campos_cliente)},
                               "valor": {"type": "string"}}),
            }}),
        },
        {
            "name": "establecer_rutina_dia",
            "description": ("Escribe los ejercicios del plan de entrenamiento (gimnasio) de un día. Para dejar un día "
                            "de descanso usa modo 'reemplazar', ejercicios vacíos y enfoque 'Descanso'. "
                            "Máximo 20 ejercicios por día."),
            "input_schema": _obj({"dia": _DIA, "modo": _MODO,
                                  "enfoque": {"type": "string",
                                              "description": "Músculo o enfoque del día; vacío para conservar el actual"},
                                  "ejercicios": {"type": "array", "items": ejercicio_gym}}),
        },
        {
            "name": "establecer_comidas_dia",
            "description": "Escribe las comidas del plan de alimentación de un día. Máximo 20 comidas por día.",
            "input_schema": _obj({"dia": _DIA, "modo": _MODO, "comidas": {
                "type": "array",
                "items": _obj({"comida": {"type": "string", "description": "Ej. Desayuno, Colación, Cena"},
                               "alimentos": {"type": "string", "description": "Alimentos y cantidades"},
                               "kcal": {"type": "string", "description": "Solo dígitos o vacío"}}),
            }}),
        },
        {
            "name": "establecer_consejos",
            "description": "Escribe el texto de consejos y recomendaciones que se imprime en el PDF.",
            "input_schema": _obj({"modo": _MODO, "texto": {"type": "string"}}),
        },
        {
            "name": "crear_rutina_casa",
            "description": ("Crea o reemplaza por completo la rutina para entrenar en casa (se entrega como PDF "
                            "aparte). Usa solo el material que el cliente tiene. Incluye calentamiento, vuelta a la "
                            "calma e indicaciones técnicas claras en cada ejercicio."),
            "input_schema": _obj({
                "titulo": {"type": "string", "description": "Subtítulo de la portada, ej. 'Plan tonificación 4 semanas'"},
                "nivel": {"type": "string", "enum": opciones["niveles_casa"]},
                "duracion_min": {"type": "integer", "description": "Minutos por sesión"},
                "equipo": {"type": "array", "items": {"type": "string", "enum": opciones["equipos_casa"]}},
                "calentamiento": {"type": "string"},
                "enfriamiento": {"type": "string"},
                "notas": {"type": "string", "description": "Notas del coach para el cliente; puede ir vacío"},
                "dias": {"type": "array", "items": _obj({
                    "dia": _DIA,
                    "enfoque": {"type": "string"},
                    "formato": {"type": "string", "description": "Cómo se ejecuta: circuito o series, vueltas y descansos"},
                    "ejercicios": {"type": "array", "items": ejercicio_casa},
                })},
            }),
        },
    ]
    for h in herramientas:
        h["strict"] = True
    return herramientas


SISTEMA_ASISTENTE = """Eres el asistente de IA de Coach System Pro, una herramienta que usan entrenadores personales para armar y entregar planes de entrenamiento y nutrición a sus clientes. Hablas con el entrenador (no con el cliente final) y le ayudas a gestionar la información del cliente, las rutinas de gimnasio, la rutina en casa, la alimentación y los consejos.

Cómo trabajas:
- Las herramientas leen y escriben directamente en el plan que el entrenador ve en pantalla. Antes de modificar algo, consulta el estado con ver_plan para no pisar datos sin querer.
- Cuando el entrenador pida crear o cambiar algo, hazlo con las herramientas en lugar de solo describirlo. Si la petición es ambigua y el cambio borraría trabajo existente, pregunta antes.
- No inventes datos medidos del cliente (peso, medidas, edad). Si faltan, dilo y sugiere completarlos.
- Respeta siempre las lesiones, alergias y limitaciones registradas: elige ejercicios y alimentos compatibles y avísale al entrenador si algo que pidió entra en conflicto con ellas.
- Usa los cálculos del sistema (calorías objetivo, macros, % de grasa) como referencia para nutrición y volumen de entrenamiento.
- Prescripciones realistas y seguras según el nivel del cliente. Nombres de ejercicios en español, claros y estándar.
- Al terminar, resume en pocas líneas qué cambiaste (por ejemplo, qué días y cuántos ejercicios) y sugiere el siguiente paso si aporta. Recuerda que los PDFs se generan con los botones de la app.

Responde en español, con un tono profesional y cercano. Sé breve: el entrenador está trabajando."""


def ejecutar_turno_asistente(cliente, historial, mensaje_usuario, herramientas, ejecutar_herramienta,
                             max_iteraciones=10):
    """Corre un turno completo del asistente.

    ``historial`` se modifica en el lugar (solo se agregan mensajes al final).
    ``ejecutar_herramienta(nombre, entrada) -> (texto_resultado, es_error)``.
    Devuelve (texto_final, acciones) donde acciones es la lista de herramientas usadas.
    """
    historial.append({"role": "user", "content": mensaje_usuario})
    acciones = []
    for _ in range(max_iteraciones):
        try:
            respuesta = _crear_mensaje(
                cliente,
                max_tokens=16000,
                system=[{"type": "text", "text": SISTEMA_ASISTENTE, "cache_control": {"type": "ephemeral"}}],
                tools=herramientas,
                output_config={"effort": "medium"},
                messages=historial,
            )
        except ErrorIA:
            if not acciones:
                historial.pop()  # el turno no llegó a producir nada: se descarta
            raise

        if respuesta.stop_reason == "refusal":
            if not acciones:
                historial.pop()
            return "No puedo ayudar con esa petición. ¿Puedes reformularla?", acciones

        historial.append({"role": "assistant", "content": respuesta.content})

        if respuesta.stop_reason == "pause_turn":
            continue
        if respuesta.stop_reason != "tool_use":
            texto = _texto_respuesta(respuesta)
            if respuesta.stop_reason == "max_tokens":
                texto += "\n\n_(La respuesta quedó cortada por su longitud.)_"
            return texto or "Listo.", acciones

        resultados = []
        for bloque in respuesta.content:
            if bloque.type != "tool_use":
                continue
            try:
                resultado, es_error = ejecutar_herramienta(bloque.name, bloque.input)
            except Exception as e:  # nunca romper el bucle por una herramienta
                resultado, es_error = f"Error al ejecutar {bloque.name}: {e}", True
            acciones.append({"herramienta": bloque.name, "error": es_error,
                             "dia": (bloque.input or {}).get("dia", "") if isinstance(bloque.input, dict) else ""})
            resultados.append({"type": "tool_result", "tool_use_id": bloque.id,
                               "content": resultado, "is_error": es_error})
        historial.append({"role": "user", "content": resultados})

    return ("Hice varios pasos pero no terminé la tarea. Revisa los cambios y dime cómo seguimos.", acciones)


# ==========================================================================
# 📄 LECTURA DE DOCUMENTOS CON IA (opcional; la lectura normal no usa IA)
# ==========================================================================

_ESQUEMA_COMIDA = {
    "type": "object",
    "properties": {"comida": {"type": "string"}, "alimentos": {"type": "string"}, "kcal": {"type": "string"}},
    "required": ["comida", "alimentos", "kcal"],
    "additionalProperties": False,
}

ESQUEMA_DOCUMENTO = {
    "type": "object",
    "properties": {
        "es_plan": {"type": "boolean"},
        "observaciones": {"type": "string"},
        "consejos": {"type": "string"},
        "entrenamiento": ESQUEMA_EXTRACCION["properties"]["bloques"],
        "nutricion": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "etiqueta": {"type": "string"},
                    "dia_semana": {"type": "string", "enum": DIAS + ["Sin especificar"]},
                    "comidas": {"type": "array", "items": _ESQUEMA_COMIDA},
                },
                "required": ["etiqueta", "dia_semana", "comidas"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["es_plan", "observaciones", "consejos", "entrenamiento", "nutricion"],
    "additionalProperties": False,
}

PROMPT_DOCUMENTO = """Eres el asistente de un entrenador personal. Abajo está el texto extraído de un documento (Word, PDF, Excel u otro) con un plan de entrenamiento y/o de alimentación de un cliente. Conviértelo a datos estructurados para cargarlo en el sistema del entrenador, sin perder información.

Entrenamiento ("entrenamiento"): un bloque por día o sesión, con las mismas reglas que una transcripción: "etiqueta" con el título original, "dia_semana" solo si el día está escrito (si no, "Sin especificar"), nombres de ejercicios completos y bien escritos en español, "4x12" separado en series y reps, "descanso_seg" solo dígitos en segundos, "peso_kg" en kg (convierte libras), y técnica, tempo o superseries en "nota". Lo que no esté escrito queda vacío; no inventes cargas ni repeticiones.

Nutrición ("nutricion"): un bloque por día o por menú. Si el plan es un solo menú para todos los días, usa un único bloque con "Sin especificar". Cada comida con su nombre ("Desayuno", "Colación", "Cena"...), los alimentos con sus cantidades tal como aparecen, y "kcal" solo dígitos si aparece.

"consejos": recomendaciones generales del documento (hidratación, descanso, suplementos...), en texto. "observaciones": una o dos frases con lo que el entrenador debería revisar. Si el documento no contiene ningún plan, "es_plan" es false.

TEXTO DEL DOCUMENTO:
"""


def interpretar_documento(cliente, texto):
    """Interpreta con IA el texto de un documento. Devuelve el formato común de importación."""
    texto = (texto or "").strip()
    if not texto:
        raise ErrorIA("El documento no tiene texto para leer.")
    if len(texto) > 400_000:
        raise ErrorIA("El documento es demasiado largo para leerlo de una vez. Divídelo en partes.")
    respuesta = _crear_mensaje(
        cliente,
        max_tokens=16000,  # más alto exige streaming en el SDK
        output_config={"effort": "medium",
                       "format": {"type": "json_schema", "schema": ESQUEMA_DOCUMENTO}},
        messages=[{"role": "user", "content": PROMPT_DOCUMENTO + texto}],
    )
    _revisar_parada(respuesta)
    try:
        datos = json.loads(_texto_respuesta(respuesta))
    except ValueError as e:
        raise ErrorIA("La respuesta de la IA no tuvo el formato esperado. Intenta de nuevo.") from e
    datos["rutina_casa"] = None
    return datos
