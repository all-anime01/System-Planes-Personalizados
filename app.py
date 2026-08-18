import streamlit as st
from fpdf import FPDF
import io as _io
from PIL import Image
import tempfile
import os
import math
import json
import time
import uuid

# ==========================================
# CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(
    page_title="Coach System Pro", 
    layout="wide", 
    page_icon="img/favicon.ico" if os.path.exists("img/favicon.ico") else "🏆"
)

# ==========================================
# 🔒 SISTEMA DE LICENCIAS Y SEGURIDAD
# ==========================================
ARCHIVO_MASTER_LICENCIAS = "licencias_master.json"
ARCHIVO_LICENCIA_LOCAL = "licencia_guardada.json"
ARCHIVO_DEVICE_ID = "dispositivo_id.json"

def obtener_device_id():
    if os.path.exists(ARCHIVO_DEVICE_ID):
        try:
            with open(ARCHIVO_DEVICE_ID, "r", encoding="utf-8") as f:
                return json.load(f).get("id")
        except:
            pass
    nuevo_id = str(uuid.uuid4())
    with open(ARCHIVO_DEVICE_ID, "w", encoding="utf-8") as f:
        json.dump({"id": nuevo_id}, f)
    return nuevo_id

def cargar_licencias_validas():
    if not os.path.exists(ARCHIVO_MASTER_LICENCIAS):
        licencias_ejemplo = {"ADMIN12345": [], "CLIENTE001": [], "FITNESS999": [], "LauFIT96":[]}
        with open(ARCHIVO_MASTER_LICENCIAS, "w", encoding="utf-8") as f:
            json.dump(licencias_ejemplo, f, indent=4)
    
    with open(ARCHIVO_MASTER_LICENCIAS, "r", encoding="utf-8") as f:
        data = json.load(f)
        if isinstance(data, list):
            data = {codigo: [] for codigo in data}
            guardar_licencias_master(data)
        return data

