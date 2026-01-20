import streamlit as st
import requests
from bs4 import BeautifulSoup
import PIL.Image
import PIL.ImageOps
import io
from google import genai
from google.genai import types

# --- 1. CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title="Probador Virtual Pro", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    label, p, h1, h2, h3, span { color: white !important; }
    .stTextInput input { color: black !important; }
    div.stButton > button {
        background-color: #0082C9; color: white; width: 100%; font-weight: bold; border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("👕 Probador Virtual Pro")

# --- 2. CONFIGURACIÓN DE API SEGURA ---
# Buscamos la clave en los 'Secrets' de Streamlit para que sea privado y seguro
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    st.error("⚠️ Configuración de seguridad faltante: GEMINI_API_KEY no encontrada en los Secrets.")
    st.info("Por favor, agregá la clave en el panel de Streamlit (Settings > Secrets).")
    st.stop()

client = genai.Client(api_key=api_key)

# --- 3. FUNCIONES DE APOYO ---
def preparar_imagen(archivo):
    img = PIL.Image.open(archivo)
    return PIL.ImageOps.exif_transpose(img)

def scrap_solo_deportes(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        meta = soup.find("meta", property="og:image")
        if meta:
            img_data = requests.get(meta["content"], headers=headers).content
            return PIL.Image.open(io.BytesIO(img_data))
    except:
        return None
    return None

# --- 4. INTERFAZ ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. La Prenda")
    metodo = st.radio("Origen:", ["Link Solo Deportes", "Subir Foto Manual"])
    img_prenda = None
    if metodo == "Link Solo Deportes":
        url = st.text_input("Pegá el link aquí:")
        if url:
            img_prenda = scrap_solo_deportes(url)
    else:
        f_prenda = st.file_uploader("Foto de la prenda", type=['jpg', 'jpeg', 'png'])
        if f_prenda:
            img_prenda = preparar_imagen(f_prenda)
    
    if img_prenda:
        st.image(img_prenda, width=150)

with col2:
    st.subheader("2. Tu Foto")
    f_user = st.file_uploader("Tu foto (de frente)", type=['jpg', 'jpeg', 'png'])
    img_usuario = None
    if f_user:
        img_usuario = preparar_imagen(f_user)
        st.image(img_usuario, width=150)

# --- 5. GENERACIÓN ---
st.divider()

if st.button("🚀 GENERAR PRUEBA AHORA"):
    if not img_prenda or not img_usuario:
        st.error("⚠️ Cargá ambas imágenes primero.")
    else:
        with st.spinner("Procesando con IA segura..."):
            try:
                orig_w, orig_h = img_usuario.size
                
                prompt = (
                    "Virtual try-on task. Replace the clothing of the person in the first image "
                    "with the garment shown in the second image. Maintain the person's face, pose, "
                    "identity, and the background exactly. Fit the new garment naturally."
                )

                safety_settings = [
                    types.SafetySetting(category="HATE_SPEECH", threshold="OFF"),
                    types.SafetySetting(category="HARASSMENT", threshold="OFF"),
                    types.SafetySetting(category="SEXUALLY_EXPLICIT", threshold="OFF"),
                    types.SafetySetting(category="DANGEROUS_CONTENT", threshold="OFF"),
                ]

                response = client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=[prompt, img_usuario, img_prenda],
                    config=types.GenerateContentConfig(
                        safety_settings=safety_settings
                    )
                )

                if response.candidates and
