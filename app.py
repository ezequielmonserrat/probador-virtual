import streamlit as st
import requests
from bs4 import BeautifulSoup
import PIL.Image
import PIL.ImageOps
import io
import google.generativeai as genai # Usamos el motor principal

# --- 1. CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title="Probador Virtual Pro", layout="centered")
st.markdown("<style>.stApp { background-color: #0E1117; color: white; }</style>", unsafe_allow_html=True)
st.title("👕 Probador Virtual Pro")

# --- 2. CONEXIÓN SEGURA ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Falta la clave API en Secrets.")
    st.stop()

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
        url = st.text_input("Link:")
        if url: img_prenda = scrap_solo_deportes(url)
    else:
        f = st.file_uploader("Prenda", type=['jpg', 'png', 'jpeg'])
        if f: img_prenda = preparar_foto(f)
    if img_prenda: st.image(img_prenda, width=150)

with col2:
    st.subheader("2. Tu Foto")
    f_u = st.file_uploader("Tu foto", type=['jpg', 'png', 'jpeg'])
    img_usuario = None
    if f_u:
        img_usuario = preparar_foto(f_u)
        st.image(img_usuario, width=150)

# --- 5. GENERACIÓN CON FILTROS DESACTIVADOS ---
st.divider()
if st.button("🚀 GENERAR PRUEBA AHORA"):
    if not img_prenda or not img_usuario:
        st.error("Cargá ambas fotos.")
    else:
        with st.spinner("Cambiando prenda..."):
            try:
                # Configuramos el modelo para que IGNORE los filtros de seguridad
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                safety_settings = [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                ]

                prompt = (
                    "Photo-realistic clothing swap. "
                    "Take the garment from the second image and put it on the person in the first image. "
                    "Keep the face, pose, and background exactly the same. Fit the shirt to the body shape."
                )
                
                response = model.generate_content(
                    [prompt, img_usuario, img_prenda],
                    safety_settings=safety_settings
                )

                # Si la IA funcionó, nos devuelve la imagen en el primer 'part'
                if response.candidates:
                    # Intentamos buscar si hay una imagen en la respuesta
                    # (Nota: Algunos modelos devuelven la imagen directamente)
                    st.success("¡Imagen generada!")
                    # Mostramos el resultado (el modelo 1.5 a veces requiere un manejo distinto de bytes)
                    try:
                        st.write(response.text) # Si es texto con descripción
                    except:
                        st.image(response.candidates[0].content.parts[0].inline_data.data)
                
            except Exception as e:
                st.error(f"Error de la IA: {str(e)}")
                st.info("Si el error persiste, probá con una prenda que no tenga logos de marcas famosas.")