def guardar_licencias_master(data):
    with open(ARCHIVO_MASTER_LICENCIAS, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def verificar_licencia_activa(validas, my_device_id):
    if os.path.exists(ARCHIVO_LICENCIA_LOCAL):
        try:
            with open(ARCHIVO_LICENCIA_LOCAL, "r", encoding="utf-8") as f:
                data = json.load(f)
                codigo_guardado = data.get("licencia_activa")
                if codigo_guardado in validas and my_device_id in validas[codigo_guardado]:
                    return True
        except:
            return False
    return False

def activar_licencia_local(codigo):
    with open(ARCHIVO_LICENCIA_LOCAL, "w", encoding="utf-8") as f:
        json.dump({"licencia_activa": codigo}, f, indent=4)

mi_device_id = obtener_device_id()
licencias_validas = cargar_licencias_validas()
acceso_concedido = verificar_licencia_activa(licencias_validas, mi_device_id)

if not acceso_concedido:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.error("🔒 **SISTEMA BLOQUEADO - SE REQUIERE LICENCIA**")
        st.write("Bienvenido a **Coach System Pro**. Por favor ingresa tu código de acceso (10 dígitos). *Nota: Esta licencia es válida para un máximo de 3 dispositivos.*")
        codigo_ingresado = st.text_input("🔑 Código de Licencia:", max_chars=10, type="password")
        if st.button("🚀 ACTIVAR PROGRAMA", use_container_width=True):
            if codigo_ingresado in licencias_validas:
                dispositivos_registrados = licencias_validas[codigo_ingresado]
                if mi_device_id in dispositivos_registrados or len(dispositivos_registrados) < 3:
                    animacion_placeholder = st.empty()
                    with animacion_placeholder.container():
                        st.markdown("""
                        <style>
                            .spinner-container { position: relative; width: 100px; height: 100px; margin: 0 auto; }
                            .spinner-ring { position: absolute; width: 100%; height: 100%; border-radius: 50%; border: 5px solid rgba(76, 175, 80, 0.2); border-top-color: #4CAF50; border-left-color: #4CAF50; animation: spin 1s cubic-bezier(0.68, -0.55, 0.265, 1.55) infinite; }
                            .spinner-icon { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 45px; filter: drop-shadow(0px 4px 4px rgba(0,0,0,0.2)); animation: pulse 1.5s ease-in-out infinite; }
                            @keyframes spin { 100% { transform: rotate(360deg); } }
                            @keyframes pulse { 0%, 100% { transform: translate(-50%, -50%) scale(1); } 50% { transform: translate(-50%, -50%) scale(1.15); } }
                        </style>
                        <div style="text-align: center; height: 300px; display: flex; flex-direction: column; justify-content: center;">
                            <div class="spinner-container"><div class="spinner-ring"></div><div class="spinner-icon">🏋️</div></div>
                            <h3 style="color: #4CAF50; margin-top: 25px;">Licencia Validada</h3>
                            <p style="font-family: monospace; color: #666; font-size: 14px;">Iniciando entorno premium...</p>
                        </div>
                        """, unsafe_allow_html=True)
                    time.sleep(3) 
                    animacion_placeholder.empty() 
                    if mi_device_id not in dispositivos_registrados:
                        licencias_validas[codigo_ingresado].append(mi_device_id)
                        guardar_licencias_master(licencias_validas)
                    activar_licencia_local(codigo_ingresado)
                    st.rerun() 
                else:
                    st.error(f"❌ **Límite Excedido:** Esta licencia ya se encuentra en uso en 3 dispositivos distintos.")
            elif codigo_ingresado == "":
                st.warning("Por favor, ingresa un código.")
            else:
                st.error("❌ Código inválido. Verifica el código o contacta a tu distribuidor.")
    st.stop() 


# ==========================================
# CÓDIGO PRINCIPAL DE LA APLICACIÓN
# ==========================================

def limpiar_texto(texto):
    if not texto: return ""
    return str(texto).encode('latin-1', 'ignore').decode('latin-1')

# --- 🚀 NUEVO MOTOR MATEMÁTICO ANTI-CORTES ---
def calcular_altura_multicell(pdf_obj, texto, ancho_multicell, alto_linea):
    if not texto: return 0
    # Obtenemos el margen interno real de la librería (suele ser 1mm por lado)
    c_margin = getattr(pdf_obj, 'c_margin', 1.0)
    # Calculamos el ancho EXACTO donde el texto se quiebra
    ancho_real = ancho_multicell - (2 * c_margin) - 0.5 
    
    lineas_totales = 0
    for parrafo in str(texto).split('\n'):
        palabras = parrafo.split(' ')
        linea_actual = ""
        for palabra in palabras:
            prueba = palabra if linea_actual == "" else linea_actual + " " + palabra
            if pdf_obj.get_string_width(prueba) > ancho_real:
                if linea_actual != "":
                    lineas_totales += 1
                    linea_actual = palabra
                else:
                    lineas_totales += max(1, int(pdf_obj.get_string_width(palabra) / ancho_real))
                    linea_actual = ""
            else:
                linea_actual = prueba
        if linea_actual != "":
            lineas_totales += 1
    return lineas_totales * alto_linea

def optimizar_fondo_hd(ruta_imagen, pdf_w, pdf_h, escala=11.81):
    try:
        target_w = int(pdf_w * escala)
        target_h = int(pdf_h * escala)
        img = Image.open(ruta_imagen).convert("RGB")
        img_ratio = img.width / img.height
        target_ratio = target_w / target_h
        
        if img_ratio > target_ratio:
            new_w = int(img.height * target_ratio)
            left = (img.width - new_w) // 2
            img = img.crop((left, 0, left + new_w, img.height))
        else:
            new_h = int(img.width / target_ratio)
            top = (img.height - new_h) // 2
            img = img.crop((0, top, img.width, top + new_h))
            
        img = img.resize((target_w, target_h), getattr(Image, 'Resampling', Image).LANCZOS)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        img.save(tmp.name, format="JPEG", quality=95)
        return tmp.name
    except Exception as e:
        return None


# ==========================================
# 🧠 MOTOR ADAPTATIVO: COMPOSICIÓN, ENERGÍA Y OBJETIVOS
# ==========================================

RANGOS_GRASA = {
    "Hombre": [
        ("Grasa esencial", 2.0, 5.9),
        ("Atleta", 6.0, 13.9),
        ("Fitness", 14.0, 17.9),
        ("Promedio / Aceptable", 18.0, 24.9),
        ("Obesidad", 25.0, 100.0),
    ],
    "Mujer": [
        ("Grasa esencial", 10.0, 13.9),
        ("Atleta", 14.0, 20.9),
        ("Fitness", 21.0, 24.9),
        ("Promedio / Aceptable", 25.0, 31.9),
        ("Obesidad", 32.0, 100.0),
    ],
}

FACTORES_ACTIVIDAD = {
    "Sedentario (oficina, sin ejercicio)": 1.20,
    "Ligero (1-3 días/semana)": 1.375,
    "Moderado (3-5 días/semana)": 1.55,
    "Alto (6-7 días/semana)": 1.725,
    "Atleta (2 sesiones/día o trabajo físico)": 1.90,
}

# ajuste = % sobre el gasto total | prot = g de proteína por kg de referencia
# grasa_pct = % de las calorías que vienen de la grasa | ritmo = % de peso corporal por semana
OBJETIVOS_META = {
    "Pérdida de grasa": {"ajuste": -0.20, "prot": 2.2, "grasa_pct": 0.25, "ritmo": -0.0070},
    "Recomposición corporal": {"ajuste": -0.08, "prot": 2.4, "grasa_pct": 0.27, "ritmo": -0.0030},
    "Mantenimiento": {"ajuste": 0.00, "prot": 1.8, "grasa_pct": 0.28, "ritmo": 0.0000},
    "Ganancia muscular": {"ajuste": 0.12, "prot": 2.0, "grasa_pct": 0.25, "ritmo": 0.0025},
    "Rendimiento deportivo": {"ajuste": 0.05, "prot": 2.0, "grasa_pct": 0.25, "ritmo": 0.0010},
}

SPLITS_SUGERIDOS = {
    1: "Full Body (cuerpo completo): 1 sesión global de alta densidad",
    2: "Full Body A / B alternando patrones de empuje y tracción",
    3: "Full Body A / B / C o Empuje - Tirón - Pierna",
    4: "Torso / Pierna x2 (Upper - Lower - Upper - Lower)",
    5: "Empuje - Tirón - Pierna + Torso - Pierna",
    6: "Empuje - Tirón - Pierna x2 (PPL doble)",
    7: "Empuje - Tirón - Pierna x2 + 1 día de movilidad y cardio regenerativo",
}

PROGRESION_POR_NIVEL = {
    "Principiante": "Progresión lineal: sube 2.5-5 kg (o 1-2 reps) cada semana manteniendo la técnica. Trabaja a RIR 2-3.",
    "Intermedio": "Doble progresión: llega al tope del rango de reps y recién ahí sube el peso. RIR 1-2. Descarga cada 6-8 semanas.",
    "Avanzado": "Ondulante: alterna semanas de intensidad y de volumen. RIR 0-2 en series efectivas. Descarga cada 4-6 semanas.",
}


def _num(valor, defecto=0.0):
    """Convierte texto del formulario a número de forma segura."""
    try:
        texto = str(valor).replace(",", ".").strip()
        if texto == "":
            return defecto
        return float(texto)
    except Exception:
        return defecto


def grasa_navy(sexo, altura, cuello, cintura, cadera):
    """Método US Navy (circunferencias en cm)."""
    try:
        if altura <= 0 or cuello <= 0 or cintura <= 0:
            return None
        if sexo == "Hombre":
            if (cintura - cuello) <= 0:
                return None
            pct = 495 / (1.0324 - 0.19077 * math.log10(cintura - cuello) + 0.15456 * math.log10(altura)) - 450
        else:
            if cadera <= 0 or (cintura + cadera - cuello) <= 0:
                return None
            pct = 495 / (1.29579 - 0.35004 * math.log10(cintura + cadera - cuello) + 0.22100 * math.log10(altura)) - 450
        return round(pct, 1) if 2 <= pct <= 70 else None
    except Exception:
        return None


def grasa_pliegues(sexo, edad, p1, p2, p3):
    """Jackson-Pollock de 3 pliegues (mm) + ecuación de Siri."""
    try:
        suma = p1 + p2 + p3
        if suma <= 0 or edad <= 0:
            return None
        if sexo == "Hombre":
            densidad = 1.10938 - 0.0008267 * suma + 0.0000016 * (suma ** 2) - 0.0002574 * edad
        else:
            densidad = 1.099421 - 0.0009929 * suma + 0.0000023 * (suma ** 2) - 0.0001392 * edad
        if densidad <= 0:
            return None
        pct = (495 / densidad) - 450
        return round(pct, 1) if 2 <= pct <= 70 else None
    except Exception:
        return None


def grasa_deurenberg(imc, edad, sexo):
    """Estimación a partir del IMC (menos precisa, sirve de respaldo)."""
    try:
        if not imc or imc <= 0 or edad <= 0:
            return None
        pct = 1.20 * imc + 0.23 * edad - (10.8 if sexo == "Hombre" else 0.0) - 5.4
        return round(pct, 1) if 2 <= pct <= 70 else None
    except Exception:
        return None


def clasificar_grasa(sexo, pct):
    if pct is None:
        return "Sin datos"
    for nombre, minimo, maximo in RANGOS_GRASA.get(sexo, RANGOS_GRASA["Hombre"]):
        if minimo <= pct <= maximo:
            return nombre
    return "Por debajo del mínimo saludable" if pct < 2 else "Fuera de rango"


def calcular_imc(peso, altura):
    if peso <= 0 or altura <= 0:
        return None
    return round(peso / ((altura / 100.0) ** 2), 1)


def clasificar_imc(imc):
    if imc is None:
        return "Sin datos"
    if imc < 18.5: return "Bajo peso"
    if imc < 25: return "Peso normal"
    if imc < 30: return "Sobrepeso"
    if imc < 35: return "Obesidad grado I"
    if imc < 40: return "Obesidad grado II"
    return "Obesidad grado III"


def tmb_mifflin(sexo, peso, altura, edad):
    if peso <= 0 or altura <= 0 or edad <= 0:
        return None
    base = (10 * peso) + (6.25 * altura) - (5 * edad)
    return round(base + (5 if sexo == "Hombre" else -161))


def tmb_katch(masa_magra):
    if not masa_magra or masa_magra <= 0:
        return None
    return round(370 + 21.6 * masa_magra)


def sugerir_split(dias, nivel, objetivo):
    base = SPLITS_SUGERIDOS.get(int(dias), SPLITS_SUGERIDOS[4])
    if objetivo == "Pérdida de grasa" and dias >= 4:
        base += ". Suma 2 sesiones de cardio: 1 HIIT corto y 1 zona 2 de 30-40 min"
    elif objetivo == "Ganancia muscular":
        base += ". Limita el cardio a 2 sesiones suaves para no comerte el superávit"
    if nivel == "Principiante" and dias > 4:
        base += " (arranca con 3-4 días reales y sube cuando la adherencia sea del 90%)"
    return base


def calcular_perfil(sexo, edad, peso, altura, cuello, cintura, cadera,
                    pliegues, actividad, objetivo, metodo, grasa_manual=None):
    """Devuelve el diccionario completo de composición corporal y energía."""
    p = {
        "sexo": sexo, "edad": edad, "peso": peso, "altura": altura,
        "cuello": cuello, "cintura": cintura, "cadera": cadera,
        "pliegues": pliegues, "actividad": actividad, "objetivo": objetivo,
    }

    p["imc"] = calcular_imc(peso, altura)
    p["imc_cat"] = clasificar_imc(p["imc"])

    p["g_navy"] = grasa_navy(sexo, altura, cuello, cintura, cadera)
    p["g_pliegues"] = grasa_pliegues(sexo, edad, pliegues[0], pliegues[1], pliegues[2])
    p["g_imc"] = grasa_deurenberg(p["imc"], edad, sexo)

    grasa, metodo_usado = None, "Sin datos suficientes"
    if metodo.startswith("Manual") and grasa_manual and grasa_manual > 0:
        grasa, metodo_usado = round(grasa_manual, 1), "Valor manual (báscula / DEXA)"
    elif metodo.startswith("Circunferencias") and p["g_navy"]:
        grasa, metodo_usado = p["g_navy"], "Circunferencias (US Navy)"
    elif metodo.startswith("Pliegues") and p["g_pliegues"]:
        grasa, metodo_usado = p["g_pliegues"], "Pliegues cutáneos (Jackson-Pollock 3 + Siri)"
    elif metodo.startswith("Estimación") and p["g_imc"]:
        grasa, metodo_usado = p["g_imc"], "Estimación por IMC (Deurenberg)"
    else:
        if grasa_manual and grasa_manual > 0:
            grasa, metodo_usado = round(grasa_manual, 1), "Valor manual (báscula / DEXA)"
        elif p["g_pliegues"]:
            grasa, metodo_usado = p["g_pliegues"], "Pliegues cutáneos (Jackson-Pollock 3 + Siri)"
        elif p["g_navy"]:
            grasa, metodo_usado = p["g_navy"], "Circunferencias (US Navy)"
        elif p["g_imc"]:
            grasa, metodo_usado = p["g_imc"], "Estimación por IMC (Deurenberg)"

    p["grasa"] = grasa
    p["metodo_usado"] = metodo_usado
    p["categoria"] = clasificar_grasa(sexo, grasa)

    if grasa and peso > 0:
        p["masa_grasa"] = round(peso * grasa / 100.0, 1)
        p["masa_magra"] = round(peso - p["masa_grasa"], 1)
    else:
        p["masa_grasa"] = None
        p["masa_magra"] = None

    p["icc"] = round(cintura / cadera, 2) if (cintura > 0 and cadera > 0) else None
    p["rce"] = round(cintura / altura, 2) if (cintura > 0 and altura > 0) else None
    if p["rce"] is None:
        p["rce_alerta"] = "Sin datos"
    elif p["rce"] < 0.43:
        p["rce_alerta"] = "Muy bajo, revisar"
    elif p["rce"] <= 0.52:
        p["rce_alerta"] = "Saludable"
    elif p["rce"] <= 0.57:
        p["rce_alerta"] = "Riesgo aumentado"
    else:
        p["rce_alerta"] = "Riesgo alto"

    tmb_m = tmb_mifflin(sexo, peso, altura, edad)
    tmb_k = tmb_katch(p["masa_magra"])
    p["tmb_mifflin"] = tmb_m
    p["tmb_katch"] = tmb_k
    p["tmb"] = tmb_k or tmb_m
    p["formula_tmb"] = "Katch-McArdle (usa masa magra)" if tmb_k else "Mifflin-St Jeor"

    factor = FACTORES_ACTIVIDAD.get(actividad, 1.55)
    p["factor"] = factor
    p["tdee"] = round(p["tmb"] * factor) if p["tmb"] else None

    cfg = OBJETIVOS_META.get(objetivo, OBJETIVOS_META["Mantenimiento"])
    p["cfg"] = cfg
    if p["tdee"]:
        kcal = round(p["tdee"] * (1 + cfg["ajuste"]))
        piso = round((p["tmb"] or 0) * 1.05)
        p["kcal"] = max(kcal, piso) if piso else kcal
    else:
        p["kcal"] = None

    if p["kcal"] and peso > 0:
        peso_ref = peso if not p["masa_magra"] else min(peso, p["masa_magra"] * 1.25)
        prot_g = int(round(peso_ref * cfg["prot"]))
        grasa_g = int(round(p["kcal"] * cfg["grasa_pct"] / 9.0))
        carb_g = int(round((p["kcal"] - (prot_g * 4) - (grasa_g * 9)) / 4.0))
        if carb_g < 0:
            carb_g = 0
        p["macros"] = {"prot": prot_g, "grasa": grasa_g, "carb": carb_g}
        p["agua"] = round(peso * 0.04, 1)
    else:
        p["macros"] = None
        p["agua"] = None

    p["ritmo_kg"] = round(peso * cfg["ritmo"], 2) if peso > 0 else None
    return p


def peso_para_grasa_objetivo(masa_magra, pct_objetivo):
    """Peso corporal necesario para llegar a un % de grasa dado, conservando la masa magra."""
    if not masa_magra or not pct_objetivo or pct_objetivo <= 0 or pct_objetivo >= 70:
        return None
    return round(masa_magra / (1 - (pct_objetivo / 100.0)), 1)


def semanas_estimadas(peso_actual, peso_meta, ritmo_kg):
    if not peso_actual or not peso_meta or not ritmo_kg or ritmo_kg == 0:
        return None
    delta = peso_meta - peso_actual
    if delta == 0:
        return 0
    if (delta > 0) != (ritmo_kg > 0):
        return None
    return int(math.ceil(abs(delta) / abs(ritmo_kg)))


def texto_detalle_entreno(item, compacto=False):
    """Arma la línea de detalle del ejercicio tal como sale impresa en el PDF."""
    if compacto:
        base = "%sS | %sR | %ss" % (limpiar_texto(item.get('s', '')),
                                    limpiar_texto(item.get('r', '')),
                                    limpiar_texto(item.get('seg', '')))
    else:
        base = "%s SETS | %s REPS | %s SEG" % (limpiar_texto(item.get('s', '')),
                                               limpiar_texto(item.get('r', '')),
                                               limpiar_texto(item.get('seg', '')))
    extras = []
    peso = str(item.get('peso (kg)', '') or '').strip()
    if peso and peso not in ("0", "0.0"):
        extras.append("%s KG" % limpiar_texto(peso))
    rir = str(item.get('rir', '') or '').strip()
    if rir and rir != "-":
        extras.append("RIR %s" % limpiar_texto(rir))
    if extras:
        base += ("\n" if compacto else " | ") + " | ".join(extras)
    nota = limpiar_texto(str(item.get('nota', '') or '').strip())
    if nota:
        base += "\n" + nota
    return base


CATALOGO_ANTIANTOJOS = [
    ("Chocolate", "Onza de chocolate 85% cacao o cacao puro con yogur griego", "20-25 g", "Toma agua y espera 10 min: el antojo real baja solo."),
    ("Papas fritas / snack salado", "Palomitas sin mantequilla o garbanzos tostados", "30 g", "El crujido sacia igual con la mitad de grasa."),
    ("Refresco / gaseosa", "Agua mineral con limón y hielo o té helado sin azúcar", "500 ml", "Agrega menta o jengibre para que sepa a premio."),
    ("Pan dulce / bollería", "Tostada integral con crema de cacahuate y canela", "1 rebanada", "La canela ayuda a estabilizar la glucosa."),
    ("Helado", "Yogur griego congelado con fruta o nice cream de plátano", "150 g", "Congela plátano en rodajas y licúalo al momento."),
    ("Dulces / gomitas", "Fruta congelada (uva, mango) o gelatina sin azúcar", "1 taza", "El frío alarga el consumo y sacia más."),
    ("Comida rápida nocturna", "Wrap integral de pollo con vegetales", "1 pieza", "Cena proteína + fibra y el picoteo desaparece."),
    ("Café con azúcar y crema", "Café con leche descremada, canela o stevia", "1 taza", "Baja el azúcar un 25% cada semana."),
    ("Alcohol de fin de semana", "Agua con gas, limón y hielo en copa de vino", "1 copa", "Alterna 1 bebida y 1 vaso de agua."),
    ("Cereal azucarado", "Avena con proteína, fruta y frutos secos", "40 g", "Déjala lista la noche anterior (overnight oats)."),
]

BACKUP_FILE = "backup_progreso.json"

def guardar_progreso_local():
    estado_limpio = {k: v for k, v in st.session_state.items() if isinstance(v, (str, int, float, bool))}
    with open(BACKUP_FILE, "w", encoding="utf-8") as f:
        json.dump(estado_limpio, f, ensure_ascii=False, indent=4)

def cargar_progreso_local():
    if os.path.exists(BACKUP_FILE):
        with open(BACKUP_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            for k, v in data.items():
                st.session_state[k] = v
        st.rerun()

def generar_json_descarga():
    estado_limpio = {k: v for k, v in st.session_state.items() if isinstance(v, (str, int, float, bool))}
    return json.dumps(estado_limpio, ensure_ascii=False, indent=4)

def cargar_desde_archivo(uploaded_file):
    if uploaded_file is not None:
        data = json.load(uploaded_file)
        for k, v in data.items():
            st.session_state[k] = v
        st.rerun()

BG_IMAGES = {
    "Urban Power": "bg_urban.jpg",
    "Dark Elite": "bg_dark.jpg",
    "Ocean Fitness": "bg_ocean.jpg",
    "Cyber Neon": "bg_cyber.jpg",
    "Eco Wellness": "bg_eco.jpg",
    "Clean Minimal": None,
    "Rose Gold": "bg_rosegold.jpg",
    "Violet Luxe": "bg_violet.jpg",
    "Sunset Energy": "bg_sunset.jpg",
    "Steel Pro": "bg_steel.jpg",
    "Gold Elite": "bg_gold.jpg",
}

# Plantillas de fondo oscuro: el texto dentro de las cajas va en claro
ESTILOS_OSCUROS = ["Dark Elite", "Cyber Neon", "Violet Luxe", "Gold Elite"]
# Plantillas cuyo color de acento es claro: el texto encima va en negro
ESTILOS_ACENTO_CLARO = ["Urban Power", "Cyber Neon", "Clean Minimal", "Gold Elite"]

LISTA_PLANTILLAS = [
    "Urban Power", "Clean Minimal", "Dark Elite", "Ocean Fitness", "Cyber Neon",
    "Eco Wellness", "Rose Gold", "Violet Luxe", "Sunset Energy", "Steel Pro", "Gold Elite",
]

DESCRIPCION_PLANTILLAS = {
    "Urban Power": "Amarillo y negro, alto impacto. La clásica de gimnasio.",
    "Clean Minimal": "Blanco y negro, solo líneas. Ideal para imprimir y ahorrar tinta.",
    "Dark Elite": "Negro con carmesí. Look premium y agresivo.",
    "Ocean Fitness": "Azules claros y frescos. Transmite calma y constancia.",
    "Cyber Neon": "Negro con verde neón. Estética tech y futurista.",
    "Eco Wellness": "Verdes suaves sobre crema. Salud, nutrición y bienestar.",
    "Rose Gold": "Rosa empolvado sobre crema, con mancuernas de fondo. Elegante y femenina.",
    "Violet Luxe": "Violeta eléctrico sobre morado profundo, con foco de gimnasio. Moderna y premium.",
    "Sunset Energy": "Naranja atardecer con líneas de velocidad. Pura energía y motivación.",
    "Steel Pro": "Azul acero sobre plano técnico. Sobria, analítica y profesional.",
    "Gold Elite": "Negro con dorado y discos olímpicos. La más lujosa del catálogo.",
}

def generar_pdf_profesional(datos_rutina, datos_nutricion, consejos, config, cliente, logo_file, estilo, formato, tipo_fondo,
                            inc_entreno, inc_nutri, inc_consejos,
                            objetivos=None, perfil=None, antiantojos=None,
                            inc_objetivos=False, inc_composicion=False, inc_antiantojos=False,
                            calidad_fondo=11.81):
    objetivos = objetivos or {}
    perfil = perfil or {}
    antiantojos = antiantojos or []
    orientacion = 'L' if formato == "Horizontal (Tabla 7 Días)" else 'P'
    pdf = FPDF(orientation=orientacion)
    pdf.set_auto_page_break(auto=False) 
    
    bg_filename = BG_IMAGES.get(estilo)
    usar_textura = (tipo_fondo == "Personalizado (Textura/Imagen)")

    if estilo == "Dark Elite":
        c_bg, c_texto, c_acento, c_caja = (20, 20, 20), (240, 240, 240), (200, 10, 50), (40, 40, 40)
    elif estilo == "Clean Minimal":
        c_bg, c_texto, c_acento, c_caja = (255, 255, 255), (0, 0, 0), (0, 0, 0), (255, 255, 255)
    elif estilo == "Ocean Fitness":
        c_bg, c_texto, c_acento, c_caja = (240, 248, 255), (0, 20, 40), (0, 105, 180), (225, 240, 250)
    elif estilo == "Cyber Neon":
        c_bg, c_texto, c_acento, c_caja = (10, 10, 15), (240, 255, 240), (57, 255, 20), (25, 25, 35)
    elif estilo == "Eco Wellness":
        c_bg, c_texto, c_acento, c_caja = (248, 253, 248), (40, 60, 40), (100, 180, 60), (240, 250, 240)
    elif estilo == "Rose Gold":
        c_bg, c_texto, c_acento, c_caja = (253, 246, 244), (74, 45, 44), (183, 110, 121), (250, 234, 231)
    elif estilo == "Violet Luxe":
        c_bg, c_texto, c_acento, c_caja = (24, 18, 35), (238, 233, 248), (139, 92, 246), (43, 33, 60)
    elif estilo == "Sunset Energy":
        c_bg, c_texto, c_acento, c_caja = (255, 247, 237), (67, 32, 15), (234, 88, 12), (255, 236, 214)
    elif estilo == "Steel Pro":
        c_bg, c_texto, c_acento, c_caja = (237, 241, 245), (24, 34, 45), (45, 72, 99), (255, 255, 255)
    elif estilo == "Gold Elite":
        c_bg, c_texto, c_acento, c_caja = (18, 17, 15), (246, 241, 229), (198, 160, 58), (39, 36, 30)
    else: 
        c_bg, c_texto, c_acento, c_caja = (255, 245, 200), (20, 20, 20), (255, 204, 0), (255, 255, 240)

    def obtener_ancho_caja():
        return pdf.w - 30

    def dibujar_fondo_y_cabecera(titulo_pagina):
        pdf.add_page()
        fondo_dibujado = False
        if usar_textura and bg_filename:
            ruta_imagen = os.path.join("img", bg_filename)
            if os.path.exists(ruta_imagen):
                fondo_hd = optimizar_fondo_hd(ruta_imagen, pdf.w, pdf.h, calidad_fondo)
                if fondo_hd:
                    try:
                        pdf.image(fondo_hd, x=0, y=0, w=pdf.w, h=pdf.h)
                        fondo_dibujado = True
                        os.remove(fondo_hd) 
                    except Exception:
                        pass
        
        if not fondo_dibujado and c_bg != (255, 255, 255):
            pdf.set_fill_color(*c_bg)
            pdf.rect(0, 0, pdf.w, pdf.h, 'F')
            
        if logo_file is not None:
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                    tmp_file.write(logo_file.getvalue())
                    logo_path = tmp_file.name
                pdf.image(logo_path, x=15, y=10, w=25)
                os.remove(logo_path)
            except Exception:
                pass

        pdf.set_text_color(*c_texto)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 10, limpiar_texto(config['entrenador']).upper(), ln=True, align='C')
        pdf.set_font("Arial", 'B', 22)
        pdf.cell(0, 8, titulo_pagina, ln=True, align='C')
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 6, f"VIGENCIA: {limpiar_texto(config['fecha_inicio'])} A {limpiar_texto(config['fecha_fin'])}", ln=True, align='C')
        pdf.ln(3)

        caja_w = obtener_ancho_caja()
        y_cliente = pdf.get_y()
        
        if estilo == "Clean Minimal":
            pdf.set_draw_color(0, 0, 0)
            pdf.rect(15, y_cliente, caja_w, 8, 'D')
            pdf.set_text_color(50, 50, 50)
        elif estilo == "Urban Power":
             pdf.set_fill_color(255, 255, 255)
             pdf.rect(15, y_cliente, caja_w, 8, 'F')
             pdf.set_text_color(0, 0, 0)
        else:
            pdf.set_fill_color(*c_caja)
            pdf.rect(15, y_cliente, caja_w, 8, 'F')
            pdf.set_text_color(220,220,220) if estilo in ESTILOS_OSCUROS else pdf.set_text_color(80,90,80) if estilo == "Eco Wellness" else pdf.set_text_color(50,50,50)
            
        pdf.set_xy(15, y_cliente + 2)
        pdf.set_font("Arial", 'B', 8)
        info_c = f"USUARIO: {limpiar_texto(cliente['nombre']).upper()}  |  EDAD: {limpiar_texto(cliente['edad'])}  |  PESO: {limpiar_texto(cliente['peso'])}  |  ALTURA: {limpiar_texto(cliente['altura'])}"
        if cliente.get('grasa'):
            info_c += f"  |  GRASA: {limpiar_texto(cliente['grasa'])}%"
        if cliente.get('objetivo'):
            info_c += f"  |  META: {limpiar_texto(cliente['objetivo']).upper()}"
        pdf.cell(caja_w, 4, info_c, align='C')
        return pdf.get_y() + 8

    def dibujar_pie_pagina():
        pdf.set_y(pdf.h - 15)
        if estilo in ["Urban Power"]:
            pdf.set_fill_color(0,0,0)
            pdf.rect((pdf.w/2) - 45, pdf.h - 17, 90, 10, 'F')
            pdf.set_text_color(255,255,255)
        elif estilo in ["Cyber Neon"]:
            pdf.set_fill_color(*c_caja)
            pdf.rect((pdf.w/2) - 45, pdf.h - 17, 90, 10, 'F')
            pdf.set_text_color(255, 255, 255)
        else:
            pdf.set_text_color(*c_texto)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 6, limpiar_texto(config['redes']), align='C')

    def procesar_modulo(titulo_pagina, datos_dict, tipo_modulo):
        y_offset = dibujar_fondo_y_cabecera(titulo_pagina) + 5
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        
        # =========================================================
        # ESTRUCTURA HORIZONTAL (TABLA 7 DÍAS) - ACTUALIZADA
        # =========================================================
        if formato == "Horizontal (Tabla 7 Días)":
            caja_w = obtener_ancho_caja()
            col_w = caja_w / 7 
            
            def dibujar_cabecera_horizontal(y_pos):
                # Clean Minimal tiene el acento en negro: se rellena en blanco para
                # que el texto negro de los dias siga siendo legible.
                if estilo == "Clean Minimal": pdf.set_fill_color(255, 255, 255)
                else: pdf.set_fill_color(*c_acento)
                if estilo in ESTILOS_ACENTO_CLARO: pdf.set_text_color(0, 0, 0)
                else: pdf.set_text_color(255, 255, 255)

                if estilo == "Clean Minimal": pdf.set_draw_color(0, 0, 0)
                elif estilo == "Cyber Neon": pdf.set_draw_color(*c_acento)
                else: pdf.set_draw_color(200, 200, 200)

                x_s = 15
                for d in dias:
                    pdf.rect(x_s, y_pos, col_w, 10, 'DF')
                    enf = datos_dict.get(d, {}).get("enfoque", "")
                    
                    if enf and tipo_modulo == "entreno":
                        pdf.set_font("Arial", 'B', 8)
                        pdf.set_xy(x_s, y_pos + 1)
                        pdf.cell(col_w, 4, d.upper(), align='C')
                        
                        pdf.set_font("Arial", 'B', 5.5)
                        pdf.set_xy(x_s + 0.5, y_pos + 4.5)
                        pdf.multi_cell(col_w - 1, 2.5, limpiar_texto(enf).upper()[:50], align='C')
                    else:
                        pdf.set_font("Arial", 'B', 9)
                        pdf.set_xy(x_s, y_pos + 3)
                        pdf.cell(col_w, 4, d.upper(), align='C')
                    x_s += col_w
                return y_pos + 10

            y_offset = dibujar_cabecera_horizontal(y_offset)
            
            max_items = 0
            for dia in dias:
                items_lista = datos_dict.get(dia, {}).get("items", [])
                valid_items = [it for it in items_lista if it['nombre']]
                if len(valid_items) > max_items: max_items = len(valid_items)
            
            pdf.set_text_color(*c_texto)

            for i in range(max_items):
                max_h = 16 
                alturas_celdas = {} 
                
                # --- PASO 1: Calcular la altura máxima exacta (Con Acolchado) ---
                for dia in dias:
                    items_lista = datos_dict.get(dia, {}).get("items", [])
                    valid_items = [it for it in items_lista if it['nombre']]
                    if i < len(valid_items):
                        item = valid_items[i]
                        
                        nom_limpio = limpiar_texto(item['nombre']).upper()
                        pdf.set_font("Arial", 'B', 7.5)
                        nom_h = calcular_altura_multicell(pdf, nom_limpio, col_w - 2, 3.5)
                        
                        if tipo_modulo == "entreno":
                            det = texto_detalle_entreno(item, compacto=True)
                        else:
                            det = limpiar_texto(item['detalle'])
                            
                        pdf.set_font("Arial", '', 7)
                        det_h = calcular_altura_multicell(pdf, det, col_w - 2, 3.5)
                        
                        h_total_item = nom_h + det_h + 1.5 
                        
                        alturas_celdas[dia] = {
                            "nom_h": nom_h,
                            "det_h": det_h,
                            "h_total": h_total_item,
                            "nom": nom_limpio,
                            "det": det
                        }
                        
                        # Agregamos 10mm de padding generoso a la altura total (5 arriba y 5 abajo)
                        if h_total_item + 10 > max_h: 
                            max_h = h_total_item + 10
                
                if y_offset + max_h > pdf.h - 22:
                    dibujar_pie_pagina()
                    y_offset = dibujar_fondo_y_cabecera(titulo_pagina) + 5
                    y_offset = dibujar_cabecera_horizontal(y_offset)
                    pdf.set_text_color(*c_texto)

                # --- PASO 2: Dibujar las cajas y Auto-Centrar Verticalmente ---
                fill_row = True if i % 2 == 0 else False
                if estilo == "Clean Minimal":
                    pdf.set_fill_color(245,245,245) if fill_row else pdf.set_fill_color(255,255,255)
                else:
                    pdf.set_fill_color(*c_caja) if fill_row else pdf.set_fill_color(*c_bg)
                
                for col_idx, dia in enumerate(dias):
                    x_pos = 15 + (col_idx * col_w)
                    style_cell = 'D' if estilo == "Clean Minimal" and not fill_row else 'DF'
                    
                    pdf.rect(x_pos, y_offset, col_w, max_h, style_cell)
                    
                    if dia in alturas_celdas:
                        cell_data = alturas_celdas[dia]
                        
                        y_start = y_offset + (max_h - cell_data["h_total"]) / 2
                        
                        pdf.set_xy(x_pos + 1, y_start)
                        pdf.set_font("Arial", 'B', 7.5)
                        pdf.multi_cell(col_w - 2, 3.5, cell_data["nom"], align='C')
                        
                        y_det = pdf.get_y()
                        pdf.set_xy(x_pos + 1, y_det + 1.5)
                        pdf.set_font("Arial", '', 7)
                        pdf.multi_cell(col_w - 2, 3.5, cell_data["det"], align='C')
                            
                y_offset += max_h

        # =========================================================
        # ESTRUCTURA VERTICAL (BLOQUES)
        # =========================================================
        else:
            for dia in dias:
                data_dia = datos_dict.get(dia, {"enfoque": "", "items": []})
                items = data_dia.get("items", [])
                enfoque = data_dia.get("enfoque", "")
                
                valid_items = [it for it in items if it['nombre']]
                
                if not valid_items and not enfoque: continue 
                
                alturas_col_izq, alturas_col_der = [], []
                mitad = math.ceil(len(valid_items) / 2)
                
                for idx, item in enumerate(valid_items):
                    nom_limpio = limpiar_texto(item['nombre']).upper()
                    pdf.set_font("Arial", 'B', 8)
                    nom_h = calcular_altura_multicell(pdf, nom_limpio, 60, 4)
                    
                    if tipo_modulo == "entreno":
                        texto_detalle = texto_detalle_entreno(item)
                        pdf.set_font("Arial", 'I', 7.5)
                        det_h = calcular_altura_multicell(pdf, texto_detalle, 60, 4)
                    else:
                        det_limpio = limpiar_texto(item['detalle'])
                        pdf.set_font("Arial", '', 7.5)
                        det_h = calcular_altura_multicell(pdf, det_limpio, 60, 3.5)
                    
                    h_item = nom_h + det_h
                    if idx < mitad: alturas_col_izq.append(h_item)
                    else: alturas_col_der.append(h_item)
                
                alto_izq = sum(alturas_col_izq) + (len(alturas_col_izq) * 4) 
                alto_der = sum(alturas_col_der) + (len(alturas_col_der) * 4)
                altura_caja = max(20, alto_izq, alto_der) + 6 
                
                if y_offset + altura_caja > 265:
                    dibujar_pie_pagina()
                    y_offset = dibujar_fondo_y_cabecera(titulo_pagina) + 5
                
                if estilo == "Clean Minimal":
                    pdf.set_draw_color(0, 0, 0)
                    pdf.rect(15, y_offset, 40, altura_caja, 'D') 
                    pdf.rect(60, y_offset, 135, altura_caja, 'D') 
                else:
                    pdf.set_fill_color(*c_acento)
                    pdf.rect(15, y_offset, 40, altura_caja, 'F')
                    pdf.set_fill_color(*c_caja)
                    pdf.rect(60, y_offset, 135, altura_caja, 'F')

                y_cabecera = y_offset + (altura_caja/2) - (4 if enfoque and tipo_modulo == "entreno" else 2.5)
                pdf.set_xy(15, y_cabecera)
                pdf.set_font("Arial", 'B', 11)
                
                if estilo in ESTILOS_ACENTO_CLARO: pdf.set_text_color(0,0,0)
                else: pdf.set_text_color(255,255,255) 
                    
                pdf.cell(40, 5, dia.upper(), align='C')

                if enfoque and tipo_modulo == "entreno":
                    pdf.set_font("Arial", 'B', 7)
                    pdf.set_xy(16, pdf.get_y() + 4)
                    pdf.multi_cell(38, 3.5, limpiar_texto(enfoque).upper()[:40], align='C')

                pdf.set_text_color(220,220,220) if estilo in ESTILOS_OSCUROS else pdf.set_text_color(50,50,50)
                
                y_col_izq = y_offset + 3
                y_col_der = y_offset + 3
                
                for idx, item in enumerate(valid_items):
                    columna = 0 if idx < mitad else 1 
                    x_pos = 63 + (columna * 65) 
                    y_pos = y_col_izq if columna == 0 else y_col_der
                    
                    nom_limpio = limpiar_texto(item['nombre']).upper()
                    
                    pdf.set_xy(x_pos, y_pos)
                    pdf.set_font("Arial", 'B', 8)
                    pdf.multi_cell(60, 4, nom_limpio, align='L')
                    y_pos = pdf.get_y() 
                    
                    if tipo_modulo == "entreno":
                        texto_detalle = texto_detalle_entreno(item)
                        
                        pdf.set_xy(x_pos, y_pos)
                        pdf.set_font("Arial", 'I', 7.5)
                        pdf.multi_cell(60, 4, texto_detalle, align='L')
                        y_pos = pdf.get_y() + 4
                    else: 
                        det_limpio = limpiar_texto(item['detalle'])
                        pdf.set_xy(x_pos, y_pos)
                        pdf.set_font("Arial", '', 7.5)
                        pdf.multi_cell(60, 3.5, det_limpio, align='L')
                        y_pos = pdf.get_y() + 4
                    
                    if columna == 0: y_col_izq = y_pos
                    else: y_col_der = y_pos

                y_offset += altura_caja + 4 
            
        dibujar_pie_pagina()

    # ==========================================
    # 🧩 RENDER GENÉRICO DE TABLAS Y BLOQUES
    # ==========================================
    def _color_texto_encabezado():
        if estilo in ESTILOS_ACENTO_CLARO:
            return (0, 0, 0)
        return (255, 255, 255)

    def _preparar_bordes():
        if estilo == "Clean Minimal": pdf.set_draw_color(0, 0, 0)
        elif estilo == "Cyber Neon": pdf.set_draw_color(*c_acento)
        else: pdf.set_draw_color(200, 200, 200)

    def dibujar_subtitulo(y, texto, titulo_pagina, espacio_minimo=34):
        caja_w = obtener_ancho_caja()
        # Exige sitio para el subtitulo + el encabezado de la tabla + al menos una fila,
        # para que nunca quede un titulo colgando solo al pie de la pagina.
        if y + espacio_minimo > pdf.h - 22:
            dibujar_pie_pagina()
            y = dibujar_fondo_y_cabecera(titulo_pagina + " (CONT.)") + 5
        if estilo == "Clean Minimal":
            pdf.set_fill_color(255, 255, 255)
            pdf.set_draw_color(0, 0, 0)
            pdf.rect(15, y, caja_w, 7, 'DF')
        else:
            pdf.set_fill_color(*c_acento)
            pdf.rect(15, y, caja_w, 7, 'F')
        pdf.set_text_color(*_color_texto_encabezado())
        pdf.set_xy(15, y + 1.5)
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(caja_w, 4, limpiar_texto(texto).upper(), align='C')
        pdf.set_text_color(*c_texto)
        return y + 9

    def dibujar_caja_texto(y, titulo_pagina, texto, fuente=9, alto_linea=4.5):
        caja_w = obtener_ancho_caja()
        txt = limpiar_texto(texto)
        pdf.set_font("Arial", '', fuente)
        alto = calcular_altura_multicell(pdf, txt, caja_w - 8, alto_linea) + 8
        if y + alto > pdf.h - 22:
            dibujar_pie_pagina()
            y = dibujar_fondo_y_cabecera(titulo_pagina + " (CONT.)") + 5
        if estilo == "Clean Minimal":
            pdf.set_draw_color(0, 0, 0)
            pdf.rect(15, y, caja_w, alto, 'D')
        else:
            pdf.set_fill_color(*c_caja)
            pdf.rect(15, y, caja_w, alto, 'F')
        pdf.set_text_color(*c_texto)
        pdf.set_xy(19, y + 4)
        pdf.set_font("Arial", '', fuente)
        pdf.multi_cell(caja_w - 8, alto_linea, txt, align='L')
        return y + alto + 4

    def dibujar_tabla(titulo_pagina, encabezados, filas, pesos, y_ini=None):
        caja_w = obtener_ancho_caja()
        suma = float(sum(pesos))
        anchos = [caja_w * (p / suma) for p in pesos]
        y = (dibujar_fondo_y_cabecera(titulo_pagina) + 5) if y_ini is None else y_ini

        def _fila_encabezado(y_pos):
            _preparar_bordes()
            if estilo == "Clean Minimal": pdf.set_fill_color(255, 255, 255)
            else: pdf.set_fill_color(*c_acento)
            pdf.set_text_color(*_color_texto_encabezado())
            pdf.set_font("Arial", 'B', 7.5)
            x = 15
            for txt, w in zip(encabezados, anchos):
                pdf.rect(x, y_pos, w, 8, 'DF')
                pdf.set_xy(x, y_pos + 2)
                pdf.cell(w, 4, limpiar_texto(str(txt)).upper(), align='C')
                x += w
            pdf.set_text_color(*c_texto)
            return y_pos + 8

        # Se miden todas las filas primero: asi sabemos si el encabezado cabe junto
        # con su primera fila antes de pintarlo.
        filas_medidas = []
        for fila in filas:
            celdas = [limpiar_texto(str(celda)) for celda in fila]
            h_fila = 7.0
            for j, txt in enumerate(celdas):
                pdf.set_font("Arial", 'B' if j == 0 else '', 7.5)
                alto_txt = calcular_altura_multicell(pdf, txt, anchos[j] - 2, 3.6)
                if alto_txt + 4 > h_fila:
                    h_fila = alto_txt + 4
            filas_medidas.append((celdas, h_fila))

        if filas_medidas and (y + 8 + filas_medidas[0][1]) > pdf.h - 22:
            dibujar_pie_pagina()
            y = dibujar_fondo_y_cabecera(titulo_pagina + " (CONT.)") + 5

        y = _fila_encabezado(y)

        for idx, (celdas, h_fila) in enumerate(filas_medidas):
            if y + h_fila > pdf.h - 22:
                dibujar_pie_pagina()
                y = dibujar_fondo_y_cabecera(titulo_pagina + " (CONT.)") + 5
                y = _fila_encabezado(y)

            par = (idx % 2 == 0)
            if estilo == "Clean Minimal":
                pdf.set_fill_color(245, 245, 245) if par else pdf.set_fill_color(255, 255, 255)
            else:
                pdf.set_fill_color(*c_caja) if par else pdf.set_fill_color(*c_bg)

            _preparar_bordes()
            pdf.set_text_color(*c_texto)
            x = 15
            for j, txt in enumerate(celdas):
                modo = 'D' if (estilo == "Clean Minimal" and not par) else 'DF'
                pdf.rect(x, y, anchos[j], h_fila, modo)
                pdf.set_font("Arial", 'B' if j == 0 else '', 7.5)
                alto_txt = calcular_altura_multicell(pdf, txt, anchos[j] - 2, 3.6)
                pdf.set_xy(x + 1, y + max(1.5, (h_fila - alto_txt) / 2.0))
                pdf.multi_cell(anchos[j] - 2, 3.6, txt, align='L' if anchos[j] >= 35 else 'C')
                x += anchos[j]
            y += h_fila
        return y

    # ==========================================
    # 📄 PÁGINAS NUEVAS DEL SISTEMA
    # ==========================================
    def pagina_objetivos():
        titulo = "OBJETIVOS Y METAS"
        y = dibujar_fondo_y_cabecera(titulo) + 5

        resumen = [f for f in objetivos.get("resumen", []) if str(f[1]).strip()]
        if resumen:
            y = dibujar_subtitulo(y, "Plan de Objetivos", titulo)
            y = dibujar_tabla(titulo, ["Concepto", "Detalle"], resumen, [1, 2], y_ini=y) + 4

        estrategia = str(objetivos.get("estrategia", "") or "").strip()
        if estrategia:
            y = dibujar_subtitulo(y, "Estrategia Adaptada al Cliente", titulo)
            y = dibujar_caja_texto(y, titulo, estrategia)

        metas = [m for m in objetivos.get("metas", []) if str(m[1]).strip()]
        if metas:
            y = dibujar_subtitulo(y, "Metas por Periodo", titulo)
            y = dibujar_tabla(titulo, ["Periodo", "Meta / Acción", "Cómo se mide"], metas, [2, 5, 3], y_ini=y) + 4

        habitos = [h for h in objetivos.get("habitos", []) if str(h[0]).strip()]
        if habitos:
            filas = [[h[0], h[1], "", "", "", "", "", "", ""] for h in habitos]
            y = dibujar_subtitulo(y, "Hábitos Clave - Checklist Semanal", titulo)
            y = dibujar_tabla(titulo, ["Hábito", "Frecuencia", "L", "M", "X", "J", "V", "S", "D"],
                              filas, [7, 3, 1, 1, 1, 1, 1, 1, 1], y_ini=y) + 4

        notas = str(objetivos.get("notas", "") or "").strip()
        if notas:
            y = dibujar_subtitulo(y, "Lesiones, Alergias y Consideraciones", titulo)
            y = dibujar_caja_texto(y, titulo, notas)

        dibujar_pie_pagina()

    def pagina_composicion():
        titulo = "COMPOSICIÓN CORPORAL Y % DE GRASA"
        y = dibujar_fondo_y_cabecera(titulo) + 5

        medidas = [f for f in perfil.get("tabla_medidas", []) if str(f[1]).strip()]
        if medidas:
            y = dibujar_subtitulo(y, "Datos y Medidas Registradas", titulo)
            y = dibujar_tabla(titulo, ["Dato", "Valor"], medidas, [1, 1], y_ini=y) + 4

        resultados = [f for f in perfil.get("tabla_resultados", []) if str(f[1]).strip()]
        if resultados:
            y = dibujar_subtitulo(y, "Resultado del Análisis", titulo)
            y = dibujar_tabla(titulo, ["Indicador", "Resultado"], resultados, [1, 1], y_ini=y) + 4

        referencia = perfil.get("tabla_referencia", [])
        if referencia:
            y = dibujar_subtitulo(y, "Tabla de Referencia de Grasa Corporal", titulo)
            y = dibujar_tabla(titulo, ["Categoría", "Rango de % de grasa", "Situación del cliente"],
                              referencia, [2, 2, 2], y_ini=y) + 4

        energia = [f for f in perfil.get("tabla_energia", []) if str(f[1]).strip()]
        if energia:
            y = dibujar_subtitulo(y, "Objetivo Energético Diario", titulo)
            y = dibujar_tabla(titulo, ["Concepto", "Valor"], energia, [1, 1], y_ini=y) + 4

        pie = str(perfil.get("nota_metodo", "") or "").strip()
        if pie:
            y = dibujar_caja_texto(y, titulo, pie, fuente=8, alto_linea=4.0)

        dibujar_pie_pagina()

    def pagina_antiantojos():
        titulo = "TABLA ANTIANTOJOS"
        y = dibujar_fondo_y_cabecera(titulo) + 5

        intro = str(objetivos.get("intro_antojos", "") or "").strip()
        if intro:
            y = dibujar_caja_texto(y, titulo, intro)

        filas = [f for f in antiantojos if str(f[0]).strip() or str(f[1]).strip()]
        if filas:
            y = dibujar_subtitulo(y, "Cambia el antojo, no el objetivo", titulo)
            y = dibujar_tabla(titulo, ["Antojo", "Sustituto inteligente", "Porción", "Truco del coach"],
                              filas, [3, 5, 2, 5], y_ini=y)

        dibujar_pie_pagina()

    if inc_objetivos and (objetivos.get("resumen") or objetivos.get("metas") or objetivos.get("habitos")):
        pagina_objetivos()
    if inc_composicion and (perfil.get("tabla_medidas") or perfil.get("tabla_resultados")):
        pagina_composicion()
    if inc_entreno: procesar_modulo("PLAN DE ENTRENAMIENTO", datos_rutina, "entreno")
    if inc_nutri: procesar_modulo("PLAN DE ALIMENTACIÓN", datos_nutricion, "nutri")
    if inc_antiantojos and antiantojos:
        pagina_antiantojos()
    
    if inc_consejos and consejos.strip():
        y_offset = dibujar_fondo_y_cabecera("CONSEJOS Y RECOMENDACIONES") + 10
        caja_w = obtener_ancho_caja()
        texto_limpio = limpiar_texto(consejos)
        
        pdf.set_font("Arial", '', 10)
        alto_linea = 5.0
        
        lineas_reales = []
        for parrafo in texto_limpio.split('\n'):
            palabras = parrafo.split(' ')
            linea_actual = ""
            for palabra in palabras:
                prueba = palabra if linea_actual == "" else linea_actual + " " + palabra
                if pdf.get_string_width(prueba) > (caja_w - 12) and linea_actual != "":
                    lineas_reales.append(linea_actual)
                    linea_actual = palabra
                else:
                    linea_actual = prueba
            lineas_reales.append(linea_actual)
            
        paginas_de_texto = []
        lineas_pagina_actual = []
        y_simulado = y_offset + 5
        y_offset_siguiente = 55 
        
        for linea in lineas_reales:
            if y_simulado + alto_linea > (pdf.h - 30): 
                paginas_de_texto.append(lineas_pagina_actual)
                lineas_pagina_actual = [linea]
                y_simulado = y_offset_siguiente + 5 + alto_linea
            else:
                lineas_pagina_actual.append(linea)
                y_simulado += alto_linea
                
        if lineas_pagina_actual:
            paginas_de_texto.append(lineas_pagina_actual)
            
        for i, pagina in enumerate(paginas_de_texto):
            if i > 0:
                dibujar_pie_pagina()
                y_offset = dibujar_fondo_y_cabecera("CONSEJOS Y RECOMENDACIONES (Cont.)") + 10
                
            altura_caja = (len(pagina) * alto_linea) + 10
            
            if estilo == "Clean Minimal":
                pdf.set_draw_color(0, 0, 0)
                pdf.rect(15, y_offset, caja_w, altura_caja, 'D')
                pdf.set_text_color(50, 50, 50)
            else:
                pdf.set_fill_color(*c_caja)
                pdf.rect(15, y_offset, caja_w, altura_caja, 'F')
                pdf.set_text_color(220,220,220) if estilo in ESTILOS_OSCUROS else pdf.set_text_color(50,50,50)
                
            pdf.set_xy(20, y_offset + 5)
            for linea in pagina:
                pdf.cell(caja_w - 10, alto_linea, linea, ln=True)
                pdf.set_x(20) 
                
        dibujar_pie_pagina()

    if not (pdf.page_no() > 0):
        dibujar_fondo_y_cabecera("DOCUMENTO VACÍO")
        pdf.set_xy(15, 100)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(180, 10, "No has seleccionado ningún módulo para generar.", align='C')

    return pdf.output(dest='S')


