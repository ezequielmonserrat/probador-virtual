import streamlit as st
import requests
from bs4 import BeautifulSoup
import PIL.Image
import PIL.ImageOps
import io
from google import genai

# --- 1. CONFIGURACIÓN DE PÁGINA (SIEMPRE PRIMERO) ---
st.set_page_config(page_title="Probador Virtual Estable", layout="centered")

# CSS para asegurar legibilidad (Fondo Oscuro / Letras Blancas)
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

st.title("👕 Probador Virtual: Versión Estable")

# --- 2. CONFIGURACIÓN API ---
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    api_key = st.text_input("Ingresa tu Gemini API Key:", type="password")
    if not api_key:
        st.stop()

# Inicializamos el cliente
client = genai.Client(api_key=api_key)

# --- 3. FUNCIONES DE PROCESAMIENTO ---

def procesar_imagen(file):
    """Carga la imagen y arregla la rotación de celulares."""
    img = PIL.Image.open(file)
    return PIL.ImageOps.exif_transpose(img)

def obtener_prenda_url(url):
    """Extrae imagen de Solo Deportes de forma segura."""
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        meta = soup.find("meta", property="og:image")
        if meta and meta.get("content"):
            img_data = requests.get(meta["content"], headers=headers).content
            return PIL.Image.open(io.BytesIO(img_data))
    except:
        return None
    return None

# --- 4. INTERFAZ ---

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. La Prenda")
    fuente = st.radio("Fuente:", ["Archivo local", "Link Solo Deportes"])
    img_prenda = None
    if fuente == "Archivo local":
        f = st.file_uploader("Subir remera", type=['jpg', 'jpeg', 'png'], key="prenda")
        if f: img_prenda = procesar_imagen(f)
    else:
        url = st.text_input("Link del producto:")
        if url:
            img_prenda = obtener_prenda_url(url)
            if not img_prenda:
                st.warning("No se pudo extraer la imagen. Intentá subirla manualmente.")

    if img_prenda:
        st.image(img_prenda, width=150, caption="Remera detectada")

with col2:
    st.subheader("2. Tu Foto")
    f_user = st.file_uploader("Subir tu foto", type=['jpg', 'jpeg', 'png'], key="usuario")
    img_usuario = None
    if f_user:
        img_usuario = procesar_imagen(f_user)
        st.image(img_usuario, width=150, caption="Tu foto lista")

# --- 5. GENERACIÓN ---

st.divider()

if st.button("✨ VER RESULTADO"):
    if not img_prenda or not img_usuario:
        st.error("Por favor, cargá ambas imágenes.")
    else:
        with st.spinner("Generando..."):
            try:
                # Guardamos tamaño original para evitar deformación
                w, h = img_usuario.size
                
                # Nombre de modelo corregido para evitar el Error 404
                # 'gemini-1.5-flash' es el más compatible universalmente
                model_name = "gemini-1.5-flash" 
                
                prompt = (
                    "Act as a professional fashion photographer. "
                    "Take the garment from the second image and put it on the person in the first image. "
                    "Keep the person's pose, face, and background exactly the same. "
                    "Adjust the garment to fit the body naturally. Output only the image."
                )

                response = client.models.generate_content(
                    model=model_name,
                    contents=[prompt, img_usuario, img_prenda]
                )

                if response.candidates and response.candidates[0].content.parts:
                    img_raw = response.candidates[0].content.parts[0].inline_data.data
                    resultado = PIL.Image.open(io.BytesIO(img_raw))
                    
                    # Forzamos el tamaño original para que NO se vea estirada o rotada
                    resultado = resultado.resize((w, h), PIL.Image.Resampling.LANCZOS)
                    
                    st.success("¡Listo!")
                    st.image(resultado, use_container_width=True)
                else:
                    st.error("La IA no devolvió una imagen. Intentá con fotos más claras o sin logos grandes.")

            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.info("Nota: Si ves un error 404, es posible que tu API Key no tenga acceso a este modelo específico.")
