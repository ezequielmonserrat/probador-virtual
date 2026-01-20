import streamlit as st
import requests
from bs4 import BeautifulSoup
import PIL.Image
import PIL.ImageOps
import io
from google import genai

# --- 1. CONFIGURACIÓN VISUAL (Mantiene fondo oscuro y legibilidad) ---
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

# Usamos el cliente moderno que es el más estable en Streamlit
client = genai.Client(api_key=api_key)

# --- 3. FUNCIONES (Solución definitiva a la rotación) ---
def preparar_imagen(archivo):
    """Carga y corrige la orientación de las fotos de celular."""
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
            img_url = meta["content"]
            img_data = requests.get(img_url, headers=headers).content
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
            if not img_prenda: st.warning("Error al cargar link.")
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

# --- 5. GENERACIÓN (Lógica blindada contra deformación y errores) ---
st.divider()

if st.button("🚀 GENERAR RESULTADO FINAL"):
    if not img_prenda or not img_usuario:
        st.error("Cargá ambas fotos para continuar.")
    else:
        with st.spinner("Procesando..."):
            try:
                # 1. Medimos dimensiones originales para evitar estiramientos
                orig_w, orig_h = img_usuario.size
                
                # 2. Prompt estricto para edición profesional
                prompt = (
                    "Virtual try-on: Take the clothing from the second image and place it "
                    "on the person in the first image. Keep the person's identity, pose, "
                    "and background identical. Adapt the garment shape to the body. "
                    "Output only the resulting image."
                )

                # 3. Usamos gemini-2.0-flash que es el modelo más avanzado y disponible
                response = client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=[prompt, img_usuario, img_prenda]
                )

                # 4. Extracción segura de la imagen
                if response.candidates and response.candidates[0].content.parts:
                    img_data = response.candidates[0].content.parts[0].inline_data.data
                    resultado = PIL.Image.open(io.BytesIO(img_data))
                    
                    # 5. RE-DIMENSIONADO FINAL (Mantiene relación de aspecto y rotación)
                    resultado = resultado.resize((orig_w, orig_h), PIL.Image.Resampling.LANCZOS)
                    
                    st.success("¡Hecho!")
                    st.image(resultado, use_container_width=True)
                else:
                    st.error("La IA bloqueó la imagen. Probá con fotos sin logos de marcas muy grandes.")

            except Exception as e:
                st.error(f"Ocurrió un error: {str(e)}")