# --- INTERFAZ DE USUARIO ---
preview_colors = {
    "Urban Power": {"bg": "#f8e71c", "text": "#000000", "accent": "#000000", "box": "#ffffff", "border": "none"},
    "Clean Minimal": {"bg": "#ffffff", "text": "#000000", "accent": "#000000", "box": "#ffffff", "border": "1px solid #000000"},
    "Dark Elite": {"bg": "#141414", "text": "#ffffff", "accent": "#c8102e", "box": "#282828", "border": "none"},
    "Ocean Fitness": {"bg": "#e0f0ff", "text": "#002040", "accent": "#0069b4", "box": "#f0f8ff", "border": "none"},
    "Cyber Neon": {"bg": "#0a0a0f", "text": "#e0ffe0", "accent": "#39ff14", "box": "#1a1a25", "border": "1px solid #39ff14"},
    "Eco Wellness": {"bg": "#f4f8f4", "text": "#2e4a2e", "accent": "#64a33c", "box": "#ffffff", "border": "1px solid #c0dcc0"},
    "Rose Gold": {"bg": "#fdf6f4", "text": "#4a2d2c", "accent": "#b76e79", "box": "#faeae7", "border": "1px solid #eed7d2"},
    "Violet Luxe": {"bg": "#181223", "text": "#eee9f8", "accent": "#8b5cf6", "box": "#2b213c", "border": "none"},
    "Sunset Energy": {"bg": "#fff7ed", "text": "#43200f", "accent": "#ea580c", "box": "#ffecd6", "border": "none"},
    "Steel Pro": {"bg": "#edf1f5", "text": "#18222d", "accent": "#2d4863", "box": "#ffffff", "border": "1px solid #cfd8e3"},
    "Gold Elite": {"bg": "#12110f", "text": "#f6f1e5", "accent": "#c6a03a", "box": "#27241e", "border": "1px solid #c6a03a"}
}


