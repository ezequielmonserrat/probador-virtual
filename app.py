import streamlit as st
import requests
from bs4 import BeautifulSoup
import PIL.Image
import PIL.ImageOps
import io
from google import genai

# 1. Recuperamos la interfaz exacta de Solo Deportes
st.set_page_config(page_title="Probador Virtual | Solo Deportes", layout="centered")

st.markdown("""
    <style>
    header, #MainMenu, footer {visibility: hidden;}
    .stApp { background-color: #FFFFFF; }
    div.stButton > button:first-child {
        background-color: #0082C9; color: white; border: none; 
        width: 100%; font-weight: bold; height: 3.5em; border-radius: 5px;
    }
    div.stButton > button:first-child:hover { background-color: #E30052; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #0082C9;'>👕 PROBADOR VIRTUAL</h1>", unsafe_allow_html=True)

try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception:
    st.error("Error: Revisa la API KEY en Secrets.")
    st.stop()

# 2. Entradas originales
url_producto = st.text_input("Link del producto:")
foto_usuario = st.file_uploader("Subí tu foto para probar 📸", type=['jpg', 'png', 'jpeg'])

if st.button("VER CÓMO ME QUEDA 😎"):
    if url_producto and foto_usuario:
        try:
            with st.spinner("Procesando con alineación forzada..."):
                # Scraping de prenda
                res = requests.get(url_producto, headers={'User-Agent': 'Mozilla/5.0'})
                soup = BeautifulSoup(res.text, 'html.parser')
                img_tag = soup.find("meta", property="og:image") or soup.find("img")
                img_prenda = PIL.Image.open(io.BytesIO(requests.get(img_tag['content']).content))
                
                # --- CAMINO DIFERENTE: PRE-ROTACIÓN ---
                u_img = PIL.ImageOps.exif_transpose(PIL.Image.open(foto_usuario))
                
                # Si la foto es vertical (4:5), la mandamos rotada 90° para compensar el error de la IA
                if u_img.height > u_img.width:
                    u_img_input = u_img.rotate(90, expand=True)
                else:
                    u_img_input = u_img

                # Prompt simplificado sin órdenes de rotación (dejamos que la IA actúe)
                prompt = "Viste a la persona con la prenda de la Imagen 2. Mantén diseño y logos."
                
                resultado = client.models.generate_content(
                    model='gemini-2.5-flash-image',
                    contents=[prompt, u_img_input, img_prenda]
                )
                
                for part in resultado.candidates[0].content.parts:
                    if part.inline_data:
                        final = PIL.Image.open(io.BytesIO(part.inline_data.data))
                        
                        # Si el resultado es horizontal pero debería ser vertical, lo enderezamos
                        if final.width > final.height and u_img.height > u_img.width:
                            final = final.rotate(-90, expand=True)
                        
                        # Ajuste final de píxeles al tamaño original para asegurar 4:5 perfecto
                        final = final.resize(u_img.size, PIL.Image.Resampling.LANCZOS)
                        
                        st.image(final, use_container_width=True)
                        st.success("¡Logrado! Orientación y aspecto preservados.")
                        
        except Exception as e:
            st.error(f"Error: {e}")
