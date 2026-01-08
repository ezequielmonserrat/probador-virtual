import streamlit as st
import requests
from bs4 import BeautifulSoup
import PIL.Image
import PIL.ImageOps
import io
from google import genai

# 1. Configuración de página y Estilo Profesional
st.set_page_config(page_title="Probador Virtual | Solo Deportes", page_icon="👕", layout="centered")

# CSS para ocultar menús y aplicar colores de marca exacta
st.markdown("""
    <style>
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp { background-color: #FFFFFF; }
    
    /* Botón con el Cian exacto (#0082C9) */
    div.stButton > button:first-child {
        background-color: #0082C9; 
        color: white; 
        border: none; 
        width: 100%; 
        font-weight: bold;
        border-radius: 4px;
        transition: all 0.3s ease;
    }
    /* Hover con el Magenta exacto (#E30052) */
    div.stButton > button:first-child:hover {
        background-color: #E30052;
        color: white;
    }
    /* Borde verde para inputs (#009B3A) */
    .stTextInput input { border-color: #009B3A !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("👕 PROBADOR VIRTUAL")
st.markdown("<p style='color: #666;'>Fidelidad absoluta en encuadre y diseño.</p>", unsafe_allow_html=True)

# 2. Conexión con Gemini (Línea 45 corregida)
try:
    # Aquí cerramos correctamente el paréntesis que daba error
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error(f"⚠️ Error de API Key: {e}")
    st.stop()

# Historial de sesión
if 'historial' not in st.session_state:
    st.session_state.historial = []

# 3. Interfaz de Usuario
url_producto = st.text_input("1. Pegá el link de la prenda aquí:")
foto_usuario = st.file_uploader("2. Subí tu foto (mantenemos el encuadre original) 📸", type=['jpg', 'png', 'jpeg'])

if st.button("GENERAR PRUEBA FIEL 😎"):
    if not url_producto or not foto_usuario:
        st.error("Por favor, completá los campos.")
    else:
        try:
            with st.spinner("🪄 Procesando sin recortar tu imagen..."):
                # Scraping de imagen del producto
                headers = {'User-Agent': 'Mozilla/5.0'}
                res = requests.get(url_producto, headers=headers)
                soup = BeautifulSoup(res.text, 'html.parser')
                img_tag = soup.find("meta", property="og:image") or soup.find("meta", name="twitter:image")
                
                if not img_tag:
                    st.error("No se pudo obtener la imagen del producto.")
                    st.stop()
                
                img_prenda = PIL.Image.open(io.BytesIO(requests.get(img_tag['content']).content))
                
                # --- PROCESAMIENTO DE IMAGEN DE USUARIO ---
                img_user_raw = PIL.Image.open(foto_usuario)
                img_user = PIL.ImageOps.exif_transpose(img_user_raw)
                ancho_orig, alto_orig = img_user.size # BLOQUEO DE DIMENSIONES ORIGINALES

                # --- IA CON INSTRUCCIÓN DE FIDELIDAD ---
                instruccion = (
                    f"TAREA: Virtual Try-On de alta precisión. "
                    f"REGLA CRÍTICA: Mantén EXACTAMENTE el encuadre, fondo y dimensiones de la Imagen 1. "
                    f"Copia el diseño, logos y colores de la Imagen 2 sobre el cuerpo de la Imagen 1. "
                    f"No recortes la imagen resultante. Respeta la proporción {ancho_orig}x{alto_orig}."
                )
                
                resultado = client.models.generate_content(
                    model='gemini-2.5-flash-image',
                    contents=[instruccion, img_user, img_prenda]
                )
                
                # --- ENTREGA FINAL Y CORRECCIÓN DE FORMATO ---
                for part in resultado.candidates[0].content.parts:
                    if part.inline_data:
                        final_res = PIL.Image.open(io.BytesIO(part.inline_data.data))
                        final_res = PIL.ImageOps.exif_transpose(final_res)
                        
                        # Validamos que no haya cambiado la orientación
                        if final_res.size != (ancho_orig, alto_orig):
                            if final_res.width > final_res.height and alto_orig > ancho_orig:
                                final_res = final_res.rotate(-90, expand=True)
                            
                            # Forzamos el tamaño original para evitar recortes (como en la foto del río)
                            final_res = final_res.resize((ancho_orig, alto_orig), PIL.Image.Resampling.LANCZOS)
                        
                        st.image(final_res, use_container_width=True)
                        st.session_state.historial.append(final_res)
                        st.balloons()
                
                st.success("🔥 ¡Listo! Se mantuvo tu encuadre original.")
                        
        except Exception as e:
            st.error(f"Error técnico: {e}")

# Historial
if st.session_state.historial:
    st.markdown("---")
    st.subheader("🕒 Pruebas recientes")
    cols = st.columns(3)
    for idx, img in enumerate(reversed(st.session_state.historial[-3:])):
        cols[idx % 3].image(img, use_container_width=True)

st.markdown("<br><hr><center><small>Probador Virtual v2.5 | Solo Deportes Edition</small></center>", unsafe_allow_html=True)
