import streamlit as st
import requests
from bs4 import BeautifulSoup
import PIL.Image
import PIL.ImageOps
import io
from google import genai

# --- 1. IMPORTANTE: EL IMPORT DE ARRIBA DEBE ESTAR PRIMERO ---
# Configuramos la página inmediatamente después de los imports
st.set_page_config(page_title="Probador Virtual Pro", layout="centered")

# CSS para forzar Modo Oscuro y que las letras SIEMPRE se vean
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    label, p, h1, h2, h3 { color: white !important; }
    .stTextInput input { color: black !important; }
    </style>
""", unsafe_allow_html=True)

st.title("👕 Probador Virtual Pro")
st.write("Versión estable con Gemini 1.5 Pro")

# --- 2. CONFIGURACIÓN API ---
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    api_key = st.text_input("Ingresa tu Gemini API Key:", type="password")
    if not api_key:
        st.info("Por favor, ingresa la API Key para continuar.")
        st.stop()

client = genai.Client(api_key=api_key)

# --- 3. FUNCIONES DE APOYO ---

def preparar_imagen(upload):
    """Carga y corrige la rotación automática de la imagen."""
    img = PIL.Image.open(upload)
    return PIL.ImageOps.exif_transpose(img)

def scrap_solo_deportes(url):
    """Extrae la imagen del link de Solo Deportes de forma segura."""
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            meta = soup.find("meta", property="og:image")
            if meta:
                img_url = meta["content"]
                img_data = requests.get(img_url, headers=headers).content
                return PIL.Image.open(io.BytesIO(img_data))
    except:
        pass
    return None

# --- 4. INTERFAZ ---

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. La Prenda")
    tipo_entrada = st.radio("¿Cómo cargarás la ropa?", ["Subir Archivo", "Link de Solo Deportes"])
    
    img_prenda = None
    if tipo_entrada == "Subir Archivo":
        f_prenda = st.file_uploader("Foto de la remera", type=['jpg', 'png', 'jpeg'], key="u1")
        if f_prenda: img_prenda = preparar_imagen(f_prenda)
    else:
        url = st.text_input("Link del producto:")
        if url:
            img_prenda = scrap_solo_deportes(url)
            if not img_prenda:
                st.warning("No se pudo obtener la imagen del link. Probá subiendo el archivo manualmente.")

    if img_prenda:
        st.image(img_prenda, width=150)

with col2:
    st.subheader("2. Tu Foto")
    f_usuario = st.file_uploader("Tu foto de cuerpo entero", type=['jpg', 'png', 'jpeg'], key="u2")
    img_usuario = None
    if f_usuario:
        img_usuario = preparar_imagen(f_usuario)
        st.image(img_usuario, width=150)

# --- 5. PROCESAMIENTO ---

st.divider()

if st.button("🚀 GENERAR RESULTADO", use_container_width=True):
    if not img_prenda or not img_usuario:
        st.error("Faltan imágenes. Por favor cargá ambas.")
    else:
        with st.spinner("La IA está analizando las prendas..."):
            try:
                # Guardamos dimensiones para evitar deformación
                w, h = img_usuario.size
                
                prompt = (
                    "You are a professional fashion editor. "
                    "Task: Take the clothing item from the second image and place it on the person in the first image. "
                    "Instructions: Maintain the exact body pose, face, and background of the first image. "
                    "Make the new garment fit the body realistically. "
                    "The final output must be only the edited image."
                )

                # USAMOS 1.5 PRO para evitar los bloqueos que vimos antes
                response = client.models.generate_content(
                    model='gemini-1.5-pro',
                    contents=[prompt, img_usuario, img_prenda]
                )

                if response.candidates and response.candidates[0].content.parts:
                    img_raw = response.candidates[0].content.parts[0].inline_data.data
                    res_img = PIL.Image.open(io.BytesIO(img_raw))
                    
                    # CORRECCIÓN DE TAMAÑO FINAL
                    res_img = res_img.resize((w, h), PIL.Image.Resampling.LANCZOS)
                    
                    st.success("¡Imagen generada!")
                    st.image(res_img, use_container_width=True)
                else:
                    st.error("La IA no pudo generar el resultado. Esto pasa a veces con logos de marcas famosas.")
            
            except Exception as e:
                st.error(f"Error crítico: {str(e)}")
