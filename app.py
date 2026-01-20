import streamlit as st
import requests
from bs4 import BeautifulSoup
import PIL.Image
import PIL.ImageOps
import io
from google import genai

# 1. Configuración de Marca Solo Deportes
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

# 2. Entradas
url_producto = st.text_input("Link del producto de Solo Deportes:")
foto_usuario = st.file_uploader("Subí tu foto (4:5) 📸", type=['jpg', 'png', 'jpeg'])

if st.button("VER CÓMO ME QUEDA 😎"):
    if url_producto and foto_usuario:
        try:
            with st.spinner("Buscando producto y procesando..."):
                # --- SCRAPING ROBUSTO PARA EVITAR NONETYPE ---
                res = requests.get(url_producto, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
                soup = BeautifulSoup(res.text, 'html.parser')
                
                # Intentamos varios selectores por si cambia la web
                img_tag = (
                    soup.find("meta", property="og:image") or 
                    soup.find("img", class_="gallery-placeholder__image") or
                    soup.find("img", {"id": "magnifier-item-0"})
                )
                
                if not img_tag:
                    st.error("No se pudo obtener la imagen del link. Verifica el enlace.")
                    st.stop()
                
                img_url = img_tag['content'] if img_tag.has_attr('content') else img_tag['src']
                img_prenda = PIL.Image.open(io.BytesIO(requests.get(img_url).content))
                
                # 3. Procesar Usuario
                u_img = PIL.ImageOps.exif_transpose(PIL.Image.open(foto_usuario))
                ancho_orig, alto_orig = u_img.size

                # Prompt de fidelidad absoluta
                prompt = (
                    "Tarea: Virtual Try-on. Viste a la persona de la Imagen 1 con la prenda de la Imagen 2. "
                    "Usa exactamente el diseño de la prenda. No cambies la relación de aspecto."
                )
                
                # Usamos el modelo estable que no da 404
                resultado = client.models.generate_content(
                    model='gemini-2.0-flash', 
                    contents=[prompt, u_img, img_prenda]
                )
                
                # 4. Entrega sin deformación
                for part in resultado.candidates[0].content.parts:
                    if part.inline_data:
                        final = PIL.Image.open(io.BytesIO(part.inline_data.data))
                        # Forzamos que la salida sea igual a la entrada para evitar giros
                        final = final.resize((ancho_orig, alto_orig), PIL.Image.Resampling.LANCZOS)
                        st.image(final, use_container_width=True)
                        st.success("¡Prueba completada con éxito!")
                        
        except Exception as e:
            st.error(f"Error inesperado: {str(e)}")
