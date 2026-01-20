import streamlit as st
import requests
from bs4 import BeautifulSoup
import PIL.Image
import PIL.ImageOps
import io
from google import genai
from google.genai import types

# --- CONFIGURACIÓN VISUAL ---
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

# --- CONEXIÓN CON LA API ---
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    st.error("Falta la clave GEMINI_API_KEY en Secrets.")
    st.stop()

client = genai.Client(api_key=api_key)

# --- FUNCIONES ---
def preparar_foto(archivo):
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

# --- INTERFAZ ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. La Prenda")
    metodo = st.radio("Origen:", ["Subir Foto Manual", "Link Solo Deportes"])
    img_prenda = None
    if metodo == "Link Solo Deportes":
        url = st.text_input("Pegá el link aquí:")
        if url:
            img_prenda = scrap_solo_deportes(url)
    else:
        f_prenda = st.file_uploader("Foto de la prenda", type=['jpg', 'jpeg', 'png'])
        if f_prenda:
            img_prenda = preparar_foto(f_prenda)
    if img_prenda:
        st.image(img_prenda, width=150)

with col2:
    st.subheader("2. Tu Foto")
    f_user = st.file_uploader("Tu foto", type=['jpg', 'jpeg', 'png'])
    img_usuario = None
    if f_user:
        img_usuario = preparar_foto(f_user)
        st.image(img_usuario, width=150)

st.divider()

# --- PROCESO DE GENERACIÓN ---
if st.button("🚀 GENERAR PRUEBA AHORA"):
    if not img_prenda or not img_usuario:
        st.error("Cargá ambas imágenes.")
    else:
        with st.spinner("Procesando prenda..."):
            try:
                # 1. Parámetros de Seguridad Corregidos (Formato SDK nuevo)
                # Usamos nombres genéricos que el modelo 2.0 Flash acepta sin error
                safety_config = [
                    types.SafetySetting(category="HATE_SPEECH", threshold="OFF"),
                    types.SafetySetting(category="HARASSMENT", threshold="OFF"),
                    types.SafetySetting(category="SEXUALLY_EXPLICIT", threshold="OFF"),
                    types.SafetySetting(category="DANGEROUS_CONTENT", threshold="OFF")
                ]

                # 2. Prompt y Generación
                prompt = "Virtual try-on: replace the shirt in the first image with the garment in the second image. Keep background and person intact."
                
                response = client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=[prompt, img_usuario, img_prenda],
                    config=types.GenerateContentConfig(safety_settings=safety_config)
                )

                # 3. Validación de Respuesta Blindada
                if response.candidates and response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        if part.inline_data:
                            resultado = PIL.Image.open(io.BytesIO(part.inline_data.data))
                            st.success("¡Listo!")
                            st.image(resultado, use_container_width=True)
                            st.stop()
                
                st.error("La IA no devolvió una imagen. Probá con fotos más claras.")

            except Exception as e:
                st.error(f"Error técnico: {str(e)}")
