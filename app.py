import streamlit as st
import requests
from bs4 import BeautifulSoup
import PIL.Image
import PIL.ImageOps
import io
from google import genai

# 1. Configuración de página y Estilo Personalizado (CSS)
st.set_page_config(page_title="Probador Virtual | Solo Deportes", page_icon="👕", layout="centered")

# Inyección de estilos para emular Solo Deportes
st.markdown("""
    <style>
    /* Fondo de la aplicación */
    .stApp {
        background-color: #FFFFFF;
    }
    /* Títulos y textos en negro para contraste */
    h1, h2, h3, p, span, label {
        color: #1A1A1A !important;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    /* Personalización del botón (Cian y Magenta) */
    div.stButton > button:first-child {
        background-color: #00D1FF; /* Cian característico */
        color: white;
        border: none;
        border-radius: 5px;
        font-weight: bold;
        padding: 0.6rem 2rem;
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        background-color: #FF00FF; /* Cambio a Magenta al pasar el mouse */
        color: white;
        border: none;
    }
    /* Estilo para los inputs */
    .stTextInput input {
        border-color: #00D1FF !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Título con look de Marca Blanca
st.title("PROBADOR VIRTUAL")
st.markdown("<p style='font-size: 1.2rem; color: #666;'>Probá tus productos de <b>Solo Deportes</b> de forma instantánea.</p>", unsafe_allow_html=True)
st.markdown("---")

# 3. Conexión Segura (Secrets)
try:
    api_key_interna = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key_interna)
except Exception:
    st.error("⚠️ Error de configuración en Secrets.")
    st.stop()

# 4. Interfaz adaptada
url_producto = st.text_input("1. Pegá el link del producto (Solo Deportes, Sporting, etc):")
foto_usuario = st.file_uploader("2. Subí tu foto para el probador 📸", type=['jpg', 'png', 'jpeg'])

if st.button("PROBAR AHORA 😎"):
    if not url_producto or not foto_usuario:
        st.error("Por favor, completá los pasos para continuar.")
    else:
        try:
            with st.spinner("🪄 Ajustando la prenda a tu medida..."):
                # Scraping
                res = requests.get(url_producto, headers={'User-Agent': 'Mozilla/5.0'})
                soup = BeautifulSoup(res.text, 'html.parser')
                img_url = soup.find("meta", property="og:image")['content']
                img_prenda = PIL.Image.open(io.BytesIO(requests.get(img_url).content))
                
                # Orientación de foto de usuario
                img_user_raw = PIL.Image.open(foto_usuario)
                img_user = PIL.ImageOps.exif_transpose(img_user_raw)

                # Identificación de objeto
                h1 = soup.find("h1")
                titulo = h1.text.strip().lower() if h1 else "prenda"
                prompt_n = f"Extrae el nombre del objeto (una palabra) de: {titulo}"
                nombre_obj = client.models.generate_content(model='gemini-2.0-flash', contents=[prompt_n]).text.strip().lower()

                # Generación con IA
                instruccion = f"Sustituye la prenda del usuario por la {nombre_obj} de la Imagen 2. Mantén la pose y orientación vertical."
                
                resultado = client.models.generate_content(
                    model='gemini-2.5-flash-image',
                    contents=[instruccion, img_user, img_prenda]
                )
                
                # Entrega final respetando orientación
                for part in resultado.candidates[0].content.parts:
                    if part.inline_data:
                        final_res = PIL.Image.open(io.BytesIO(part.inline_data.data))
                        final_res = PIL.ImageOps.exif_transpose(final_res)
                        st.image(final_res, use_container_width=True, caption="Resultado del Probador Virtual")
                        st.balloons()
                
                st.success(f"🔥 ¡Esa {nombre_obj} te queda genial!")
                        
        except Exception as e:
            st.error(f"No pudimos procesar este link: {e}")

st.markdown("<hr><center><small>Desarrollado con IA para testeo de Ecommerce</small></center>", unsafe_allow_html=True)
