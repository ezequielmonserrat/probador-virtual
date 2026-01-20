import streamlit as st
import requests
from bs4 import BeautifulSoup
import PIL.Image
import PIL.ImageOps
import io
from google import genai

# Interfaz Solo Deportes
st.set_page_config(page_title="Probador Virtual Pro", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    div.stButton > button:first-child {
        background-color: #0082C9; color: white; border: none; 
        width: 100%; font-weight: bold; height: 3.5em;
    }
    </style>
    """, unsafe_allow_html=True)

try:
    # CORRECCIÓN DE SINTAXIS: El paréntesis ahora cierra correctamente
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception:
    st.error("Error en API Key.")
    st.stop()

url_producto = st.text_input("Link del producto:")
foto_usuario = st.file_uploader("Tu foto (4:5) 📸", type=['jpg', 'png', 'jpeg'])

if st.button("VER CÓMO ME QUEDA 😎"):
    if url_producto and foto_usuario:
        try:
            with st.spinner("Usando motor Pro para máxima fidelidad..."):
                res = requests.get(url_producto, headers={'User-Agent': 'Mozilla/5.0'})
                soup = BeautifulSoup(res.text, 'html.parser')
                img_src = soup.find("meta", property="og:image")['content']
                img_prenda = PIL.Image.open(io.BytesIO(requests.get(img_src).content))
                
                u_img = PIL.ImageOps.exif_transpose(PIL.Image.open(foto_usuario))
                ancho, alto = u_img.size

                # PROMPT OPTIMIZADO PARA VERSIÓN PRO
                prompt = (
                    f"Mantén estrictamente la relación de aspecto vertical {ancho}x{alto}. "
                    "Realiza un 'virtual try-on' transfiriendo la prenda de la Imagen 2 al sujeto de la Imagen 1. "
                    "Conserva el fondo original y la orientación vertical sin rotaciones."
                )
                
                # CAMBIO A MODELO SUPERIOR
                # Nota: 'imagen-3.0-generate' es el identificador para la versión de alta fidelidad.
                resultado = client.models.generate_content(
                    model='imagen-3.0-generate-001', 
                    contents=[prompt, u_img, img_prenda]
                )
                
                for part in resultado.candidates[0].content.parts:
                    if part.inline_data:
                        final = PIL.Image.open(io.BytesIO(part.inline_data.data))
                        
                        # Si el modelo Pro detecta la verticalidad, ya no necesitaremos rotar
                        st.image(final, use_container_width=True)
                        st.success("Procesado con motor de alta fidelidad.")
                        
        except Exception as e:
            st.error(f"Error: {e}")
