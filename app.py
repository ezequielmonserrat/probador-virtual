import streamlit as st
import requests
from bs4 import BeautifulSoup
import PIL.Image
import PIL.ImageOps
import io
from google import genai

# 1. Configuración de página y Estética
st.set_page_config(page_title="Probador Virtual Pro", layout="centered")

st.markdown("""
    <style>
    header, #MainMenu, footer {visibility: hidden;}
    .stApp { background-color: #FFFFFF; }
    div.stButton > button:first-child {
        background-color: #0082C9; color: white; border: none; width: 100%; font-weight: bold;
    }
    div.stButton > button:first-child:hover { background-color: #E30052; }
    </style>
    """, unsafe_allow_html=True)

st.title("👕 PROBADOR VIRTUAL")

# 2. Inicialización de Cliente
try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error(f"Error de configuración: {e}")
    st.stop()

if 'historial' not in st.session_state:
    st.session_state.historial = []

# 3. Interfaz de Usuario
url_producto = st.text_input("1. Link del producto:")
foto_usuario = st.file_uploader("2. Tu foto (Vertical) 📸", type=['jpg', 'png', 'jpeg'])

if st.button("GENERAR PRUEBA"):
    if url_producto and foto_usuario:
        try:
            with st.spinner("🪄 Corrigiendo orientación y generando..."):
                # Scraping de prenda
                res = requests.get(url_producto, headers={'User-Agent': 'Mozilla/5.0'})
                soup = BeautifulSoup(res.text, 'html.parser')
                img_src = soup.find("meta", property="og:image")['content']
                img_prenda = PIL.Image.open(io.BytesIO(requests.get(img_src).content))
                
                # --- PROCESO CRÍTICO DE ORIENTACIÓN ---
                img_user_raw = PIL.Image.open(foto_usuario)
                img_user = PIL.ImageOps.exif_transpose(img_user_raw)
                ancho_f, alto_f = img_user.size # Medidas reales de tu foto vertical
                
                # IA: Instrucción con restricción de píxeles
                prompt = (
                    f"Virtual Try-On. Imagen 1: Usuario. Imagen 2: Prenda. "
                    f"Mantén la relación de aspecto vertical de {ancho_f}x{alto_f}. "
                    f"No rotes la imagen. No recortes al sujeto. El fondo debe ser el mismo."
                )
                
                resultado = client.models.generate_content(
                    model='gemini-2.5-flash-image',
                    contents=[prompt, img_user, img_prenda]
                )
                
                # --- FIX DE ROTACIÓN POST-GENERACIÓN ---
                for part in resultado.candidates[0].content.parts:
                    if part.inline_data:
                        temp_img = PIL.Image.open(io.BytesIO(part.inline_data.data))
                        
                        # PASO 1: Detectar si la IA la giró (si el resultado es ancho y la original era alta)
                        if temp_img.width > temp_img.height and alto_f > ancho_f:
                            # Rotamos 90 grados a la izquierda para recuperar la verticalidad
                            temp_img = temp_img.rotate(90, expand=True)
                        
                        # PASO 2: Forzar el tamaño exacto para recuperar lo que la IA recortó
                        final_res = temp_img.resize((ancho_f, alto_f), PIL.Image.Resampling.LANCZOS)
                        
                        st.image(final_res, use_container_width=True)
                        st.session_state.historial.append(final_res)
                        st.balloons()
                        
        except Exception as e:
            st.error(f"Error: {e}")

# Historial
if st.session_state.historial:
    st.markdown("---")
    st.subheader("🕒 Pruebas recientes")
    cols = st.columns(3)
    for idx, img in enumerate(reversed(st.session_state.historial[-3:])):
        cols[idx % 3].image(img, use_container_width=True)
