import streamlit as st
import requests
from bs4 import BeautifulSoup
import PIL.Image
import PIL.ImageOps
import io
from google import genai

# 1. Configuración de página y Estética Solo Deportes
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
url_producto = st.text_input("1. Link del producto de la tienda:")
foto_usuario = st.file_uploader("2. Subí tu foto (Vertical) 📸", type=['jpg', 'png', 'jpeg'])

if st.button("GENERAR PRUEBA FIEL"):
    if url_producto and foto_usuario:
        try:
            with st.spinner("🪄 Corrigiendo postura y generando..."):
                # Scraping de prenda
                res = requests.get(url_producto, headers={'User-Agent': 'Mozilla/5.0'})
                soup = BeautifulSoup(res.text, 'html.parser')
                img_src = soup.find("meta", property="og:image")['content']
                img_prenda = PIL.Image.open(io.BytesIO(requests.get(img_src).content))
                
                # --- PROCESO DE ORIENTACIÓN ---
                img_user_raw = PIL.Image.open(foto_usuario)
                # Normalizamos la foto según sus metadatos de rotación
                img_user = PIL.ImageOps.exif_transpose(img_user_raw)
                ancho_orig, alto_orig = img_user.size 
                es_vertical = alto_orig > ancho_orig

                # IA: Instrucción con anclaje visual
                prompt = (
                    "Virtual Try-On de alta fidelidad. "
                    "Imagen 1: Persona (Sujeto principal). Imagen 2: Prenda de la tienda. "
                    "REGLA DE ORO: Mantén la orientación exacta de la Imagen 1. "
                    "Si el sujeto está de pie, el resultado debe estar de pie. "
                    "No rotes la imagen. No cambies el horizonte."
                )
                
                resultado = client.models.generate_content(
                    model='gemini-2.5-flash-image',
                    contents=[prompt, img_user, img_prenda]
                )
                
                # --- FIX DE PÍXELES POST-GENERACIÓN ---
                for part in resultado.candidates[0].content.parts:
                    if part.inline_data:
                        # Cargamos lo que la IA escupió
                        temp_img = PIL.Image.open(io.BytesIO(part.inline_data.data))
                        
                        # CHEQUEO MATEMÁTICO:
                        # Si tu foto era vertical pero la IA entregó algo horizontal...
                        if es_vertical and (temp_img.width > temp_img.height):
                            # ...la rotamos 90 grados para recuperar la posición correcta
                            temp_img = temp_img.rotate(90, expand=True)
                        
                        # PASO FINAL: Forzamos el redimensionamiento al tamaño original
                        # Esto recupera las partes que la IA recortó al intentar hacerla horizontal.
                        final_res = temp_img.resize((ancho_orig, alto_orig), PIL.Image.Resampling.LANCZOS)
                        
                        st.image(final_res, use_container_width=True)
                        st.session_state.historial.append(final_res)
                        st.balloons()
                        
        except Exception as e:
            st.error(f"Error técnico: {e}")

# Historial
if st.session_state.historial:
    st.markdown("---")
    st.subheader("🕒 Pruebas recientes")
    cols = st.columns(3)
    for idx, img in enumerate(reversed(st.session_state.historial[-3:])):
        cols[idx % 3].image(img, use_container_width=True)

