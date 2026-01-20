import streamlit as st
import requests
from bs4 import BeautifulSoup
import PIL.Image
import PIL.ImageOps
import io
from google import genai
from google.genai import types # Importante para los filtros

# --- 1. INTERFAZ VISUAL ---
st.set_page_config(page_title="Probador Virtual Pro", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    label, p, h1, h2, h3, span { color: white !important; }
    .stTextInput input { color: black !important; }
    div.stButton > button {
        background-color: #0082C9; color: white; width: 100%; font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

st.title("👕 Probador Virtual Pro")

# --- 2. CONFIGURACIÓN DE API ---
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    api_key = st.text_input("Ingresa tu Gemini API Key:", type="password")
    if not api_key: st.stop()

client = genai.Client(api_key=api_key)

# --- 3. FUNCIONES ---
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
    except: return None
    return None

# --- 4. INTERFAZ ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. La Prenda")
    metodo = st.radio("Origen:", ["Subir Foto", "Link Solo Deportes"])
    img_prenda = None
    if metodo == "Link Solo Deportes":
        url = st.text_input("Link aquí:")
        if url:
            img_prenda = scrap_solo_deportes(url)
    else:
        f_prenda = st.file_uploader("Foto prenda", type=['jpg', 'jpeg', 'png'])
        if f_prenda: img_prenda = preparar_imagen(f_prenda)
    if img_prenda: st.image(img_prenda, width=150)

with col2:
    st.subheader("2. Tu Foto")
    f_user = st.file_uploader("Tu foto", type=['jpg', 'jpeg', 'png'])
    img_usuario = None
    if f_user:
        img_usuario = preparar_imagen(f_user)
        st.image(img_usuario, width=150)

# --- 5. GENERACIÓN CON FILTROS DESACTIVADOS ---
st.divider()

if st.button("🚀 GENERAR RESULTADO FINAL"):
    if not img_prenda or not img_usuario:
        st.error("Cargá ambas fotos.")
    else:
        with st.spinner("Procesando prenda..."):
            try:
                orig_w, orig_h = img_usuario.size
                
                prompt = (
                    "Photo-realistic clothing swap. Take the exact garment from the second image "
                    "and place it on the person in the first image. "
                    "Maintain the person's face, pose, and the background exactly. "
                    "Ensure the new shirt fits the person's body shape naturally."
                )

                # CONFIGURACIÓN DE SEGURIDAD: Desactivamos bloqueos por marcas/logos
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

                if response.candidates and response.candidates[0].content.parts:
                    img_data = response.candidates[0].content.parts[0].inline_data.data
                    resultado = PIL.Image.open(io.BytesIO(img_data))
                    resultado = resultado.resize((orig_w, orig_h), PIL.Image.Resampling.LANCZOS)
                    st.success("¡Completado!")
                    st.image(resultado, use_container_width=True)
                else:
                    st.error("La IA aún bloquea el contenido. Intentá con una foto donde no se vea el logo tan de cerca.")

            except Exception as e:
                st.error(f"Error: {str(e)}")
