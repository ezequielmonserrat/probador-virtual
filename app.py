import streamlit as st
import requests
from bs4 import BeautifulSoup
import PIL.Image
import PIL.ImageOps
import io
from google import genai

# 1. Recuperamos la estética de Solo Deportes
st.set_page_config(page_title="Probador Virtual | Solo Deportes", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    div.stButton > button:first-child {
        background-color: #0082C9; color: white; border: none; 
        width: 100%; font-weight: bold; height: 3.5em;
    }
    div.stButton > button:first-child:hover { background-color: #E30052; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #0082C9;'>👕 PROBADOR VIRTUAL</h1>", unsafe_allow_html=True)

try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception:
    st.error("Error en la conexión con Gemini.")
    st.stop()

url_producto = st.text_input("Link del producto de la tienda:")
foto_usuario = st.file_uploader("Subí tu foto (4:5 recomendado) 📸", type=['jpg', 'png', 'jpeg'])

if st.button("VER CÓMO ME QUEDA 😎"):
    if url_producto and foto_usuario:
        try:
            with st.spinner("Manteniendo orientación original..."):
                # Scraping directo
                res = requests.get(url_producto, headers={'User-Agent': 'Mozilla/5.0'})
                soup = BeautifulSoup(res.text, 'html.parser')
                img_url = soup.find("meta", property="og:image")['content']
                img_prenda = PIL.Image.open(io.BytesIO(requests.get(img_url).content))
                
                # --- PASO CLAVE: FIJAR EL LIENZO ---
                # Cargamos la foto y eliminamos cualquier rotación fantasma de los sensores del celular
                u_img = PIL.ImageOps.exif_transpose(PIL.Image.open(foto_usuario))
                ancho, alto = u_img.size

                # Prompt de 'Contención Espacial'
                # Le damos las coordenadas de importancia para que no gire la foto.
                prompt = (
                    f"Mantén estrictamente el formato vertical {ancho}x{alto}. "
                    "Viste al sujeto de la Imagen 1 con la ropa de la Imagen 2. "
                    "PROHIBIDO: No gires la cámara, no cambies el horizonte. "
                    "La cabeza debe quedar en el eje superior siempre."
                )
                
                resultado = client.models.generate_content(
                    model='gemini-2.5-flash-image',
                    contents=[prompt, u_img, img_prenda]
                )
                
                # --- VALIDACIÓN DE SALIDA SIN DEFORMACIÓN ---
                for part in resultado.candidates[0].content.parts:
                    if part.inline_data:
                        final = PIL.Image.open(io.BytesIO(part.inline_data.data))
                        
                        # Si la IA la rotó por error (la puso horizontal), la regresamos
                        if final.width > final.height and alto > ancho:
                            final = final.transpose(PIL.Image.ROTATE_270)
                        
                        # Ajuste final al molde original de tu foto
                        final = final.resize((ancho, alto), PIL.Image.Resampling.LANCZOS)
                        
                        st.image(final, use_container_width=True)
                        st.success("Resultado en posición correcta.")
                        
        except Exception as e:
            st.error(f"Error técnico: {e}")
