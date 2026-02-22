import streamlit as st
from fpdf import FPDF
from PIL import Image
import tempfile
import os
import math
import json

# --- FUNCIÓN PARA EVITAR CRASHEOS CON EMOJIS ---
def limpiar_texto(texto):
    if not texto: return ""
    return str(texto).encode('latin-1', 'ignore').decode('latin-1')

# --- ESTIMADOR DE ALTURA DINÁMICA ---
def estimar_altura_texto(texto, ancho_celda=170, tamaño_fuente=8):
    if not texto: return 0
    caracteres_por_linea = int(ancho_celda / (tamaño_fuente * 0.25)) 
    lineas = 0
    for parrafo in texto.split('\n'):
        lineas += max(1, math.ceil(len(parrafo) / caracteres_por_linea))
    altura_linea = tamaño_fuente * 0.5 
    return lineas * altura_linea

# --- FUNCIONES DE GUARDADO Y RESPALDO ---
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

# --- MOTOR PDF OPTIMIZADO ---
def generar_pdf_profesional(datos_rutina, datos_nutricion, consejos, config, cliente, logo_file, estilo, formato, inc_entreno, inc_nutri, inc_consejos):
    orientacion = 'L' if formato == "Horizontal (Tabla 7 Días)" else 'P'
    pdf = FPDF(orientation=orientacion)
    pdf.set_auto_page_break(auto=False) 
    
    # Configuración de Colores
    if estilo == "Dark Elite":
        c_bg, c_texto, c_acento, c_caja = (25, 25, 25), (255, 255, 255), (220, 20, 60), (40, 40, 40)
    elif estilo == "Clean Minimal":
        c_bg, c_texto, c_acento, c_caja = (255, 255, 255), (0, 0, 0), (255, 255, 255), (255, 255, 255)
    elif estilo == "Ocean Fitness":
        c_bg, c_texto, c_acento, c_caja = (255, 255, 255), (0, 0, 0), (0, 105, 180), (230, 240, 250)
    elif estilo == "Cyber Neon":
        c_bg, c_texto, c_acento, c_caja = (15, 15, 15), (255, 255, 255), (57, 255, 20), (35, 35, 35)
    elif estilo == "Eco Wellness": 
        c_bg, c_texto, c_acento, c_caja = (255, 255, 255), (50, 50, 50), (130, 200, 80), (245, 250, 245)
    else: # Urban Power
        c_bg, c_texto, c_acento, c_caja = (255, 255, 255), (0, 0, 0), (244, 196, 48), (240, 240, 240)

    def obtener_ancho_caja():
        return pdf.w - 30

    def dibujar_fondo_y_cabecera(titulo_pagina):
        pdf.add_page()
        if estilo in ["Dark Elite", "Cyber Neon"]:
            pdf.set_fill_color(*c_bg)
            pdf.rect(0, 0, pdf.w, pdf.h, 'F')
            
        if logo_file is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                tmp_file.write(logo_file.getvalue())
                logo_path = tmp_file.name
            pdf.image(logo_path, x=15, y=10, w=25)
            os.remove(logo_path)

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
        else:
            pdf.set_fill_color(230,230,230) if estilo == "Urban Power" else pdf.set_fill_color(*c_caja)
            pdf.rect(15, y_cliente, caja_w, 8, 'F')
            
        pdf.set_xy(15, y_cliente + 2)
        pdf.set_font("Arial", 'B', 8)
        pdf.set_text_color(200,200,200) if estilo in ["Dark Elite", "Cyber Neon"] else pdf.set_text_color(50,50,50)
        
        info_c = f"USUARIO: {limpiar_texto(cliente['nombre']).upper()}  |  EDAD: {limpiar_texto(cliente['edad'])}  |  PESO: {limpiar_texto(cliente['peso'])}  |  ALTURA: {limpiar_texto(cliente['altura'])}"
        pdf.cell(caja_w, 4, info_c, align='C')
        return pdf.get_y() + 8

    def dibujar_pie_pagina():
        pdf.set_y(pdf.h - 15)
        if estilo in ["Urban Power", "Cyber Neon"]:
            pdf.set_fill_color(0, 0, 0) if estilo == "Urban Power" else pdf.set_fill_color(*c_caja)
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
        # ESTRUCTURA HORIZONTAL (TABLA 7 DÍAS)
        # =========================================================
        if formato == "Horizontal (Tabla 7 Días)":
            caja_w = obtener_ancho_caja()
            col_w = caja_w / 7 
            
            pdf.set_fill_color(*c_acento)
            if estilo in ["Urban Power", "Cyber Neon", "Clean Minimal"]:
                pdf.set_text_color(0, 0, 0)
            else:
                pdf.set_text_color(255, 255, 255)
                
            # Borde visible si es Minimal
            if estilo == "Clean Minimal": pdf.set_draw_color(0, 0, 0)
            else: pdf.set_draw_color(200, 200, 200)

            pdf.set_font("Arial", 'B', 9)
            pdf.set_xy(15, y_offset)
            for dia in dias:
                pdf.cell(col_w, 8, dia.upper(), border=1, fill=True, align='C')
            pdf.ln(8)
            y_offset = pdf.get_y()
            
            max_items = 0
            for dia in dias:
                valid_items = [it for it in datos_dict.get(dia, []) if it['nombre']]
                if len(valid_items) > max_items: max_items = len(valid_items)
            
            pdf.set_text_color(*c_texto)

            for i in range(max_items):
                max_h = 15 
                for dia in dias:
                    valid_items = [it for it in datos_dict.get(dia, []) if it['nombre']]
                    if i < len(valid_items):
                        item = valid_items[i]
                        nom_h = estimar_altura_texto(limpiar_texto(item['nombre']), col_w, 8)
                        if tipo_modulo == "entreno":
                            det = f"{item['s']}S | {item['r']}R | {item['seg']}s"
                            det_h = estimar_altura_texto(det, col_w, 7.5)
                        else:
                            det = limpiar_texto(item['detalle'])
                            det_h = estimar_altura_texto(det, col_w, 7.5)
                        
                        h_total = nom_h + det_h + 8 
                        if h_total > max_h: max_h = h_total
                
                if y_offset + max_h > pdf.h - 22:
                    dibujar_pie_pagina()
                    y_offset = dibujar_fondo_y_cabecera(titulo_pagina) + 5
                    
                    pdf.set_fill_color(*c_acento)
                    if estilo in ["Urban Power", "Cyber Neon", "Clean Minimal"]: pdf.set_text_color(0, 0, 0)
                    else: pdf.set_text_color(255, 255, 255)
                    pdf.set_font("Arial", 'B', 9)
                    pdf.set_xy(15, y_offset)
                    for dia in dias:
                        pdf.cell(col_w, 8, dia.upper(), border=1, fill=True, align='C')
                    pdf.ln(8)
                    y_offset = pdf.get_y()
                    pdf.set_text_color(*c_texto)

                fill_row = True if i % 2 == 0 else False
                pdf.set_fill_color(*c_caja) if fill_row else pdf.set_fill_color(*c_bg)
                
                for col_idx, dia in enumerate(dias):
                    x_pos = 15 + (col_idx * col_w)
                    pdf.rect(x_pos, y_offset, col_w, max_h, 'DF' if fill_row else 'D')
                    
                    valid_items = [it for it in datos_dict.get(dia, []) if it['nombre']]
                    if i < len(valid_items):
                        item = valid_items[i]
                        
                        pdf.set_xy(x_pos + 1, y_offset + 2)
                        pdf.set_font("Arial", 'B', 7.5)
                        pdf.multi_cell(col_w - 2, 3.5, limpiar_texto(item['nombre']).upper(), align='C')
                        
                        y_det = pdf.get_y()
                        pdf.set_xy(x_pos + 1, y_det + 1)
                        pdf.set_font("Arial", '', 7)
                        
                        if tipo_modulo == "entreno":
                            det = f"{limpiar_texto(item['s'])}S | {limpiar_texto(item['r'])}R | {limpiar_texto(item['seg'])}s"
                            if item.get('peso (kg)') and str(item.get('peso (kg)')) != "0":
                                det += f"\n{limpiar_texto(item['peso (kg)'])} KG"
                            pdf.multi_cell(col_w - 2, 3.5, det, align='C')
                        else:
                            pdf.multi_cell(col_w - 2, 3.5, limpiar_texto(item['detalle']), align='C')
                            
                y_offset += max_h

        # =========================================================
        # ESTRUCTURA VERTICAL (BLOQUES)
        # =========================================================
        else:
            for dia in dias:
                items = datos_dict.get(dia, [])
                if not any(item['nombre'] for item in items): continue 
                
                alturas_col_izq, alturas_col_der = [], []
                
                for idx, item in enumerate(items):
                    if not item['nombre']: continue
                    h_item = 5 + (4 if tipo_modulo == "entreno" else estimar_altura_texto(item['detalle'], ancho_celda=60))
                    if idx < 3: alturas_col_izq.append(h_item)
                    else: alturas_col_der.append(h_item)
                
                altura_caja = max(20, sum(alturas_col_izq) + (len(alturas_col_izq) * 4), sum(alturas_col_der) + (len(alturas_col_der) * 4)) + 5 
                
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

                pdf.set_xy(15, y_offset + (altura_caja/2) - 2.5)
                pdf.set_font("Arial", 'B', 11)
                
                if estilo in ["Urban Power", "Cyber Neon", "Clean Minimal"]: pdf.set_text_color(0,0,0)
                else: pdf.set_text_color(255,255,255) 
                    
                pdf.cell(40, 5, dia.upper(), align='C')

                pdf.set_text_color(220,220,220) if estilo in ["Dark Elite", "Cyber Neon"] else pdf.set_text_color(50,50,50)
                
                y_col_izq = y_offset + 3
                y_col_der = y_offset + 3
                
                for idx, item in enumerate(items):
                    if not item['nombre']: continue
                    columna = idx // 3 
                    x_pos = 63 + (columna * 65) 
                    y_pos = y_col_izq if columna == 0 else y_col_der
                    
                    nom_limpio = limpiar_texto(item['nombre']).upper()
                    pdf.set_xy(x_pos, y_pos)
                    pdf.set_font("Arial", 'B', 8)
                    pdf.cell(60, 4, nom_limpio[:45])
                    y_pos += 4 
                    
                    if tipo_modulo == "entreno":
                        pdf.set_xy(x_pos, y_pos)
                        pdf.set_font("Arial", 'I', 7.5)
                        texto_detalle = f"{limpiar_texto(item['s'])} SETS | {limpiar_texto(item['r'])} REPS | {limpiar_texto(item['seg'])} SEG"
                        if item.get('peso (kg)') and str(item.get('peso (kg)')) != "0":
                            texto_detalle += f" | {limpiar_texto(item['peso (kg)'])} KG"
                        pdf.cell(60, 4, texto_detalle)
                        y_pos += 8 
                    else: 
                        pdf.set_xy(x_pos, y_pos)
                        pdf.set_font("Arial", '', 7.5)
                        det_limpio = limpiar_texto(item['detalle'])
                        pdf.multi_cell(62, 3.5, det_limpio) 
                        altura_real = pdf.get_y() - y_pos
                        y_pos += altura_real + 4
                    
                    if columna == 0: y_col_izq = y_pos
                    else: y_col_der = y_pos

                y_offset += altura_caja + 4 
            
        dibujar_pie_pagina()

    if inc_entreno: procesar_modulo("PLAN DE ENTRENAMIENTO", datos_rutina, "entreno")
    if inc_nutri: procesar_modulo("PLAN DE ALIMENTACIÓN", datos_nutricion, "nutri")
    
    if inc_consejos and consejos.strip():
        y_offset = dibujar_fondo_y_cabecera("CONSEJOS Y RECOMENDACIONES") + 10
        caja_w = obtener_ancho_caja()
        
        if estilo == "Clean Minimal":
            pdf.set_draw_color(0, 0, 0)
            pdf.rect(15, y_offset, caja_w, pdf.h - y_offset - 25, 'D')
        else:
            pdf.set_fill_color(*c_caja)
            pdf.rect(15, y_offset, caja_w, pdf.h - y_offset - 25, 'F')
            
        pdf.set_xy(20, y_offset + 5)
        pdf.set_font("Arial", '', 10)
        pdf.set_text_color(220,220,220) if estilo in ["Dark Elite", "Cyber Neon"] else pdf.set_text_color(50,50,50)
        pdf.multi_cell(caja_w - 10, 6, limpiar_texto(consejos))
        dibujar_pie_pagina()

    if not inc_entreno and not inc_nutri and not inc_consejos:
        dibujar_fondo_y_cabecera("DOCUMENTO VACÍO")
        pdf.set_xy(15, 100)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(180, 10, "No has seleccionado ningún módulo para generar.", align='C')

    return pdf.output(dest='S')

