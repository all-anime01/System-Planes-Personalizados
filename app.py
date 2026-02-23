import streamlit as st
from fpdf import FPDF
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

def optimizar_fondo_hd(ruta_imagen, pdf_w, pdf_h):
    try:
        target_w = int(pdf_w * 11.81)
        target_h = int(pdf_h * 11.81)
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
    "Clean Minimal": None 
}

def generar_pdf_profesional(datos_rutina, datos_nutricion, consejos, config, cliente, logo_file, estilo, formato, tipo_fondo, inc_entreno, inc_nutri, inc_consejos):
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
                fondo_hd = optimizar_fondo_hd(ruta_imagen, pdf.w, pdf.h)
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
            pdf.set_text_color(220,220,220) if estilo in ["Dark Elite", "Cyber Neon"] else pdf.set_text_color(80,90,80) if estilo == "Eco Wellness" else pdf.set_text_color(50,50,50)
            
        pdf.set_xy(15, y_cliente + 2)
        pdf.set_font("Arial", 'B', 8)
        info_c = f"USUARIO: {limpiar_texto(cliente['nombre']).upper()}  |  EDAD: {limpiar_texto(cliente['edad'])}  |  PESO: {limpiar_texto(cliente['peso'])}  |  ALTURA: {limpiar_texto(cliente['altura'])}"
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
                pdf.set_fill_color(*c_acento)
                if estilo in ["Urban Power", "Cyber Neon", "Clean Minimal"]: pdf.set_text_color(0, 0, 0)
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
                            det = f"{limpiar_texto(item['s'])}S | {limpiar_texto(item['r'])}R | {limpiar_texto(item['seg'])}s"
                            if item.get('peso (kg)') and str(item.get('peso (kg)')) != "0":
                                det += f"\n{limpiar_texto(item['peso (kg)'])} KG"
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
                        texto_detalle = f"{limpiar_texto(item['s'])} SETS | {limpiar_texto(item['r'])} REPS | {limpiar_texto(item['seg'])} SEG"
                        if item.get('peso (kg)') and str(item.get('peso (kg)')) != "0":
                            texto_detalle += f" | {limpiar_texto(item['peso (kg)'])} KG"
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
                
                if estilo in ["Urban Power", "Cyber Neon", "Clean Minimal"]: pdf.set_text_color(0,0,0)
                else: pdf.set_text_color(255,255,255) 
                    
                pdf.cell(40, 5, dia.upper(), align='C')

                if enfoque and tipo_modulo == "entreno":
                    pdf.set_font("Arial", 'B', 7)
                    pdf.set_xy(16, pdf.get_y() + 4)
                    pdf.multi_cell(38, 3.5, limpiar_texto(enfoque).upper()[:40], align='C')

                pdf.set_text_color(220,220,220) if estilo in ["Dark Elite", "Cyber Neon"] else pdf.set_text_color(50,50,50)
                
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
                        texto_detalle = f"{limpiar_texto(item['s'])} SETS | {limpiar_texto(item['r'])} REPS | {limpiar_texto(item['seg'])} SEG"
                        if item.get('peso (kg)') and str(item.get('peso (kg)')) != "0":
                            texto_detalle += f" | {limpiar_texto(item['peso (kg)'])} KG"
                        
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

    if inc_entreno: procesar_modulo("PLAN DE ENTRENAMIENTO", datos_rutina, "entreno")
    if inc_nutri: procesar_modulo("PLAN DE ALIMENTACIÓN", datos_nutricion, "nutri")
    
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
                pdf.set_text_color(220,220,220) if estilo in ["Dark Elite", "Cyber Neon"] else pdf.set_text_color(50,50,50)
                
            pdf.set_xy(20, y_offset + 5)
            for linea in pagina:
                pdf.cell(caja_w - 10, alto_linea, linea, ln=True)
                pdf.set_x(20) 
                
        dibujar_pie_pagina()

    if not inc_entreno and not inc_nutri and not inc_consejos:
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
    "Eco Wellness": {"bg": "#f4f8f4", "text": "#2e4a2e", "accent": "#64a33c", "box": "#ffffff", "border": "1px solid #c0dcc0"}
}

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
    
    opciones_estilos = ["Urban Power", "Clean Minimal", "Dark Elite", "Ocean Fitness", "Cyber Neon", "Eco Wellness"]
    estilo_elegido = st.selectbox("2. Tema de Color:", opciones_estilos, key="k_estilo")

    opciones_fondo = ["Sencillo (Color Sólido)", "Personalizado (Textura/Imagen)"]
    if estilo_elegido == "Clean Minimal":
        tipo_fondo_elegido = st.radio("3. Tipo de Fondo:", ["Sencillo (Color Sólido)"], help="Clean Minimal solo usa fondo blanco.")
    else:
        tipo_fondo_elegido = st.radio("3. Tipo de Fondo:", opciones_fondo)
        
        if tipo_fondo_elegido == "Personalizado (Textura/Imagen)":
            archivo_esperado = BG_IMAGES.get(estilo_elegido)
            if archivo_esperado:
                ruta_completa = os.path.join("img", archivo_esperado)
                if not os.path.exists(ruta_completa):
                    st.warning(f"⚠️ ¡Falta la imagen de fondo!\n\nGuarda la imagen: 👉 `{archivo_esperado}` dentro de la carpeta `img`")
                else:
                    st.success(f"✅ ¡Fondo `{archivo_esperado}` detectado!")

    st.write("**Vista Previa (Aproximada):**")
    estilo_css = preview_colors[estilo_elegido]
    
    if estilo_elegido == "Clean Minimal":
         c_txt_dia = "#000000" if formato_elegido == "Horizontal (Tabla 7 Días)" else estilo_css["text"]
         bg_dia = "#ffffff" if formato_elegido == "Horizontal (Tabla 7 Días)" else estilo_css["accent"]
         border_dia = "1px solid #000"
    else:
         c_txt_dia = "#ffffff" if estilo_elegido not in ["Urban Power", "Cyber Neon"] else "#000000"
         bg_dia = estilo_css["accent"]
         border_dia = estilo_css["border"]

    if formato_elegido == "Vertical (Bloques)":
        html_preview = f"""
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
    else:
        html_preview = f"""
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
    st.markdown(html_preview, unsafe_allow_html=True)


