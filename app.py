import streamlit as st
import requests
from bs4 import BeautifulSoup
import PIL.Image
import PIL.ImageOps
import io
from google import genai

# 1. Configuración de página y Estilo Profesional (Colores Solo Deportes)
st.set_page_config(page_title="Probador Virtual | Solo Deportes", page_icon="👕", layout="centered")

# Estilos CSS con los códigos HEX extraídos del logo
st.markdown("""
    <style>
    /* Fondo limpio blanco */
    .stApp {
        background-color: #FFFFFF;
    }
    /* Textos en negro para contraste profesional */
    h1, h2, h3, p, span, label {
        color: #1A1A1A !important;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    /* Botón con el Cian exacto del logo (#0082C9) */
    div.stButton > button:first-child {
        background-color: #0082C9; 
        color: white;
        border: none;
        border-radius: 4px;
        font-weight: bold;
        padding: 0.6rem 2rem;
        width: 100%;
        transition: all 0.3s ease;
    }
    /* Botón cambia al Magenta exacto (#E30052) al pasar el mouse */
    div.stButton > button:first-child:hover {
        background-color: #E30052;
        color: white;
        border: none;
    }
    /* Borde del input con el Verde exacto del logo (#009B3A) */
    .stTextInput input {
        border-color: #009B3A !important;
    }
    /* Estilo para el cargador de archivos */
    .stFileUploader {
        border: 1px dashed #0082C9;
        border-radius: 10px;
        padding: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Título de Marca Blanca
st.title("👕 PROBADOR VIRTUAL")
st.markdown("<p style='font-size: 1.1rem; color: #555;'>Experimentá cómo te queda la ropa de <b>Solo Deportes</b> antes de comprar.</p>", unsafe_allow_html=True)
st.markdown("---")

# 3. Conexión Segura con Gemini (Secrets)
try:
    api_key_interna = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key_interna)
except Exception:
    st.error("⚠️ Error: Configure la GEMINI_API_KEY en los Secrets de Streamlit.")
    st.stop()

# 4. Interfaz de Usuario
url_producto = st.text_input("1. Pegá el link de la prenda aquí:")
foto_usuario = st.file_uploader("2. Subí tu foto (vertical para mejores resultados) 📸", type=['jpg', 'png', 'jpeg'])

if st.button("VER CÓMO ME QUEDA 😎"):
    if not url_producto or not foto_usuario:
        st.error("Por favor, completá el link y subí tu foto.")
    else:
        try:
            with st.spinner("🪄 Procesando prenda y ajustando talle..."):
                # Scraping de la imagen del producto
                res = requests.get(url_producto, headers={'User-Agent': 'Mozilla/5.0'})
                soup = BeautifulSoup(res.text, 'html.parser')
                img_url = soup.find("meta", property="og:image")['content']
                img_prenda = PIL.Image.open(io.BytesIO(requests.get(img_url).content))
                
                # Respetar orientación original de la foto del usuario
                img_user_raw = PIL.Image.open(foto_usuario)
                img_user = PIL.ImageOps.exif_transpose(img_user_raw)

                # Extraer nombre del producto para la IA
                h1 = soup.find("h1")
                titulo = h1.text.strip().lower() if h1 else "prenda"
                prompt_n = f"Extrae el nombre del objeto (una palabra) de: {titulo}"
                nombre_obj = client.models.generate_content(model='gemini-2.0-flash', contents=[prompt_n]).text.strip().lower()

                # Generación de Imagen (Virtual Try-On)
                instruccion = f"Sustituye la prenda del usuario por la {nombre_obj} de la Imagen 2. Mantén la pose y orientación vertical."
                
                resultado = client.models.generate_content(
                    model='gemini-2.5-flash-image',
                    contents=[instruccion, img_user, img_prenda]
                )
                
                # Entrega final con corrección de rotación
                for part in resultado.candidates[0].content.parts:
                    if part.inline_data:
                        final_res = PIL.Image.open(io.BytesIO(part.inline_data.data))
                        final_res = PIL.ImageOps.exif_transpose(final_res)
                        st.image(final_res, use_container_width=True, caption="Tu look en Solo Deportes")
                        st.balloons()
                
                st.success(f"🔥 ¡Esa {nombre_obj} te queda espectacular!")
                        
        except Exception as e:
            st.error(f"No pudimos procesar este producto. Verificá el link o intentá con otro. (Error: {e})")

# Pie de página estilo corporativo
st.markdown("<br><hr><center><small>Probador Virtual Independiente | Optimizado para E-commerce</small></center>", unsafe_allow_html=True)