# --- INTERFAZ DE USUARIO ---
st.set_page_config(page_title="Coach System Pro", layout="wide")

preview_colors = {
    "Urban Power": {"bg": "#ffffff", "text": "#000000", "accent": "#f4c430", "box": "#f0f0f0", "border": "none"},
    "Clean Minimal": {"bg": "#ffffff", "text": "#000000", "accent": "#ffffff", "box": "#ffffff", "border": "1px solid #000000"},
    "Dark Elite": {"bg": "#191919", "text": "#ffffff", "accent": "#dc143c", "box": "#282828", "border": "none"},
    "Ocean Fitness": {"bg": "#ffffff", "text": "#000000", "accent": "#0069b4", "box": "#e6f0fa", "border": "none"},
    "Cyber Neon": {"bg": "#0f0f0f", "text": "#ffffff", "accent": "#39ff14", "box": "#232323", "border": "none"},
    "Eco Wellness": {"bg": "#ffffff", "text": "#333333", "accent": "#82c850", "box": "#f2f9f2", "border": "1px solid #e0e0e0"}
}

# --- PANEL LATERAL ---
with st.sidebar:
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
    # --- AQUI SEPARAMOS FORMATO Y ESTILO ---
    formato_elegido = st.radio("Estructura del PDF:", ["Vertical (Bloques)", "Horizontal (Tabla 7 Días)"])
    st.markdown("<br>", unsafe_allow_html=True)
    
    opciones_estilos = ["Urban Power", "Clean Minimal", "Dark Elite", "Ocean Fitness", "Cyber Neon", "Eco Wellness"]
    estilo_elegido = st.selectbox("Tema de Color:", opciones_estilos, key="k_estilo")

    st.write("**Vista Previa del Diseño:**")
    estilo_css = preview_colors[estilo_elegido]
    
    if formato_elegido == "Vertical (Bloques)":
        color_texto_dia = "#000000" if estilo_elegido in ["Urban Power", "Cyber Neon", "Clean Minimal"] else "#ffffff"
        html_preview = f"""
        <div style="background-color: {estilo_css['bg']}; padding: 15px; border-radius: 8px; border: 1px solid #ccc; font-family: Arial, sans-serif;">
            <div style="display: flex; height: 60px;">
                <div style="background-color: {estilo_css['accent']}; width: 30%; display: flex; align-items: center; justify-content: center; border: {estilo_css['border']}; border-right: none;">
                    <b style="color: {color_texto_dia}; font-size: 14px;">LUNES</b>
                </div>
                <div style="background-color: {estilo_css['box']}; width: 70%; padding: 8px; border: {estilo_css['border']}; border-left: none;">
                    <div style="color: {estilo_css['text']}; font-size: 11px; font-weight: bold;">PRESS DE BANCA</div>
                    <div style="color: {estilo_css['text']}; font-size: 10px; font-style: italic; opacity: 0.8;">4 SETS | 12 REPS | 60 SEG | 20 KG</div>
                </div>
            </div>
        </div>
        """
    else:
        color_texto_dia = "#000000" if estilo_elegido in ["Urban Power", "Cyber Neon", "Clean Minimal"] else "#ffffff"
        html_preview = f"""
        <div style="background-color: {estilo_css['bg']}; padding: 10px; border-radius: 8px; border: 1px solid #ccc; font-family: Arial, sans-serif; overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; text-align: center; font-size: 9px;">
                <tr style="background-color: {estilo_css['accent']}; color: {color_texto_dia}; font-weight: bold;">
                    <td style="border: {estilo_css['border']} if '{estilo_elegido}'=='Clean Minimal' else 1px solid #ccc; padding: 5px;">LUNES</td>
                    <td style="border: {estilo_css['border']} if '{estilo_elegido}'=='Clean Minimal' else 1px solid #ccc; padding: 5px;">MARTES</td>
                    <td style="border: {estilo_css['border']} if '{estilo_elegido}'=='Clean Minimal' else 1px solid #ccc; padding: 5px;">MIERCOLES</td>
                </tr>
                <tr style="background-color: {estilo_css['box']}; color: {estilo_css['text']};">
                    <td style="border: {estilo_css['border']} if '{estilo_elegido}'=='Clean Minimal' else 1px solid #ccc; padding: 5px;"><b>PRESS BANCA</b><br>4S | 12R | 60s</td>
                    <td style="border: {estilo_css['border']} if '{estilo_elegido}'=='Clean Minimal' else 1px solid #ccc; padding: 5px;"><b>SENTADILLA</b><br>4S | 10R | 90s</td>
                    <td style="border: {estilo_css['border']} if '{estilo_elegido}'=='Clean Minimal' else 1px solid #ccc; padding: 5px;"><b>DESCANSO</b><br>Recuperación</td>
                </tr>
            </table>
        </div>
        """
    st.markdown(html_preview, unsafe_allow_html=True)

