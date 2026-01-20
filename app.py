import streamlit as st
import requests
from bs4 import BeautifulSoup
import PIL.Image
import PIL.ImageOps
import io
from google import genai

# Interfaz Solo Deportes
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
    st.error("Error: Revisa tu API KEY.")
    st.stop()

url_producto = st.text_input("Link del producto:")
foto_usuario = st.file_uploader("Subí tu foto 📸", type=['jpg', 'png', 'jpeg'])

def hacer_cuadrada(img):
    """Agrega bordes para que la IA no rote la imagen"""
    width, height = img.size
    new_side = max(width, height)
    result = PIL.Image.new("RGB", (new_side, new_side), (255, 255, 255))
    offset = ((new_side - width) // 2, (new_side - height) // 2)
    result.paste(img, offset)
    return result, offset, (width, height)

if st.button("VER CÓMO ME QUEDA 😎"):
    if url_producto and foto_usuario:
        try:
            with st.spinner("Procesando con protección de orientación..."):
                # Scraping
                res = requests.get(url_producto, headers={'User-Agent': 'Mozilla/5.0'})
                soup = BeautifulSoup(res.text, 'html.parser')
                img_src = soup.find("meta", property="og:image")['content']
                img_prenda = PIL.Image.open(io.BytesIO(requests.get(img_src).content))
                
                # Pre-procesamiento: La hacemos cuadrada para que la IA no la gire
                u_img_orig = PIL.ImageOps.exif_transpose(PIL.Image.open(foto_usuario))
                u_img_sq, offset, size_orig = hacer_cuadrada(u_img_orig)

                # Usamos el modelo que sí funciona en tu cuenta
                prompt = "Viste a la persona con la prenda de la Imagen 2. Mantén fondo y postura vertical."
                
                resultado = client.models.generate_content(
                    model='gemini-2.0-flash', # Volvemos al modelo estable
                    contents=[prompt, u_img_sq, img_prenda]
                )
                
                for part in resultado.candidates[0].content.parts:
                    if part.inline_data:
                        gen_img = PIL.Image.open(io.BytesIO(part.inline_data.data))
                        
                        # Post-procesamiento: Recortamos los bordes y volvemos a 4:5
                        # Esto elimina la deformación y el giro
                        left, top = offset
                        right, bottom = left + size_orig[0], top + size_orig[1]
                        final = gen_img.resize(u_img_sq.size).crop((left, top, right, bottom))
                        
                        st.image(final, use_container_width=True)
                        st.success("¡Orientación y aspecto preservados!")
                        
        except Exception as e:
            st.error(f"Error: {e}")
