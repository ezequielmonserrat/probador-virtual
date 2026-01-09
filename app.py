import streamlit as st
import requests
from bs4 import BeautifulSoup
import PIL.Image
import PIL.ImageOps
import io
from google import genai

# 1. Interfaz Original Solo Deportes
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
    st.error("Error: Configura tu GEMINI_API_KEY.")
    st.stop()

url_producto = st.text_input("Link del producto de Solo Deportes:")
foto_usuario = st.file_uploader("Subí tu foto para probar 📸", type=['jpg', 'png', 'jpeg'])

if st.button("VER CÓMO ME QUEDA 😎"):
    if url_producto and foto_usuario:
        try:
            with st.spinner("Procesando con relación de aspecto original..."):
                # Scraping de la prenda
                res = requests.get(url_producto, headers={'User-Agent': 'Mozilla/5.0'})
                soup = BeautifulSoup(res.text, 'html.parser')
                img_tag = soup.find("meta", property="og:image") or soup.find("img")
                img_prenda = PIL.Image.open(io.BytesIO(requests.get(img_tag['content'] if img_tag.has_attr('content') else img_tag['src']).content))
                
                # --- CAPTURA DE DIMENSIONES ORIGINALES ---
                u_img = PIL.ImageOps.exif_transpose(PIL.Image.open(foto_usuario))
                ancho_orig, alto_orig = u_img.size # Guardamos el ADN de tu foto

                # Prompt enfocado en el lienzo
                prompt = (
                    f"Tarea: Virtual Try-on. Mantén el lienzo exacto de {ancho_orig}x{alto_orig}. "
                    "Viste al sujeto de la Imagen 1 con la prenda de la Imagen 2. "
                    "No recortes el fondo, no cambies la relación de aspecto y mantén al sujeto vertical."
                )
                
                resultado = client.models.generate_content(
                    model='gemini-2.5-flash-image',
                    contents=[prompt, u_img, img_prenda]
                )
                
                for part in resultado.candidates[0].content.parts:
                    if part.inline_data:
                        gen_img = PIL.Image.open(io.BytesIO(part.inline_data.data))
                        
                        # --- CORRECCIÓN FINAL DE RELACIÓN DE ASPECTO ---
                        # 1. Si la IA la rotó, la enderezamos primero
                        if (alto_orig > ancho_orig) and (gen_img.width > gen_img.height):
                            gen_img = gen_img.rotate(-90, expand=True)
                        
                        # 2. Forzamos el tamaño original exacto (mismo alto y ancho que subiste)
                        # Usamos Resampling.LANCZOS para que no se deforme el contenido.
                        final = gen_img.resize((ancho_orig, alto_orig), PIL.Image.Resampling.LANCZOS)
                        
                        st.image(final, use_container_width=True)
                        st.success("¡Perfecto! Se mantuvo tu encuadre original.")
                        
        except Exception as e:
            st.error(f"Error: {e}")
