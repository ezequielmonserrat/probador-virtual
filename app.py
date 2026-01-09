import streamlit as st
import requests
from bs4 import BeautifulSoup
import PIL.Image
import PIL.ImageOps
import io
from google import genai

# 1. Identidad Visual Original
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

# 2. Interfaz con las etiquetas que te gustaban
url_producto = st.text_input("Link del producto de Solo Deportes:")
foto_usuario = st.file_uploader("Subí tu foto para probar 📸", type=['jpg', 'png', 'jpeg'])

if st.button("VER CÓMO ME QUEDA 😎"):
    if url_producto and foto_usuario:
        try:
            with st.spinner("Procesando tu prueba..."):
                # Scraping estándar
                res = requests.get(url_producto, headers={'User-Agent': 'Mozilla/5.0'})
                soup = BeautifulSoup(res.text, 'html.parser')
                img_tag = soup.find("meta", property="og:image") or soup.find("img")
                img_prenda = PIL.Image.open(io.BytesIO(requests.get(img_tag['content'] if img_tag.has_attr('content') else img_tag['src']).content))
                
                # Procesar usuario
                u_img = PIL.ImageOps.exif_transpose(PIL.Image.open(foto_usuario))

                # 3. EL PROMPT DE FIDELIDAD (Lo que funcionó antes)
                # Eliminamos tecnicismos de rotación y volvemos a la instrucción de diseño.
                prompt = (
                    "Instrucción: Ignora lo que creas saber de esta prenda. "
                    "Usa EXACTAMENTE el diseño de la Imagen 2 (logos, colores, detalles). "
                    "Viste a la persona de la Imagen 1 manteniendo su fondo y su posición original. "
                    "No deformes la imagen."
                )
                
                resultado = client.models.generate_content(
                    model='gemini-2.5-flash-image',
                    contents=[prompt, u_img, img_prenda]
                )
                
                # 4. Entrega limpia (Sin redimensionar para evitar deformación)
                for part in resultado.candidates[0].content.parts:
                    if part.inline_data:
                        final = PIL.Image.open(io.BytesIO(part.inline_data.data))
                        st.image(final, use_container_width=True)
                        st.success("¡Listo! Así se te vería la prenda original.")
                        
        except Exception as e:
            st.error(f"Error al conectar con la tienda: {e}")