# --- DATOS DEL USUARIO ---
st.subheader("👤 Datos del Usuario")
c1, c2, c3, c4 = st.columns(4)
c_nombre = c1.text_input("Usuario", "", key="c_nombre")
c_edad = c2.text_input("Edad", "", key="c_edad")
c_peso = c3.text_input("Peso", "", key="c_peso")
c_altura = c4.text_input("Altura", "", key="c_altura")

st.divider()

dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

tab1, tab2, tab3 = st.tabs(["🔥 Entrenamiento", "🍎 Nutrición", "💡 Consejos"])

with tab1:
    datos_rutina = {}
    for dia in dias_semana:
        with st.expander(f"Rutina del {dia}", expanded=False):
            enfoque_dia = st.text_input("💪 Músculo o Enfoque del Día (Ej: Pierna - Cuádriceps)", key=f"enf_{dia}")
            n_ej = st.number_input(f"Cantidad ejercicios {dia} (Máx 9)", 1, 9, 4, key=f"ne_{dia}")
            lista_ej = []
            for i in range(n_ej):
                col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
                nombre = col1.text_input("Ejercicio", key=f"n_{dia}_{i}")
                s = col2.text_input("Sets", "4", key=f"s_{dia}_{i}")
                r = col3.text_input("Reps", "12", key=f"r_{dia}_{i}")
                seg = col4.text_input("Seg", "60", key=f"g_{dia}_{i}")
                p = col5.text_input("Peso (kg)", "0", key=f"p_{dia}_{i}")
                lista_ej.append({"nombre": nombre, "s": s, "r": r, "seg": seg, "peso (kg)": p})
            
            datos_rutina[dia] = {"enfoque": enfoque_dia, "items": lista_ej}

with tab2:
    datos_nutricion = {}
    for dia in dias_semana:
        with st.expander(f"Comidas del {dia}", expanded=False):
            n_comidas = st.number_input(f"Cantidad comidas {dia} (Máx 9)", 1, 9, 4, key=f"nc_{dia}")
            lista_comidas = []
            for i in range(n_comidas):
                col1, col2 = st.columns([1, 3])
                tipo = col1.text_input("Comida (Ej: Desayuno...)", key=f"t_{dia}_{i}")
                detalle = col2.text_input("Alimentos (Ej: 2 huevos...)", key=f"d_{dia}_{i}")
                lista_comidas.append({"nombre": tipo, "detalle": detalle})
            
            datos_nutricion[dia] = {"enfoque": "", "items": lista_comidas}

with tab3:
    st.info("Escribe aquí todas las indicaciones extra: cantidad de agua, descanso, uso de suplementos, etc.")
    texto_consejos = st.text_area("Consejos y Recomendaciones:", height=250, key="k_consejos")

st.divider()

# --- OPCIONES DE GENERACIÓN ---
st.subheader("⚙️ Opciones de Generación")
col_opt1, col_opt2, col_opt3 = st.columns(3)
inc_entreno = col_opt1.checkbox("💪 Entrenamiento", value=True, key="k_inc_entreno")
inc_nutri = col_opt2.checkbox("🥗 Nutrición", value=True, key="k_inc_nutri")
inc_consejos = col_opt3.checkbox("💡 Consejos", value=True, key="k_inc_consejos")

st.markdown("<br>", unsafe_allow_html=True) 

# --- BOTÓN DE GENERACIÓN PDF ---
if st.button("🚀 GENERAR PDF PROFESIONAL", use_container_width=True):
    if not (inc_entreno or inc_nutri or inc_consejos):
        st.error("⚠️ Debes seleccionar al menos un módulo.")
    else:
        configuracion = {"entrenador": entrenador, "redes": redes, "fecha_inicio": fecha_in, "fecha_fin": fecha_out}
        datos_cliente = {"nombre": c_nombre, "edad": c_edad, "peso": c_peso, "altura": c_altura}
        
        pdf_bytes = generar_pdf_profesional(
            datos_rutina, datos_nutricion, texto_consejos, configuracion, 
            datos_cliente, logo_subido, estilo_elegido, formato_elegido, tipo_fondo_elegido,
            inc_entreno, inc_nutri, inc_consejos
        )
        
        nombre_archivo = f"Plan_{c_nombre.replace(' ', '_')}.pdf" if c_nombre else "Plan_Entrenamiento.pdf"
        
        st.success("¡Plan generado a tu medida!")
        st.download_button(
            label=f"📥 Descargar {nombre_archivo}",
            data=bytes(pdf_bytes),
            file_name=nombre_archivo,
            mime="application/pdf"
        )