# ==========================================
# 🖼️ VISTA PREVIA REAL DE LAS PLANTILLAS
# ==========================================
DEMO_CONFIG = {"entrenador": "TU MARCA", "redes": "@tu_instagram",
               "fecha_inicio": "01/09/2026", "fecha_fin": "30/09/2026"}
DEMO_CLIENTE = {"nombre": "Cliente Demo", "edad": "30", "peso": "72",
                "altura": "173", "grasa": "18.5", "objetivo": "Pérdida de grasa"}

DEMO_RUTINA = {
    "Lunes": ("Pecho y tríceps", [
        ("Press de banca", "4", "8", "90", "60", "2"),
        ("Press inclinado con mancuernas", "3", "10", "75", "22", "2"),
        ("Fondos en paralelas", "3", "12", "60", "0", "1"),
        ("Extensión de tríceps en polea", "3", "15", "45", "25", "1"),
    ]),
    "Martes": ("Espalda y bíceps", [
        ("Dominadas", "4", "8", "90", "0", "1"),
        ("Remo con barra", "4", "10", "75", "50", "2"),
        ("Jalón al pecho", "3", "12", "60", "45", "2"),
        ("Curl de bíceps con barra", "3", "12", "45", "20", "1"),
    ]),
    "Miércoles": ("Pierna completa", [
        ("Sentadilla trasera", "4", "8", "120", "80", "2"),
        ("Peso muerto rumano", "4", "10", "90", "70", "2"),
        ("Prensa de piernas", "3", "12", "75", "120", "2"),
        ("Elevación de gemelos", "4", "15", "45", "40", "1"),
    ]),
    "Jueves": ("Hombro y core", [
        ("Press militar", "4", "10", "75", "30", "2"),
        ("Elevaciones laterales", "4", "15", "45", "8", "1"),
        ("Face pull", "3", "15", "45", "20", "1"),
        ("Plancha abdominal", "3", "45", "60", "0", ""),
    ]),
    "Viernes": ("Cardio y movilidad", [
        ("Cinta en zona 2", "1", "35", "0", "0", ""),
        ("Movilidad de cadera", "3", "10", "30", "0", ""),
    ]),
}

