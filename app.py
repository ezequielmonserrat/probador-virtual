import streamlit as st
import requests
from bs4 import BeautifulSoup
import PIL.Image
import PIL.ImageOps
import io
from google import genai

st.set_page_config(page_title="Probador Virtual Pro", layout="centered")

# Estilos Solo Deportes
st.markdown("""
    <style>
    header, #MainMenu, footer {visibility: hidden;}
    .stApp { background-color: #FFFFFF; }
    div.stButton > button:first-child {
        background-color: #0082C9; color: white; border: none; width: 100%; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error("Error de configuración.")
    st.stop()

url_producto = st.text_input("Link del producto:")
foto_usuario = st.file_uploader("Tu foto 📸", type=['jpg', 'png', 'jpeg'])

def hacer_cuadrada(im, color=(255, 255, 255)):
    """Añade bordes blancos para que la IA no rote la imagen"""
    width, height = im.size
    if width == height: return im
    elif width > height:
        result = PIL.Image.new(im.mode, (width, width), color)
        result.paste(im, (0, (width - height) // 2))
        return result
    else:
        result = PIL.Image.new(im.mode, (height, height), color)
        result.paste(im, ((height - width) // 2, 0))
        return result

if st.button("PROBAR AHORA"):
    if url_producto and foto_usuario:
        try:
            with st.spinner("Procesando con bloqueo de orientación..."):
                # 1. Obtener imagen de la prenda
                res = requests.get(url_producto, headers={'User-Agent': 'Mozilla/5.0'})
                soup = BeautifulSoup(res.text, 'html.parser')
                img_src = soup.find("meta", property="og:image")['content']
                img_prenda = PIL.Image.open(io.BytesIO(requests.get(img_src).content))
                
                # 2. Pre-procesar foto de usuario para que sea CUADRADA
                img_user_raw = PIL.ImageOps.exif_transpose(PIL.Image.open(foto_usuario))
                w_orig, h_orig = img_user_raw.size
                img_user_sq = hacer_cuadrada(img_user_raw) # Blindaje contra rotación
                
                # 3. IA: Instrucción simplificada pero firme
                prompt = "Cambia la prenda del sujeto por la de la Imagen 2. Mantén la posición y orientación vertical del sujeto."
                
                resultado = client.models.generate_content(
                    model='gemini-2.5-flash-image',
                    contents=[prompt, img_user_sq, img_prenda]
                )
                
                # 4. Post-proceso: Recortar y devolver a tamaño original
                for part in resultado.candidates[0].content.parts:
                    if part.inline_data:
                        res_img = PIL.Image.open(io.BytesIO(part.inline_data.data))
                        # Si la IA la rotó a pesar de ser cuadrada, la enderezamos
                        if res_img.width > res_img.height and h_orig > w_orig:
                            res_img = res_img.rotate(-90, expand=True)
                        
                        # Ajuste final al tamaño exacto que subiste
                        final_res = res_img.resize(img_user_sq.size).crop(
                            ((img_user_sq.width - w_orig) // 2, 
                             (img_user_sq.height - h_orig) // 2,
                             (img_user_sq.width + w_orig) // 2, 
                             (img_user_sq.height + h_orig) // 2)
                        )
                        
                        st.image(final_res, use_container_width=True)
                        st.balloons()
        except Exception as e:
            st.error(f"Error: {e}")
