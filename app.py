import streamlit as st
import requests
from bs4 import BeautifulSoup
import PIL.Image
import PIL.ImageOps
import io
from google import genai

# --- 1. CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title="Probador Virtual Pro", layout="centered")
st.markdown("<style>.stApp { background-color: #0E1117; color: white; }</style>", unsafe_allow_html=True)
st.title("👕 Probador Virtual Pro")

# --- 2. CONEXIÓN SEGURA ---
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    st.error("Falta la clave GEMINI_API_KEY en Secrets.")
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

# --- 5. GENERACIÓN SIMPLIFICADA (SIN FILTROS MANUALES PARA EVITAR ERRORES) ---
st.divider()
if st.button("🚀 GENERAR PRUEBA AHORA"):
    if not img_prenda or not img_usuario:
        st.error("Cargá ambas fotos.")
    else:
        with st.spinner("Generando..."):
            try:
                # Prompt optimizado para no disparar alertas de seguridad
                prompt = (
                    "Please perform a professional clothing swap. "
                    "Replace the person's upper garment in the first image with the shirt shown in the second image. "
                    "Keep the person's identity and background exactly as they are."
                )
                
                # Llamada ultra-simple: sin configuraciones extra que causen 'INVALID_ARGUMENT'
                response = client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=[prompt, img_usuario, img_prenda]
                )

                if response.text:
                    # Si la respuesta es texto en lugar de imagen, algo falló
                    st.warning("La IA devolvió texto. Intentando extraer imagen...")
                
                # Intentamos capturar la imagen del primer candidato
                if response.candidates:
                    for part in response.candidates[0].content.parts:
                        if part.inline_data:
                            resultado = PIL.Image.open(io.BytesIO(part.inline_data.data))
                            st.success("¡Logrado!")
                            st.image(resultado, use_container_width=True)
                            st.stop()
                
                st.error("No se pudo generar la imagen. Probá con una foto de la prenda con fondo liso.")

            except Exception as e:
                st.error(f"Error técnico: {str(e)}")