DEMO_ANTOJOS = [list(fila) for fila in CATALOGO_ANTIANTOJOS[:5]]

DEMO_OBJETIVOS = {
    "resumen": [
        ["Objetivo principal", "Pérdida de grasa"],
        ["Nivel de experiencia", "Intermedio"],
        ["Días de entrenamiento", "5 por semana"],
        ["Distribución sugerida", "Empuje - Tirón - Pierna + Torso - Pierna"],
        ["Calorías objetivo", "2180 kcal por día"],
        ["Macros objetivo", "Proteína 158 g | Grasas 61 g | Carbohidratos 224 g"],
        ["Agua diaria", "2.9 litros"],
    ],
    "estrategia": ("Doble progresión: llega al tope del rango de reps y recién ahí sube el peso. "
                   "Trabaja a RIR 1-2 y programa una semana de descarga cada 6-8 semanas."),
    "metas": [
        ["Semana 1-2", "Ajustar horarios de comida y sumar 8.000 pasos diarios", "Registro y pasos"],
        ["Semana 3-4", "Bajar 1.2 kg y subir 5 kg en press de banca", "Peso y cargas"],
        ["Semana 5-6", "Mantener adherencia del 90% al plan", "Check semanal"],
    ],
    "habitos": [
        ["Beber 2.5 - 3 litros de agua", "Diario"],
        ["Dormir 7 a 8 horas", "Diario"],
        ["Registrar todas las comidas", "Diario"],
        ["Pesarse en ayunas", "3 veces por semana"],
    ],
    "notas": "",
    "intro_antojos": ("Cuando aparezca el antojo: toma un vaso grande de agua y espera 10 minutos. "
                      "Si sigue ahí, usa el sustituto de esta tabla y respeta la porción indicada."),
}

# Cada seccion se genera por separado: asi la etiqueta siempre corresponde
# con lo que se ve, sin importar cuantas paginas ocupe en cada formato.
SECCIONES_MUESTRA = [
    ("objetivos", "Objetivos y metas"),
    ("entreno", "Plan de entrenamiento"),
    ("antojos", "Tabla antiantojos"),
]


def _construir_rutina_demo():
    rutina = {}
    for dia, (enfoque, ejercicios) in DEMO_RUTINA.items():
        rutina[dia] = {
            "enfoque": enfoque,
            "items": [{"nombre": n, "s": s, "r": r, "seg": g, "peso (kg)": p, "rir": rir, "nota": ""}
                      for n, s, r, g, p, rir in ejercicios],
        }
    return rutina


@st.cache_data(show_spinner=False)
def generar_pdf_muestra(estilo, formato, tipo_fondo, seccion="entreno"):
    """PDF de ejemplo con una sola seccion, para ver como luce la plantilla."""
    return bytes(generar_pdf_profesional(
        _construir_rutina_demo(), {}, "", DEMO_CONFIG, DEMO_CLIENTE, None,
        estilo, formato, tipo_fondo,
        seccion == "entreno", False, False,
        objetivos=DEMO_OBJETIVOS, perfil={}, antiantojos=DEMO_ANTOJOS,
        inc_objetivos=(seccion == "objetivos"),
        inc_composicion=False,
        inc_antiantojos=(seccion == "antojos"),
        calidad_fondo=4.5,
    ))


@st.cache_data(show_spinner=False)
def renderizar_paginas_pdf(pdf_bytes, indices, escala=1.6):
    """Convierte páginas del PDF en imágenes PNG. Devuelve None si falta pypdfium2."""
    try:
        import pypdfium2 as pdfium
    except Exception:
        return None
    try:
        documento = pdfium.PdfDocument(pdf_bytes)
        imagenes = []
        for indice in indices:
            if indice >= len(documento):
                continue
            imagen = documento[indice].render(scale=escala).to_pil()
            memoria = _io.BytesIO()
            imagen.save(memoria, format="PNG")
            imagenes.append(memoria.getvalue())
        documento.close()
        return imagenes or None
    except Exception:
        return None


