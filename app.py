import streamlit as st
from fpdf import FPDF
from PIL import Image
import tempfile
import os

# --- MOTOR PDF OPTIMIZADO ---
def generar_pdf_profesional(datos_rutina, datos_nutricion, config, cliente, logo_file, estilo):
    pdf = FPDF()
    # Bloqueamos el salto automático para tener control total y evitar páginas extra
    pdf.set_auto_page_break(auto=False) 
    
    # Configuración de Colores según Estilo (5 Estilos Disponibles)
    if estilo == "Dark Elite":
        c_bg, c_texto, c_acento, c_caja = (25, 25, 25), (255, 255, 255), (220, 20, 60), (40, 40, 40)
    elif estilo == "Clean Minimal":
        c_bg, c_texto, c_acento, c_caja = (255, 255, 255), (0, 0, 0), (255, 255, 255), (255, 255, 255)
    elif estilo == "Ocean Fitness":
        c_bg, c_texto, c_acento, c_caja = (255, 255, 255), (0, 0, 0), (0, 105, 180), (230, 240, 250)
    elif estilo == "Cyber Neon":
        c_bg, c_texto, c_acento, c_caja = (15, 15, 15), (255, 255, 255), (57, 255, 20), (35, 35, 35)
    else: # Urban Power
        c_bg, c_texto, c_acento, c_caja = (255, 255, 255), (0, 0, 0), (244, 196, 48), (240, 240, 240)

    # Función interna para dibujar cada página
    def dibujar_pagina(titulo_pagina, datos_dict, tipo_modulo):
        pdf.add_page()
        
        # Fondo oscuro
        if estilo in ["Dark Elite", "Cyber Neon"]:
            pdf.set_fill_color(*c_bg)
            pdf.rect(0, 0, 210, 297, 'F')
            
        # Logo Funcional
        if logo_file is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                tmp_file.write(logo_file.getvalue())
                logo_path = tmp_file.name
            pdf.image(logo_path, x=15, y=10, w=25)
            os.remove(logo_path)

        # Encabezado (Ajustado para ganar espacio)
        pdf.set_text_color(*c_texto)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 10, config['entrenador'].upper(), ln=True, align='C')
        pdf.set_font("Arial", 'B', 22)
        pdf.cell(0, 8, titulo_pagina, ln=True, align='C')
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 6, f"VIGENCIA: {config['fecha_inicio']} A {config['fecha_fin']}", ln=True, align='C')
        pdf.ln(3)

        # Caja de Cliente (Un poco más arriba para dar espacio al Domingo)
        y_cliente = pdf.get_y()
        if estilo == "Clean Minimal":
            pdf.set_draw_color(0, 0, 0)
            pdf.rect(15, y_cliente, 180, 8, 'D')
        else:
            pdf.set_fill_color(230,230,230) if estilo == "Urban Power" else pdf.set_fill_color(*c_caja)
            pdf.rect(15, y_cliente, 180, 8, 'F')
            
        pdf.set_xy(15, y_cliente + 2)
        pdf.set_font("Arial", 'B', 8)
        pdf.set_text_color(200,200,200) if estilo in ["Dark Elite", "Cyber Neon"] else pdf.set_text_color(50,50,50)
        info_c = f"CLIENTE: {cliente['nombre'].upper()}  |  EDAD: {cliente['edad']}  |  PESO: {cliente['peso']}  |  ALTURA: {cliente['altura']}"
        pdf.cell(180, 4, info_c, align='C')

        # --- GENERACIÓN DE DÍAS Y CAJAS (Matemática Ajustada) ---
        y_offset = 48 # Comenzamos más arriba (antes 55)
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        
        for dia in dias:
            items = datos_dict.get(dia, [])
            if not items: continue 
            
            # Altura ajustada a 27 para que los 7 días entren sin tapar el pie de página
            if estilo == "Clean Minimal":
                pdf.set_draw_color(0, 0, 0)
                pdf.rect(15, y_offset, 40, 27, 'D') 
                pdf.rect(60, y_offset, 135, 27, 'D') 
            else:
                pdf.set_fill_color(*c_acento)
                pdf.rect(15, y_offset, 40, 27, 'F')
                pdf.set_fill_color(*c_caja)
                pdf.rect(60, y_offset, 135, 27, 'F')

            # Título del Día
            pdf.set_xy(15, y_offset + 10.5)
            pdf.set_font("Arial", 'B', 11)
            pdf.set_text_color(0,0,0) if estilo in ["Urban Power", "Cyber Neon"] else pdf.set_text_color(*c_texto)
            pdf.cell(40, 5, dia.upper(), align='C')

            # Imprimir Contenido (Inteligencia de 2 Columnas)
            pdf.set_text_color(220,220,220) if estilo in ["Dark Elite", "Cyber Neon"] else pdf.set_text_color(50,50,50)
            
            for idx, item in enumerate(items):
                if not item['nombre']: continue
                
                columna = idx // 3 
                fila = idx % 3
                
                # Coordenadas ajustadas para el nuevo tamaño de caja
                x_pos = 63 + (columna * 65) 
                y_pos = y_offset + 2.5 + (fila * 8)
                
                if tipo_modulo == "entreno":
                    # Nombre del Ejercicio
                    pdf.set_xy(x_pos, y_pos)
                    pdf.set_font("Arial", 'B', 8)
                    pdf.cell(60, 4, str(item['nombre']).upper()[:35]) 
                    
                    # Series, Reps, Segs, Peso
                    pdf.set_xy(x_pos, y_pos + 3.5)
                    pdf.set_font("Arial", 'I', 7.5)
                    texto_detalle = f"{item['s']} SETS | {item['r']} REPS | {item['seg']} SEG"
                    if item.get('peso (kg)') and str(item.get('peso (kg)')) != "0":
                        texto_detalle += f" | {item['peso (kg)']} KG"
                    pdf.cell(60, 4, texto_detalle)
                
                else: # Nutrición
                    # Comida
                    pdf.set_xy(x_pos, y_pos)
                    pdf.set_font("Arial", 'B', 8)
                    pdf.cell(60, 4, str(item['nombre']).upper()[:35])
                    # Detalle
                    pdf.set_xy(x_pos, y_pos + 3.5)
                    pdf.set_font("Arial", '', 7.5)
                    pdf.cell(60, 4, str(item['detalle'])[:40]) 

            y_offset += 30 # Salto de 30 unidades (antes 32) para ganar espacio

        # Pie de página (Redes Sociales libres de solapamiento)
        pdf.set_y(270)
        if estilo in ["Urban Power", "Cyber Neon"]:
            pdf.set_fill_color(0, 0, 0) if estilo == "Urban Power" else pdf.set_fill_color(*c_caja)
            pdf.rect(60, 268, 90, 10, 'F')
            pdf.set_text_color(255, 255, 255)
        else:
            pdf.set_text_color(*c_texto)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 6, config['redes'], align='C')

    # Ejecutar dibujo de las dos páginas
    dibujar_pagina("PLAN DE ENTRENAMIENTO", datos_rutina, "entreno")
    dibujar_pagina("PLAN DE ALIMENTACIÓN", datos_nutricion, "nutri")

    return pdf.output(dest='S')

