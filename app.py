import streamlit as st
import requests
from bs4 import BeautifulSoup
import PIL.Image
import PIL.ImageOps
import io
from google import genai

# Configuración básica
st.set_page_config(page_title="Probador Virtual Pro", layout="centered")

# Ocultar menús para que parezca nativa
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
except Exception:
    st.error("Error en API Key.")
    st.stop()

url_prenda = st.text_input("Link del producto:")
foto_usuario = st.file_uploader("Subí tu foto 📸", type=['jpg', 'png', 'jpeg'])

if st.button("VER RESULTADO"):
    if url_prenda and foto_usuario:
        try:
            with st.spinner("Procesando..."):
                # 1. Obtener imagen de la prenda
                res = requests.get(url_prenda, headers={'User-Agent': 'Mozilla/5.0'})
                soup = BeautifulSoup(res.text, 'html.parser')
                img_src = soup.find("meta", property="og:image")['content']
                img_prenda = PIL.Image.open(io.BytesIO(requests.get(img_src).content))
                
                # 2. Preparar foto de usuario y detectar orientación
                u_img = PIL.ImageOps.exif_transpose(PIL.Image.open(foto_usuario))
                w_in, h_in = u_img.size
                es_vertical_in = h_in > w_in # ¿La foto original es parada?

                # 3. Pedir a la IA el cambio (Prompt mínimo para evitar confusión)
                prompt = "Vestir a la persona de la Imagen 1 con la prenda de la Imagen 2. Mantener fondo."
                
                resultado = client.models.generate_content(
                    model='gemini-2.5-flash-image',
                    contents=[prompt, u_img, img_prenda]
                )
                
                # 4. REVISIÓN DE SALIDA (Aquí estaba el fallo)
                for part in resultado.candidates[0].content.parts:
                    if part.inline_data:
                        out_img = PIL.Image.open(io.BytesIO(part.inline_data.data))
                        w_out, h_out = out_img.size
                        es_horizontal_out = w_out > h_out # ¿La IA la sacó acostada?

                        # CORRECCIÓN AUTOMÁTICA
                        # Si entró vertical y salió horizontal -> ROTAR 90 GRADOS
                        if es_vertical_in and es_horizontal_out:
                            out_img = out_img.rotate(-90, expand=True)
                        
                        # Si entró horizontal y salió vertical -> ROTAR 90 GRADOS
                        elif not es_vertical_in and not es_horizontal_out:
                            out_img = out_img.rotate(90, expand=True)

                        # Forzar tamaño final al original para evitar deformación
                        final = out_img.resize((w_in, h_in), PIL.Image.Resampling.LANCZOS)
                        
                        st.image(final, use_container_width=True)
                        st.balloons()
                        
        except Exception as e:
            st.error(f"Error: {e}")