def vista_previa_plantilla(estilo, formato, tipo_fondo, seccion="entreno", escala=1.6):
    """Devuelve el PNG de la primera pagina de esa seccion, o None si no se puede."""
    try:
        imagenes = renderizar_paginas_pdf(
            generar_pdf_muestra(estilo, formato, tipo_fondo, seccion), (0,), escala)
        return imagenes[0] if imagenes else None
    except Exception:
        return None


def construir_preview_html(estilo, formato):
    """Vista aproximada en HTML: respaldo cuando no se puede renderizar el PDF."""
    estilo_css = preview_colors[estilo]
    if estilo == "Clean Minimal":
        c_txt_dia = "#000000" if formato == "Horizontal (Tabla 7 Días)" else estilo_css["text"]
        bg_dia = "#ffffff" if formato == "Horizontal (Tabla 7 Días)" else estilo_css["accent"]
        border_dia = "1px solid #000"
    else:
        c_txt_dia = "#000000" if estilo in ESTILOS_ACENTO_CLARO else "#ffffff"
        bg_dia = estilo_css["accent"]
        border_dia = estilo_css["border"]

    if formato == "Vertical (Bloques)":
        return f"""
        <div style="background-color: {estilo_css['bg']}; padding: 15px; border-radius: 8px; border: 1px solid #ccc; font-family: Arial, sans-serif;">
            <div style="display: flex; height: 60px;">
                <div style="background-color: {bg_dia}; width: 30%; display: flex; flex-direction: column; align-items: center; justify-content: center; border: {border_dia}; border-right: none;">
                    <b style="color: {c_txt_dia}; font-size: 14px; margin-bottom: 2px;">LUNES</b>
                    <span style="color: {c_txt_dia}; font-size: 9px; opacity: 0.8;">PIERNA - CUÁDRICEPS</span>
                </div>
                <div style="background-color: {estilo_css['box']}; width: 70%; padding: 8px; border: {border_dia}; border-left: none;">
                    <div style="color: {estilo_css['text']}; font-size: 11px; font-weight: bold;">SENTADILLAS</div>
                    <div style="color: {estilo_css['text']}; font-size: 10px; font-style: italic; opacity: 0.8;">4 SETS | 12 REPS</div>
                </div>
            </div>
        </div>
        """
    return f"""
    <div style="background-color: {estilo_css['bg']}; padding: 10px; border-radius: 8px; border: 1px solid #ccc; font-family: Arial, sans-serif; overflow-x: auto;">
        <table style="width: 100%; border-collapse: collapse; text-align: center; font-size: 9px;">
            <tr style="background-color: {bg_dia}; color: {c_txt_dia}; font-weight: bold;">
                <td style="border: {border_dia}; padding: 5px;">LUNES<br><span style="font-size:7px; font-weight:normal;">PIERNA</span></td>
                <td style="border: {border_dia}; padding: 5px;">MARTES<br><span style="font-size:7px; font-weight:normal;">EMPUJE</span></td>
                <td style="border: {border_dia}; padding: 5px;">MIERCOLES<br><span style="font-size:7px; font-weight:normal;">DESCANSO</span></td>
            </tr>
            <tr style="background-color: {estilo_css['box']}; color: {estilo_css['text']};">
                <td style="border: {border_dia}; padding: 5px;"><b>SENTAD.</b><br>4S | 12R</td>
                <td style="border: {border_dia}; padding: 5px;"><b>PRESS</b><br>4S | 10R</td>
                <td style="border: {border_dia}; padding: 5px;"><b>CARDIO</b><br>Recup.</td>
            </tr>
        </table>
    </div>
    """


def seleccionar_plantilla(nombre):
    st.session_state["k_estilo"] = nombre


# --- PANEL LATERAL ---
with st.sidebar:
    if os.path.exists(ARCHIVO_LICENCIA_LOCAL):
        with open(ARCHIVO_LICENCIA_LOCAL, "r") as f:
            lic = json.load(f).get("licencia_activa", "")
        st.success(f"🎟️ **Licencia Activa:** `{lic}`")
    
    st.header("💾 Seguridad y Respaldos")
    col_g1, col_g2 = st.columns(2)
    if col_g1.button("💾 Guardar Local"):
        guardar_progreso_local()
        st.success("¡Guardado!")
    if col_g2.button("📂 Cargar Local"):
        cargar_progreso_local()
        
    archivo_subido = st.file_uploader("Subir Plantilla (JSON)", type=['json'])
    if archivo_subido is not None:
        if st.button("Aplicar Plantilla"):
            cargar_desde_archivo(archivo_subido)
            
    st.download_button(
        label="📥 Descargar como Plantilla",
        data=generar_json_descarga(),
        file_name="Plantilla_Progreso.json",
        mime="application/json"
    )

    st.divider()

    st.header("⚙️ Tu Marca (Logo)")
    logo_subido = st.file_uploader("Sube tu Logo (PNG/JPG)", type=['png', 'jpg', 'jpeg'])
    entrenador = st.text_input("Nombre del Entrenador", "TU NOMBRE O MARCA", key="k_entrenador")
    redes = st.text_input("Redes Sociales", "@tu_instagram", key="k_redes")
    fecha_in = st.text_input("Fecha Inicio", "01/02/2026", key="k_fecha_in")
    fecha_out = st.text_input("Fecha Fin", "28/02/2026", key="k_fecha_out")
    
    st.divider()

    st.header("🎨 Diseño del Documento")
    formato_elegido = st.radio("1. Estructura del PDF:", ["Vertical (Bloques)", "Horizontal (Tabla 7 Días)"])
    st.markdown("<br>", unsafe_allow_html=True)
    
    opciones_estilos = LISTA_PLANTILLAS
    estilo_elegido = st.selectbox("2. Tema de Color:", opciones_estilos, key="k_estilo")
    st.caption(DESCRIPCION_PLANTILLAS.get(estilo_elegido, ""))

    opciones_fondo = ["Sencillo (Color Sólido)", "Personalizado (Textura/Imagen)"]
    archivo_fondo = BG_IMAGES.get(estilo_elegido)
    tiene_textura = bool(archivo_fondo) and os.path.exists(os.path.join("img", archivo_fondo))

    if not tiene_textura:
        if estilo_elegido == "Clean Minimal":
            ayuda_fondo = "Clean Minimal solo usa fondo blanco."
        elif archivo_fondo:
            ayuda_fondo = f"Falta la imagen `{archivo_fondo}` en la carpeta `img`, así que se usa color sólido."
        else:
            ayuda_fondo = f"'{estilo_elegido}' es una plantilla de color sólido: no necesita imagen de fondo."
        tipo_fondo_elegido = st.radio("3. Tipo de Fondo:", ["Sencillo (Color Sólido)"], help=ayuda_fondo)
    else:
        tipo_fondo_elegido = st.radio("3. Tipo de Fondo:", opciones_fondo)
        if tipo_fondo_elegido == "Personalizado (Textura/Imagen)":
            st.success(f"✅ ¡Fondo `{archivo_fondo}` detectado!")

    st.write("**Vista Previa:**")
    _miniatura = vista_previa_plantilla(estilo_elegido, formato_elegido, tipo_fondo_elegido, "entreno", 1.1)
    if _miniatura:
        st.image(_miniatura, use_container_width=True)
        st.caption("Vista real del PDF. Compara todas en la pestaña 🎨 Plantillas.")
    else:
        st.caption("Vista aproximada. Instala `pypdfium2` para ver el PDF real.")
        st.markdown(construir_preview_html(estilo_elegido, formato_elegido), unsafe_allow_html=True)


# --- PERFIL DEL CLIENTE ---
st.subheader("👤 Perfil del Cliente")

VALORES_INICIALES = {
    "k_objetivo": "Pérdida de grasa",
    "k_nivel": "Intermedio",
    "k_dias_disp": 4,
}
for _clave, _valor in VALORES_INICIALES.items():
    if _clave not in st.session_state:
        st.session_state[_clave] = _valor

# Blindaje: si una plantilla vieja trae un valor que ya no existe, se resetea
if st.session_state.get("k_objetivo") not in OBJETIVOS_META:
    st.session_state["k_objetivo"] = "Pérdida de grasa"
if st.session_state.get("k_nivel") not in PROGRESION_POR_NIVEL:
    st.session_state["k_nivel"] = "Intermedio"
if st.session_state.get("c_actividad") not in FACTORES_ACTIVIDAD:
    st.session_state["c_actividad"] = "Moderado (3-5 días/semana)"

c1, c2, c3, c4, c5 = st.columns(5)
c_nombre = c1.text_input("Nombre", "", key="c_nombre")
c_edad = c2.text_input("Edad", "", key="c_edad")
c_sexo = c3.selectbox("Sexo", ["Hombre", "Mujer"], key="c_sexo")
c_peso = c4.text_input("Peso (kg)", "", key="c_peso")
c_altura = c5.text_input("Altura (cm)", "", key="c_altura")

c_actividad = st.selectbox(
    "🏃 Nivel de actividad diaria (fuera del entrenamiento)",
    list(FACTORES_ACTIVIDAD.keys()),
    key="c_actividad",
    help="Define el gasto energético base. Es lo que hace que el plan se adapte a la vida real del cliente."
)

st.divider()

dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

tab_obj, tab_comp, tab1, tab2, tab_anti, tab3, tab_plant = st.tabs([
    "🎯 Objetivos",
    "📊 % de Grasa",
    "🔥 Entrenamiento",
    "🍎 Nutrición",
    "🍫 Antiantojos",
    "💡 Consejos",
    "🎨 Plantillas"
])

# ==========================================================
# 🎨 GALERÍA Y VISTA PREVIA DE PLANTILLAS
# ==========================================================
with tab_plant:
    st.markdown(f"#### 🎨 Plantilla actual: {estilo_elegido}")
    st.caption(f"{DESCRIPCION_PLANTILLAS.get(estilo_elegido, '')}  ·  Formato: {formato_elegido}  ·  Fondo: {tipo_fondo_elegido}")

    paginas_muestra = [
        (etiqueta, vista_previa_plantilla(estilo_elegido, formato_elegido, tipo_fondo_elegido, seccion, 2.0))
        for seccion, etiqueta in SECCIONES_MUESTRA
    ]
    if any(imagen for _, imagen in paginas_muestra):
        columnas_muestra = st.columns(len(paginas_muestra))
        for columna, (etiqueta, imagen) in zip(columnas_muestra, paginas_muestra):
            if imagen:
                columna.image(imagen, caption=etiqueta, use_container_width=True)
        st.caption("Ejemplo con datos de muestra. Tu logo y los datos reales del cliente se aplican al generar el PDF.")
    else:
        st.info("Para ver el PDF real dentro de la app hace falta la librería `pypdfium2`. "
                "Mientras tanto se muestra la vista aproximada.")
        st.markdown(construir_preview_html(estilo_elegido, formato_elegido), unsafe_allow_html=True)

    st.divider()

    st.markdown("##### 🖼️ Galería: compara las 11 plantillas")
    if not st.session_state.get("ver_galeria_plantillas"):
        if st.button("Ver todas las plantillas", use_container_width=True):
            st.session_state["ver_galeria_plantillas"] = True
            st.rerun()
        st.caption("Se generan 11 vistas previas reales; la primera vez tarda unos segundos.")
    else:
        columnas_galeria = st.columns(4)
        for indice_plantilla, nombre_plantilla in enumerate(LISTA_PLANTILLAS):
            with columnas_galeria[indice_plantilla % 4]:
                miniatura = vista_previa_plantilla(nombre_plantilla, formato_elegido,
                                                   "Sencillo (Color Sólido)", "entreno", 0.9)
                if miniatura:
                    st.image(miniatura, use_container_width=True)
                else:
                    st.markdown(construir_preview_html(nombre_plantilla, formato_elegido), unsafe_allow_html=True)
                es_actual = (nombre_plantilla == estilo_elegido)
                st.button(("✅ " if es_actual else "") + nombre_plantilla,
                          key=f"btn_plantilla_{indice_plantilla}",
                          use_container_width=True,
                          disabled=es_actual,
                          on_click=seleccionar_plantilla,
                          args=(nombre_plantilla,))
                st.caption(DESCRIPCION_PLANTILLAS.get(nombre_plantilla, ""))