# --- INTERFAZ DE USUARIO ---
st.set_page_config(page_title="Coach System Pro", layout="wide")

# --- DICCIONARIO PARA LA VISTA PREVIA VISUAL ---
preview_styles = {
    "Urban Power": {"bg": "#ffffff", "text": "#000000", "accent": "#f4c430", "box": "#f0f0f0", "border": "none"},
    "Clean Minimal": {"bg": "#ffffff", "text": "#000000", "accent": "#ffffff", "box": "#ffffff", "border": "1px solid #000000"},
    "Dark Elite": {"bg": "#191919", "text": "#ffffff", "accent": "#dc143c", "box": "#282828", "border": "none"},
    "Ocean Fitness": {"bg": "#ffffff", "text": "#000000", "accent": "#0069b4", "box": "#e6f0fa", "border": "none"},
    "Cyber Neon": {"bg": "#0f0f0f", "text": "#ffffff", "accent": "#39ff14", "box": "#232323", "border": "none"}
}

# PANEL LATERAL: Configuración y Logo
with st.sidebar:
    st.header("⚙️ Tu Marca (Logo)")
    logo_subido = st.file_uploader("Sube tu Logo (PNG/JPG)", type=['png', 'jpg', 'jpeg'])
    entrenador = st.text_input("Nombre del Entrenador", "TU NOMBRE O MARCA")
    redes = st.text_input("Redes Sociales", "@tu_instagram")
    fecha_in = st.text_input("Fecha Inicio", "01/10")
    fecha_out = st.text_input("Fecha Fin", "31/10")
    
    st.divider()
    st.header("🎨 Selección de Plantilla")
    opciones_estilos = ["Urban Power", "Clean Minimal", "Dark Elite", "Ocean Fitness", "Cyber Neon"]
    estilo_elegido = st.radio("Elige tu diseño:", opciones_estilos)
    
    # --- RENDERIZADO DE VISTA PREVIA ---
    st.write("**Vista Previa del Diseño:**")
    estilo_css = preview_styles[estilo_elegido]
    color_texto_dia = "#000" if estilo_elegido in ["Urban Power", "Cyber Neon"] else estilo_css["text"]
    
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
    st.markdown(html_preview, unsafe_allow_html=True)

