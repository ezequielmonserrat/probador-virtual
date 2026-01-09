import streamlit as st
import requests
from bs4 import BeautifulSoup
import PIL.Image
import PIL.ImageOps
import io
from google import genai

# 1. Recuperamos la Identidad Visual Original
st.set_page_config(page_title="Probador Virtual | Solo Deportes", layout="centered")

st.markdown("""
    <style>
    header, #MainMenu, footer {visibility: hidden;}
    .stApp { background-color: #FFFFFF; }
    div.stButton > button:first-child {
        background-color: #0082C9; color: white; border: none; 
        width: 100%; font-weight: bold; height: 3em; border-radius: 5px;
    }
    div.stButton > button:first-child:hover { background-color: #E30052; }
    </style>
    """, unsafe_allow_html=True)

# Recuperamos los títulos exactos que pediste
st.markdown("<h1 style='text-align: center;'>👕 PROBADOR VIRTUAL</h1>", unsafe_allow_html=True)

try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception:
    st.error("Error: Configura tu GEMINI_API_KEY.")
    st.stop()

# 2. Interfaz con las etiquetas originales
url_producto = st.text_input("Pegá el link de la prenda aquí:")
foto_usuario = st.file_uploader("Subí tu foto 📸", type=['jpg', 'png', 'jpeg'])

if st.button("Ver cómo me queda 😎"):
    if url_producto and foto_usuario:
        try:
            with st.spinner("Buscando prenda y procesando..."):
                # Scraping mejorado para Solo Deportes
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                res = requests.get(url_producto, headers=headers, timeout=10)
                soup = BeautifulSoup(res.text, 'html.parser')
                
                # Buscamos la imagen del producto en meta tags o etiquetas de imagen
                img_tag = soup.find("meta", property="og:image") or soup.find("img", {"class": "product-image"})
                img_url = img_tag['content'] if img_tag.has_attr('content') else img_tag['src']
                
                img_prenda = PIL.Image.open(io.BytesIO(requests.get(img_url).content))
                
                # Procesar usuario y registrar verticalidad real
                u_raw = PIL.Image.open(foto_usuario)
                u_img = PIL.ImageOps.exif_transpose(u_raw)
                w_in, h_in = u_img.size
                es_vertical_real = h_in > w_in

                # Prompt simplificado para que la IA no se confunda
                prompt = "Viste a la persona con la prenda de la Imagen 2. Mantén fondo y postura vertical."
                
                resultado = client.models.generate_content(
                    model='gemini-2.5-flash-image',
                    contents=[prompt, u_img, img_prenda]
                )
                
                for part in resultado.candidates[0].content.parts:
                    if part.inline_data:
                        gen_img = PIL.Image.open(io.BytesIO(part.inline_data.data))
                        
                        # BLOQUE DE CORRECCIÓN FÍSICA
                        # Si tu foto es vertical pero la IA entregó algo horizontal, rotamos sí o sí.
                        if es_vertical_real and (gen_img.width > gen_img.height):
                            # Rotamos 90 grados para devolver al sujeto a su posición
                            gen_img = gen_img.rotate(-90, expand=True)
                        
                        # Forzamos a que el tamaño final sea el mismo que el original
                        final = gen_img.resize((w_in, h_in), PIL.Image.Resampling.LANCZOS)
                        
                        st.image(final, use_container_width=True)
                        st.success("¡Esa camiseta te queda espectacular!")
                        
        except Exception as e:
            st.error(f"No pudimos procesar el link o la foto. Error: {e}")