# ==========================================================
# 📊 COMPOSICIÓN CORPORAL — se calcula primero porque alimenta
#    al resto de las pestañas (objetivos, calorías, macros)
# ==========================================================
with tab_comp:
    st.markdown("#### 📏 Datos necesarios para obtener el % de grasa")
    st.caption("Mide en ayunas, con cinta flexible y sin apretar. Con cuello + cintura (y cadera en mujeres) ya se obtiene el porcentaje.")

    metodo_grasa = st.radio(
        "Método de cálculo",
        [
            "Automático (usa el mejor dato disponible)",
            "Circunferencias (US Navy)",
            "Pliegues cutáneos (Jackson-Pollock 3)",
            "Estimación por IMC (Deurenberg)",
            "Manual (bioimpedancia / DEXA)",
        ],
        key="k_metodo_grasa"
    )

    st.markdown("**Circunferencias (cm)**")
    m1, m2, m3 = st.columns(3)
    m_cuello = m1.text_input("Cuello", "", key="m_cuello",
                             help="Justo debajo de la nuez, con la cinta levemente inclinada hacia abajo.")
    m_cintura = m2.text_input("Cintura", "", key="m_cintura",
                              help="Hombres: a la altura del ombligo. Mujeres: en la parte más estrecha del torso.")
    m_cadera = m3.text_input("Cadera", "", key="m_cadera",
                             help="Zona más ancha de los glúteos. Obligatorio en mujeres para el método US Navy.")

    with st.expander("➕ Pliegues cutáneos (opcional, resultado más preciso)"):
        st.caption("Hombre: pecho · abdomen · muslo   |   Mujer: tríceps · suprailíaco · muslo. Medir en mm, lado derecho, promedio de 2 tomas.")
        pl1, pl2, pl3 = st.columns(3)
        etiquetas = ("Pecho (mm)", "Abdomen (mm)", "Muslo (mm)") if c_sexo == "Hombre" else ("Tríceps (mm)", "Suprailíaco (mm)", "Muslo (mm)")
        m_p1 = pl1.text_input(etiquetas[0], "", key="m_p1")
        m_p2 = pl2.text_input(etiquetas[1], "", key="m_p2")
        m_p3 = pl3.text_input(etiquetas[2], "", key="m_p3")

    m_grasa_manual = st.text_input("% de grasa medido con báscula o DEXA (opcional)", "", key="m_grasa_manual")

    perfil = calcular_perfil(
        sexo=c_sexo,
        edad=_num(c_edad),
        peso=_num(c_peso),
        altura=_num(c_altura),
        cuello=_num(m_cuello),
        cintura=_num(m_cintura),
        cadera=_num(m_cadera),
        pliegues=(_num(m_p1), _num(m_p2), _num(m_p3)),
        actividad=c_actividad,
        objetivo=st.session_state.get("k_objetivo", "Pérdida de grasa"),
        metodo=metodo_grasa,
        grasa_manual=_num(m_grasa_manual) or None,
    )

    st.divider()

    if perfil["grasa"]:
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("% de Grasa", f"{perfil['grasa']} %", perfil["categoria"], delta_color="off")
        r2.metric("Masa Grasa", f"{perfil['masa_grasa']} kg")
        r3.metric("Masa Magra", f"{perfil['masa_magra']} kg")
        r4.metric("IMC", f"{perfil['imc']}" if perfil["imc"] else "—", perfil["imc_cat"], delta_color="off")
        st.caption(f"Método aplicado: **{perfil['metodo_usado']}**")
    else:
        st.warning("Completa peso, altura, edad y al menos **cuello + cintura** (y cadera si es mujer) para calcular el % de grasa.")

    if perfil["tdee"]:
        e1, e2, e3, e4 = st.columns(4)
        e1.metric("Metabolismo Basal", f"{perfil['tmb']} kcal")
        e2.metric("Gasto Total (TDEE)", f"{perfil['tdee']} kcal")
        e3.metric("Objetivo Calórico", f"{perfil['kcal']} kcal")
        e4.metric("Agua / día", f"{perfil['agua']} L" if perfil["agua"] else "—")
        if perfil["macros"]:
            mc = perfil["macros"]
            st.success(
                f"**Macros sugeridos:** 🥩 Proteína {mc['prot']} g  ·  🥑 Grasas {mc['grasa']} g  ·  🍚 Carbohidratos {mc['carb']} g"
                f"  —  total ≈ {mc['prot']*4 + mc['grasa']*9 + mc['carb']*4} kcal"
            )

    # --- Tabla de referencia del % de grasa ---
    st.markdown(f"##### 📋 Tabla de referencia de % de grasa — {c_sexo}")
    filas_ref_html = ""
    tabla_referencia_pdf = []
    for nombre_cat, minimo, maximo in RANGOS_GRASA[c_sexo]:
        rango_txt = f"{minimo} % - {maximo} %" if maximo < 100 else f"{minimo} % o más"
        es_actual = bool(perfil["grasa"] and minimo <= perfil["grasa"] <= maximo)
        estado = "NIVEL ACTUAL DEL CLIENTE" if es_actual else ""
        tabla_referencia_pdf.append([nombre_cat, rango_txt, estado])
        fondo = "background-color:#2e7d32;color:#ffffff;font-weight:bold;" if es_actual else ""
        filas_ref_html += (
            f"<tr style='{fondo}'>"
            f"<td style='padding:6px 10px;border:1px solid #999;'>{nombre_cat}</td>"
            f"<td style='padding:6px 10px;border:1px solid #999;text-align:center;'>{rango_txt}</td>"
            f"<td style='padding:6px 10px;border:1px solid #999;text-align:center;'>{'◀ AQUÍ ESTÁ' if es_actual else ''}</td>"
            f"</tr>"
        )
    st.markdown(
        "<table style='width:100%;border-collapse:collapse;font-size:14px;'>"
        "<tr style='background-color:#444;color:#fff;'>"
        "<th style='padding:8px 10px;border:1px solid #999;text-align:left;'>Categoría</th>"
        "<th style='padding:8px 10px;border:1px solid #999;'>Rango de % de grasa</th>"
        "<th style='padding:8px 10px;border:1px solid #999;'>Situación</th>"
        "</tr>" + filas_ref_html + "</table>",
        unsafe_allow_html=True
    )

    with st.expander("🔬 Comparar los tres métodos y ver indicadores de salud"):
        cmp1, cmp2, cmp3 = st.columns(3)
        cmp1.metric("US Navy", f"{perfil['g_navy']} %" if perfil["g_navy"] else "—")
        cmp2.metric("Pliegues (J-P 3)", f"{perfil['g_pliegues']} %" if perfil["g_pliegues"] else "—")
        cmp3.metric("Por IMC", f"{perfil['g_imc']} %" if perfil["g_imc"] else "—")
        s1, s2 = st.columns(2)
        s1.metric("Índice cintura/cadera", f"{perfil['icc']}" if perfil["icc"] else "—")
        s2.metric("Cintura / altura", f"{perfil['rce']}" if perfil["rce"] else "—", perfil["rce_alerta"], delta_color="off")
        st.caption("Cintura/altura por debajo de 0.52 es el indicador de riesgo cardiometabólico más simple y confiable.")

    # --- Estructuras que viajan al PDF ---
    def _fmt(valor, sufijo="", decimales=None):
        if valor is None or valor == "" or valor == 0:
            return ""
        if decimales is not None:
            return f"{round(float(valor), decimales)}{sufijo}"
        return f"{valor}{sufijo}"

    perfil["tabla_medidas"] = [
        ["Sexo", c_sexo],
        ["Edad", _fmt(_num(c_edad), " años")],
        ["Peso actual", _fmt(_num(c_peso), " kg")],
        ["Altura", _fmt(_num(c_altura), " cm")],
        ["Cuello", _fmt(_num(m_cuello), " cm")],
        ["Cintura", _fmt(_num(m_cintura), " cm")],
        ["Cadera", _fmt(_num(m_cadera), " cm")],
        ["Pliegues (3 sitios)", f"{_num(m_p1)} / {_num(m_p2)} / {_num(m_p3)} mm" if (_num(m_p1) + _num(m_p2) + _num(m_p3)) > 0 else ""],
        ["Nivel de actividad", c_actividad],
        ["Fecha de valoración", fecha_in],
    ]

    perfil["tabla_resultados"] = [
        ["Porcentaje de grasa", _fmt(perfil["grasa"], " %")],
        ["Método utilizado", perfil["metodo_usado"] if perfil["grasa"] else ""],
        ["Clasificación", perfil["categoria"] if perfil["grasa"] else ""],
        ["Masa grasa", _fmt(perfil["masa_grasa"], " kg")],
        ["Masa magra (músculo, hueso, agua)", _fmt(perfil["masa_magra"], " kg")],
        ["Índice de masa corporal (IMC)", f"{perfil['imc']} - {perfil['imc_cat']}" if perfil["imc"] else ""],
        ["Índice cintura / cadera", _fmt(perfil["icc"])],
        ["Cintura / altura", f"{perfil['rce']} - {perfil['rce_alerta']}" if perfil["rce"] else ""],
        ["Comparativa US Navy", _fmt(perfil["g_navy"], " %")],
        ["Comparativa pliegues", _fmt(perfil["g_pliegues"], " %")],
        ["Comparativa por IMC", _fmt(perfil["g_imc"], " %")],
    ]

    perfil["tabla_referencia"] = tabla_referencia_pdf if perfil["grasa"] or True else []

    macros_p = perfil["macros"] or {}
    perfil["tabla_energia"] = [
        ["Metabolismo basal (TMB)", f"{perfil['tmb']} kcal - {perfil['formula_tmb']}" if perfil["tmb"] else ""],
        ["Gasto energético total (TDEE)", f"{perfil['tdee']} kcal (factor {perfil['factor']})" if perfil["tdee"] else ""],
        ["Objetivo calórico diario", f"{perfil['kcal']} kcal" if perfil["kcal"] else ""],
        ["Proteína", f"{macros_p.get('prot')} g ({macros_p.get('prot', 0) * 4} kcal)" if macros_p else ""],
        ["Grasas", f"{macros_p.get('grasa')} g ({macros_p.get('grasa', 0) * 9} kcal)" if macros_p else ""],
        ["Carbohidratos", f"{macros_p.get('carb')} g ({macros_p.get('carb', 0) * 4} kcal)" if macros_p else ""],
        ["Agua recomendada", _fmt(perfil["agua"], " litros por día")],
        ["Ritmo esperado de cambio", f"{perfil['ritmo_kg']} kg por semana" if perfil["ritmo_kg"] else ""],
    ]

    perfil["nota_metodo"] = (
        "Cómo se obtuvo este porcentaje: el método US Navy usa circunferencias (cuello, cintura y cadera) junto con la altura. "
        "El método de pliegues aplica la fórmula de Jackson-Pollock de 3 sitios y la ecuación de Siri. "
        "La estimación por IMC (Deurenberg) es un respaldo cuando no hay medidas. "
        "El gasto energético se calcula con Katch-McArdle cuando se conoce la masa magra y con Mifflin-St Jeor en caso contrario. "
        "Repetir la medición cada 15 días, siempre en las mismas condiciones."
    )

# ==========================================================
# 🎯 OBJETIVOS
# ==========================================================
with tab_obj:
    st.markdown("#### 🎯 Hacia dónde vamos")

    o1, o2, o3 = st.columns(3)
    objetivo_principal = o1.selectbox("Objetivo principal", list(OBJETIVOS_META.keys()), key="k_objetivo")
    nivel_exp = o2.selectbox("Nivel de experiencia", list(PROGRESION_POR_NIVEL.keys()), key="k_nivel")
    dias_disp = o3.number_input("Días de entreno por semana", 1, 7, key="k_dias_disp")

    o4, o5, o6 = st.columns(3)
    peso_meta_txt = o4.text_input("Peso meta (kg)", "", key="k_peso_meta")
    grasa_meta_txt = o5.text_input("% de grasa meta", "", key="k_grasa_meta")
    plazo_txt = o6.text_input("Plazo o fecha objetivo", "", key="k_plazo")

    om1, om2 = st.columns(2)
    motivacion = om1.text_area("💬 Motivación del cliente (su porqué)", key="k_motivacion", height=90)
    limitaciones = om2.text_area("⚠️ Lesiones, alergias o limitaciones a respetar", key="k_limitaciones", height=90)

    # --- Motor adaptativo ---
    split_sugerido = sugerir_split(dias_disp, nivel_exp, objetivo_principal)
    peso_actual = _num(c_peso)
    peso_meta = _num(peso_meta_txt)
    grasa_meta = _num(grasa_meta_txt)
    peso_por_grasa = peso_para_grasa_objetivo(perfil["masa_magra"], grasa_meta)
    peso_objetivo_final = peso_meta or peso_por_grasa
    semanas = semanas_estimadas(peso_actual, peso_objetivo_final, perfil["ritmo_kg"])

    st.markdown("##### 🤖 Recomendación adaptada del sistema")
    a1, a2, a3 = st.columns(3)
    a1.metric("Calorías objetivo", f"{perfil['kcal']} kcal" if perfil["kcal"] else "—")
    a2.metric("Ritmo esperado", f"{perfil['ritmo_kg']} kg/sem" if perfil["ritmo_kg"] else "—")
    a3.metric("Tiempo estimado", f"{semanas} semanas" if semanas else "—")
    st.info(f"**Distribución sugerida ({dias_disp} días):** {split_sugerido}")
    st.info(f"**Progresión ({nivel_exp}):** {PROGRESION_POR_NIVEL[nivel_exp]}")
    if peso_por_grasa and grasa_meta:
        st.caption(f"Para llegar al {grasa_meta} % de grasa conservando la masa magra actual, el peso corporal debería rondar los **{peso_por_grasa} kg**.")
    if peso_objetivo_final and peso_actual and not semanas:
        st.caption("El objetivo elegido y el peso meta van en direcciones opuestas: revisa el objetivo principal o el peso meta.")

    st.divider()

    # --- Metas por periodo ---
    st.markdown("##### 📌 Metas por periodo")
    n_metas = st.number_input("Cantidad de metas", 0, 20, 4, key="k_n_metas")
    metas_lista = []
    for i in range(int(n_metas)):
        col_a, col_b, col_c = st.columns([1.2, 3, 2])
        per = col_a.text_input("Periodo", f"Semana {i+1}", key=f"meta_per_{i}")
        des = col_b.text_input("Meta / acción concreta", key=f"meta_des_{i}")
        ind = col_c.text_input("Cómo se mide", key=f"meta_ind_{i}")
        metas_lista.append([per, des, ind])

    st.divider()

    # --- Hábitos ---
    st.markdown("##### ✅ Hábitos clave (checklist semanal impreso en el PDF)")
    HABITOS_BASE = [
        ("Beber 2.5 - 3 litros de agua", "Diario"),
        ("Dormir 7 a 8 horas", "Diario"),
        ("Caminar 8.000 - 10.000 pasos", "Diario"),
        ("Registrar todas las comidas", "Diario"),
        ("Pesarse en ayunas", "3 veces por semana"),
        ("Tomar medidas y fotos de control", "Cada 15 días"),
    ]
    n_habitos = st.number_input("Cantidad de hábitos", 0, 20, 6, key="k_n_habitos")
    habitos_lista = []
    for i in range(int(n_habitos)):
        base_h = HABITOS_BASE[i] if i < len(HABITOS_BASE) else ("", "Diario")
        col_h1, col_h2 = st.columns([3, 1])
        hab = col_h1.text_input("Hábito", base_h[0], key=f"hab_n_{i}")
        frec = col_h2.text_input("Frecuencia", base_h[1], key=f"hab_f_{i}")
        habitos_lista.append([hab, frec])

