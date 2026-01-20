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
        background-color: #0082C9; color: white; width: 100%; font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

st.title("👕 Probador Virtual Pro")

# --- 2. CONFIGURACIÓN DE API (CLAVE INTEGRADA) ---
# He vuelto a poner tu clave aquí para que el código funcione directamente
api_key = "AIzaSyD..." # Aquí va la clave que me pasaste anteriormente
client = genai.Client(api_key=api_key)

# --- 3. FUNCIONES DE PROCESAMIENTO ---
def preparar_imagen(archivo):
    """Carga y corrige la orientación de las fotos de celular (EXIF)."""
    img = PIL.Image.open(archivo)
    return PIL.ImageOps.exif_transpose(img)

def scrap_solo_deportes(url):
    """Extrae imagen de Solo Deportes de forma segura."""
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
        url = st.text_input("Link de la prenda aquí:")
        if url:
            img_prenda = scrap_solo_deportes(url)
    else:
        f_prenda = st.file_uploader("Subir foto de la prenda", type=['jpg', 'jpeg', 'png'])
        if f_prenda: img_prenda = preparar_imagen(f_prenda)
    
    if img_prenda: st.image(img_prenda, width=150, caption="Prenda lista")

with col2:
    st.subheader("2. Tu Foto")
    f_user = st.file_uploader("Subir tu foto de frente", type=['jpg', 'jpeg', 'png'])
    img_usuario = None
    if f_user:
        img_usuario = preparar_imagen(f_user)
        st.image(img_usuario, width=150, caption="Tu foto lista")

# --- 5. GENERACIÓN ---
st.divider()

if st.button("🚀 GENERAR RESULTADO FINAL"):
    if not img_prenda or not img_usuario:
        st.error("Por favor, cargá ambas imágenes.")
    else:
        with st.spinner("Procesando... La IA está cambiando la prenda."):
            try:
                # Guardamos el tamaño de tu foto original
                orig_w, orig_h = img_usuario.size
                
                prompt = (
                    "Photo-realistic clothing swap. Take the exact garment from the second image "
                    "and place it on the person in the first image. "
                    "Maintain the person's face, identity, pose, and background exactly the same. "
                    "Adjust the shirt to the person's body shape naturally."
                )

                # Desactivamos filtros para que no bloquee logos de fútbol
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
                    
                    # Forzamos a que el resultado tenga el tamaño de tu foto original
                    resultado = resultado.resize((orig_w, orig_h), PIL.Image.Resampling.LANCZOS)
                    
                    st.success("¡Imagen generada con éxito!")
                    st.image(resultado, use_container_width=True)
                else:
                    st.error("La IA declinó la imagen. Si es una camiseta con muchos logos, probá con una foto más lejana.")

            except Exception as e:
                st.error(f"Error: {str(e)}")