st.title("🏋️‍♂️ Sistema de Planes Personalizados")

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
            n_ej = st.number_input(f"Cantidad ejercicios {dia} (Máx 6)", 1, 6, 4, key=f"ne_{dia}")
            lista_ej = []
            for i in range(n_ej):
                col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
                nombre = col1.text_input("Ejercicio", key=f"n_{dia}_{i}")
                s = col2.text_input("Sets", "4", key=f"s_{dia}_{i}")
                r = col3.text_input("Reps", "12", key=f"r_{dia}_{i}")
                seg = col4.text_input("Seg", "60", key=f"g_{dia}_{i}")
                p = col5.text_input("Peso (kg)", "0", key=f"p_{dia}_{i}")
                lista_ej.append({"nombre": nombre, "s": s, "r": r, "seg": seg, "peso (kg)": p})
            datos_rutina[dia] = lista_ej

with tab2:
    datos_nutricion = {}
    for dia in dias_semana:
        with st.expander(f"Comidas del {dia}", expanded=False):
            n_comidas = st.number_input(f"Cantidad comidas {dia} (Máx 6)", 1, 6, 4, key=f"nc_{dia}")
            lista_comidas = []
            for i in range(n_comidas):
                col1, col2 = st.columns([1, 3])
                tipo = col1.text_input("Comida (Ej: Desayuno...)", key=f"t_{dia}_{i}")
                detalle = col2.text_input("Alimentos (Ej: 2 huevos...)", key=f"d_{dia}_{i}")
                lista_comidas.append({"nombre": tipo, "detalle": detalle})
            datos_nutricion[dia] = lista_comidas

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
            datos_cliente, logo_subido, estilo_elegido, formato_elegido,
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