# ==========================================================
# 🔥 ENTRENAMIENTO
# ==========================================================
with tab1:
    st.caption("Hasta 20 ejercicios por día. Los campos RIR y Nota son opcionales y se imprimen bajo el ejercicio.")
    datos_rutina = {}
    for dia in dias_semana:
        with st.expander(f"Rutina del {dia}", expanded=False):
            enfoque_dia = st.text_input("💪 Músculo o Enfoque del Día (Ej: Pierna - Cuádriceps)", key=f"enf_{dia}")
            n_ej = st.number_input(f"Cantidad ejercicios {dia} (Máx 20)", 1, 20, 4, key=f"ne_{dia}")
            lista_ej = []
            for i in range(int(n_ej)):
                col1, col2, col3, col4, col5, col6, col7 = st.columns([3, 0.9, 0.9, 0.9, 1, 0.9, 2.6])
                nombre = col1.text_input("Ejercicio", key=f"n_{dia}_{i}")
                s = col2.text_input("Sets", "4", key=f"s_{dia}_{i}")
                r = col3.text_input("Reps", "12", key=f"r_{dia}_{i}")
                seg = col4.text_input("Seg", "60", key=f"g_{dia}_{i}")
                p = col5.text_input("Peso (kg)", "0", key=f"p_{dia}_{i}")
                rir = col6.text_input("RIR", "", key=f"rir_{dia}_{i}", help="Reps en reserva: cuántas repeticiones podría hacer todavía.")
                nota = col7.text_input("Nota / técnica", key=f"nt_{dia}_{i}")
                lista_ej.append({"nombre": nombre, "s": s, "r": r, "seg": seg,
                                 "peso (kg)": p, "rir": rir, "nota": nota})

            datos_rutina[dia] = {"enfoque": enfoque_dia, "items": lista_ej}

# ==========================================================
# 🍎 NUTRICIÓN
# ==========================================================
with tab2:
    st.caption("Hasta 20 comidas por día. Si cargas las kcal de cada comida, el sistema compara el total con el objetivo calculado.")
    datos_nutricion = {}
    for dia in dias_semana:
        with st.expander(f"Comidas del {dia}", expanded=False):
            n_comidas = st.number_input(f"Cantidad comidas {dia} (Máx 20)", 1, 20, 4, key=f"nc_{dia}")
            lista_comidas = []
            total_kcal_dia = 0
            for i in range(int(n_comidas)):
                col1, col2, col3 = st.columns([1.2, 4, 1])
                tipo = col1.text_input("Comida (Ej: Desayuno...)", key=f"t_{dia}_{i}")
                detalle = col2.text_input("Alimentos (Ej: 2 huevos...)", key=f"d_{dia}_{i}")
                kcal_c = col3.text_input("Kcal", "", key=f"kc_{dia}_{i}")
                total_kcal_dia += _num(kcal_c)
                detalle_final = detalle
                if _num(kcal_c) > 0:
                    detalle_final = f"{detalle} ({int(_num(kcal_c))} kcal)" if detalle else f"{int(_num(kcal_c))} kcal"
                lista_comidas.append({"nombre": tipo, "detalle": detalle_final})

            if total_kcal_dia > 0:
                if perfil["kcal"]:
                    diferencia = int(total_kcal_dia - perfil["kcal"])
                    st.metric(f"Total {dia}", f"{int(total_kcal_dia)} kcal",
                              f"{diferencia:+d} kcal respecto al objetivo", delta_color="off")
                else:
                    st.metric(f"Total {dia}", f"{int(total_kcal_dia)} kcal")

            datos_nutricion[dia] = {"enfoque": "", "items": lista_comidas}

# ==========================================================
# 🍫 ANTIANTOJOS
# ==========================================================
with tab_anti:
    st.info("Tabla de sustituciones inteligentes: el cliente no elimina el antojo, lo cambia por una versión que sí entra en el plan.")
    intro_antojos = st.text_area(
        "Indicación general para el cliente",
        "Cuando aparezca el antojo: toma un vaso grande de agua y espera 10 minutos. Si sigue ahí, usa el sustituto de esta tabla y respeta la porción indicada. Un antojo controlado no rompe el plan; uno improvisado sí.",
        key="k_intro_antojos", height=90
    )
    n_antojos = st.number_input("Cantidad de filas de la tabla", 1, 30, 8, key="k_n_antojos")
    antiantojos_lista = []
    for i in range(int(n_antojos)):
        base_a = CATALOGO_ANTIANTOJOS[i] if i < len(CATALOGO_ANTIANTOJOS) else ("", "", "", "")
        col_a, col_b, col_c, col_d = st.columns([2, 3.2, 1.2, 3.2])
        antojo = col_a.text_input("Antojo", base_a[0], key=f"anti_a_{i}")
        sustituto = col_b.text_input("Sustituto inteligente", base_a[1], key=f"anti_s_{i}")
        porcion = col_c.text_input("Porción", base_a[2], key=f"anti_p_{i}")
        truco = col_d.text_input("Truco del coach", base_a[3], key=f"anti_t_{i}")
        antiantojos_lista.append([antojo, sustituto, porcion, truco])

# ==========================================================
# 💡 CONSEJOS
# ==========================================================
with tab3:
    st.info("Escribe aquí todas las indicaciones extra: cantidad de agua, descanso, uso de suplementos, etc.")
    if perfil["kcal"]:
        st.caption(
            f"Referencia rápida para este cliente: {perfil['kcal']} kcal/día · "
            f"{(perfil['macros'] or {}).get('prot', '—')} g de proteína · "
            f"{perfil['agua']} L de agua · objetivo: {st.session_state.get('k_objetivo')}."
        )
    texto_consejos = st.text_area("Consejos y Recomendaciones:", height=250, key="k_consejos")

st.divider()

# ==========================================================
# 📦 ARMADO DE LOS DATOS QUE VIAJAN AL PDF
# ==========================================================
resumen_objetivos = [
    ["Objetivo principal", objetivo_principal],
    ["Nivel de experiencia", nivel_exp],
    ["Días de entrenamiento", f"{int(dias_disp)} por semana"],
    ["Distribución sugerida", split_sugerido],
    ["Peso actual", f"{peso_actual} kg" if peso_actual else ""],
    ["Peso meta", f"{peso_meta} kg" if peso_meta else ""],
    ["Grasa actual", f"{perfil['grasa']} % ({perfil['categoria']})" if perfil["grasa"] else ""],
    ["Grasa meta", f"{grasa_meta} %" if grasa_meta else ""],
    ["Peso estimado al llegar a la grasa meta", f"{peso_por_grasa} kg" if peso_por_grasa else ""],
    ["Ritmo de cambio previsto", f"{perfil['ritmo_kg']} kg por semana" if perfil["ritmo_kg"] else ""],
    ["Tiempo estimado", f"{semanas} semanas aproximadamente" if semanas else ""],
    ["Plazo acordado", plazo_txt],
    ["Calorías objetivo", f"{perfil['kcal']} kcal por dia" if perfil["kcal"] else ""],
    ["Macros objetivo", (f"Proteína {perfil['macros']['prot']} g | Grasas {perfil['macros']['grasa']} g | "
                         f"Carbohidratos {perfil['macros']['carb']} g") if perfil["macros"] else ""],
    ["Agua diaria", f"{perfil['agua']} litros" if perfil["agua"] else ""],
    ["Motivación del cliente", motivacion],
]

estrategia_txt = f"Distribución semanal: {split_sugerido}. {PROGRESION_POR_NIVEL[nivel_exp]}"
if perfil["kcal"]:
    estrategia_txt += (f" Objetivo energético: {perfil['kcal']} kcal diarias sobre un gasto estimado de {perfil['tdee']} kcal, "
                       f"priorizando {perfil['macros']['prot']} g de proteína para proteger la masa magra.")
if semanas:
    estrategia_txt += f" Con este ritmo, la meta de peso se alcanza en unas {semanas} semanas de trabajo sostenido."

objetivos_pdf = {
    "resumen": resumen_objetivos,
    "estrategia": estrategia_txt,
    "metas": metas_lista,
    "habitos": habitos_lista,
    "notas": limitaciones,
    "intro_antojos": intro_antojos,
}

# --- OPCIONES DE GENERACIÓN ---
st.subheader("⚙️ Opciones de Generación")
col_opt1, col_opt2, col_opt3, col_opt4, col_opt5, col_opt6 = st.columns(6)
inc_objetivos = col_opt1.checkbox("🎯 Objetivos", value=True, key="k_inc_objetivos")
inc_composicion = col_opt2.checkbox("📊 % Grasa", value=True, key="k_inc_composicion")
inc_entreno = col_opt3.checkbox("💪 Entrenamiento", value=True, key="k_inc_entreno")
inc_nutri = col_opt4.checkbox("🥗 Nutrición", value=True, key="k_inc_nutri")
inc_antiantojos = col_opt5.checkbox("🍫 Antiantojos", value=True, key="k_inc_antiantojos")
inc_consejos = col_opt6.checkbox("💡 Consejos", value=True, key="k_inc_consejos")

st.markdown("<br>", unsafe_allow_html=True)

# --- BOTÓN DE GENERACIÓN PDF ---
if st.button("🚀 GENERAR PDF PROFESIONAL", use_container_width=True):
    modulos = [inc_entreno, inc_nutri, inc_consejos, inc_objetivos, inc_composicion, inc_antiantojos]
    if not any(modulos):
        st.error("⚠️ Debes seleccionar al menos un módulo.")
    else:
        configuracion = {"entrenador": entrenador, "redes": redes, "fecha_inicio": fecha_in, "fecha_fin": fecha_out}
        datos_cliente = {
            "nombre": c_nombre, "edad": c_edad, "peso": c_peso, "altura": c_altura,
            "grasa": perfil["grasa"] if perfil["grasa"] else "",
            "objetivo": objetivo_principal,
        }

        pdf_bytes = generar_pdf_profesional(
            datos_rutina, datos_nutricion, texto_consejos, configuracion,
            datos_cliente, logo_subido, estilo_elegido, formato_elegido, tipo_fondo_elegido,
            inc_entreno, inc_nutri, inc_consejos,
            objetivos=objetivos_pdf,
            perfil=perfil,
            antiantojos=antiantojos_lista,
            inc_objetivos=inc_objetivos,
            inc_composicion=inc_composicion,
            inc_antiantojos=inc_antiantojos,
        )

        nombre_archivo = f"Plan_{c_nombre.replace(' ', '_')}.pdf" if c_nombre else "Plan_Entrenamiento.pdf"

        st.success("¡Plan generado a tu medida!")
        st.download_button(
            label=f"📥 Descargar {nombre_archivo}",
            data=bytes(pdf_bytes),
            file_name=nombre_archivo,
            mime="application/pdf"
        )
