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
st.markdown("<style>.stApp { background-color: #0E1117; color: white; }</style>", unsafe_allow_html=True)
st.title("👕 Probador Virtual Pro")

# --- 2. CONEXIÓN (Secrets de Streamlit) ---
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    st.error("Configurá GEMINI_API_KEY en los Secrets de Streamlit.")
    st.stop()

client = genai.Client(api_key=api_key)

# --- 3. FUNCIONES ---
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
    except: return None
    return None

# --- 4. INTERFAZ ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("1. La Prenda")
    metodo = st.radio("Origen:", ["Subir Manual", "Link Solo Deportes"])
    img_prenda = None
    if metodo == "Link Solo Deportes":
        url = st.text_input("Link de la prenda:")
        if url: img_prenda = scrap_solo_deportes(url)
    else:
        f = st.file_uploader("Foto de prenda", type=['jpg', 'png', 'jpeg'])
        if f: img_prenda = preparar_foto(f)
    if img_prenda: st.image(img_prenda, width=150)

with col2:
    st.subheader("2. Tu Foto")
    f_u = st.file_uploader("Tu foto", type=['jpg', 'png', 'jpeg'])
    img_usuario = None
    if f_u:
        img_usuario = preparar_foto(f_u)
        st.image(img_usuario, width=150)

# --- 5. GENERACIÓN ---
st.divider()
if st.button("🚀 GENERAR RESULTADO FINAL"):
    if not img_prenda or not img_usuario:
        st.error("Cargá ambas fotos primero.")
    else:
        with st.spinner("La IA está creando tu imagen..."):
            try:
                # Prompt directo y potente
                prompt = (
                    "PHOTOREALISTIC VIRTUAL TRY-ON. Replace the person's shirt in the first image "
                    "with the exact garment from the second image. Keep the face, background, "
                    "and body pose identical. Ensure the new shirt fits the person naturally."
                )

                # CONFIGURACIÓN DE SEGURIDAD PARA GEMINI 2.0 (Evita bloqueos de logos)
                safety_settings = [
                    types.SafetySetting(category="HATE_SPEECH", threshold="OFF"),
                    types.SafetySetting(category="HARASSMENT", threshold="OFF"),
                    types.SafetySetting(category="SEXUALLY_EXPLICIT", threshold="OFF"),
                    types.SafetySetting(category="DANGEROUS_CONTENT", threshold="OFF"),
                ]

                # Llamada al modelo estable
                response = client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=[prompt, img_usuario, img_prenda],
                    config=types.GenerateContentConfig(
                        safety_settings=safety_settings
                    )
                )

                # Procesamiento de la imagen resultante
                if response.candidates and response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        if part.inline_data:
                            resultado = PIL.Image.open(io.BytesIO(part.inline_data.data))
                            st.success("¡Imagen generada con éxito!")
                            st.image(resultado, use_container_width=True)
                            st.stop()
                
                st.error("La IA no pudo procesar esta prenda específica. Intentá con una foto más clara.")

            except Exception as e:
                st.error(f"Error técnico: {str(e)}")