st.title("🏋️‍♂️ Sistema de Planes Personalizados")

# Pestaña de Cliente
st.subheader("👤 Datos del Cliente")
c1, c2, c3, c4 = st.columns(4)
c_nombre = c1.text_input("Nombre del Cliente", "")
c_edad = c2.text_input("Edad", "")
c_peso = c3.text_input("Peso", "")
c_altura = c4.text_input("Altura", "")

st.divider()

dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

# PESTAÑAS PARA SEPARAR EL TRABAJO
tab1, tab2 = st.tabs(["🔥 Módulo de Entrenamiento", "🍎 Módulo de Nutrición (Por Días)"])

# --- TAB 1: ENTRENAMIENTO ---
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

# --- TAB 2: NUTRICIÓN POR DÍAS ---
with tab2:
    datos_nutricion = {}
    for dia in dias_semana:
        with st.expander(f"Comidas del {dia}", expanded=False):
            n_comidas = st.number_input(f"Cantidad comidas {dia} (Máx 6)", 1, 6, 4, key=f"nc_{dia}")
            lista_comidas = []
            for i in range(n_comidas):
                col1, col2 = st.columns([1, 3])
                tipo = col1.text_input("Comida (Ej: Desayuno, Snack, Almuerzo...)", key=f"t_{dia}_{i}")
                detalle = col2.text_input("Alimentos (Ej: 2 huevos, 1 pan...)", key=f"d_{dia}_{i}")
                lista_comidas.append({"nombre": tipo, "detalle": detalle})
            datos_nutricion[dia] = lista_comidas

st.divider()

# BOTÓN DE GENERACIÓN
if st.button("🚀 GENERAR PDF PROFESIONAL", use_container_width=True):
    configuracion = {"entrenador": entrenador, "redes": redes, "fecha_inicio": fecha_in, "fecha_fin": fecha_out}
    datos_cliente = {"nombre": c_nombre, "edad": c_edad, "peso": c_peso, "altura": c_altura}
    
    pdf_bytes = generar_pdf_profesional(datos_rutina, datos_nutricion, configuracion, datos_cliente, logo_subido, estilo_elegido)
    
    nombre_archivo = f"Plan_{c_nombre.replace(' ', '_')}.pdf" if c_nombre else "Plan_Entrenamiento.pdf"
    
    st.success("¡Plan generado con éxito! El diseño ya no tapa las redes sociales.")
    st.download_button(
        label=f"📥 Descargar {nombre_archivo}",
        data=bytes(pdf_bytes),
        file_name=nombre_archivo,
        mime="application/pdf"
    )