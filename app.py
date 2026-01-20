import streamlit as st
import requests
from bs4 import BeautifulSoup
import PIL.Image
import PIL.ImageOps
import io
from google import genai

# --- 1. CONFIGURACIÓN E INTERFAZ VISUAL ---
st.set_page_config(page_title="Probador Virtual", layout="centered")

# CSS CORREGIDO: Forzamos MODO OSCURO (Fondo Negro / Letras Blancas)
st.markdown("""
    <style>
    /* 1. Fondo General negro */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    
    /* 2. Forzar color de textos, títulos y etiquetas */
    h1, h2, h3, h4, p, label, .stMarkdown {
        color: #FAFAFA !important;
    }
    
    /* 3. Estilo de los Radio Buttons (Opciones) */
    .stRadio > label {
        color: #FAFAFA !important;
    }
    
    /* 4. Inputs de texto (para que se vea lo que escribís) */
    .stTextInput input {
        color: #333333;
        background-color: #FAFAFA;
    }

    /* 5. Botón Principal */
    div.stButton > button {
        background-color: #0082C9; 
        color: white; 
        width: 100%; 
        border-radius: 8px; 
        font-weight: bold; 
        padding: 0.5rem;
        border: 1px solid #0082C9;
    }
    div.stButton > button:hover { 
        background-color: #005f9e; 
        border-color: #005f9e;
    }
    </style>
""", unsafe_allow_html=True)

st.title("👕 Probador Virtual")
st.markdown("---")

# --- 2. GESTIÓN DE API KEY ---
try:
    # Intenta leer de secrets
    api_key = st.secrets.get("GEMINI_API_KEY")
except:
    api_key = None

# Si no está en secrets, pedirla en pantalla
if not api_key:
    st.info("ℹ️ Configuración: Ingresa tu API Key para empezar.")
    api_key = st.text_input("Gemini API Key:", type="password")

if not api_key:
    st.stop() # Detiene la app hasta que haya clave

client = genai.Client(api_key=api_key)

# --- 3. FUNCIONES ---

def corregir_orientacion(imagen):
    """Evita que las fotos de celular salgan rotadas."""
    return PIL.ImageOps.exif_transpose(imagen)

def obtener_imagen_desde_url(url):
    """Descarga imagen simulando navegador."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Busca metaetiqueta OpenGraph (og:image)
        meta_img = soup.find("meta", property="og:image")
        
        if meta_img and meta_img.get("content"):
            img_url = meta_img["content"]
            img_resp = requests.get(img_url, headers=headers, timeout=10)
            return PIL.Image.open(io.BytesIO(img_resp.content))
        return None 
    except:
        return None

# --- 4. INTERFAZ DE USUARIO (COLUMNAS) ---

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. La Prenda")
    metodo = st.radio("Fuente de la ropa:", ["Subir Foto Manual", "Link Solo Deportes"])
    
    img_prenda = None
    
    if metodo == "Link Solo Deportes":
        url = st.text_input("Pegá el link del producto:")
        if url:
            with st.spinner("Buscando foto..."):
                img_prenda = obtener_imagen_desde_url(url)
                if not img_prenda:
                    st.error("🔒 Web protegida. Descargá la foto y usá la opción 'Subir Foto Manual'.")
    else:
        uploaded_prenda = st.file_uploader("Sube foto de la ropa (JPG/PNG)", type=["jpg", "png", "jpeg"])
        if uploaded_prenda:
            img_prenda = PIL.Image.open(uploaded_prenda)

    if img_prenda:
        st.image(img_prenda, caption="Prenda lista", width=150)

with col2:
    st.subheader("2. Tu Foto")
    uploaded_user = st.file_uploader("Sube tu foto de cuerpo entero", type=["jpg", "png", "jpeg"])
    img_usuario = None
    if uploaded_user:
        # CORRECCIÓN ROTACIÓN
        img_usuario = corregir_orientacion(PIL.Image.open(uploaded_user))
        st.image(img_usuario, caption="Tu foto lista", width=150)

# --- 5. BOTÓN Y GENERACIÓN ---

st.markdown("---")

if st.button("✨ GENERAR PRUEBA AHORA"):
    if not img_prenda or not img_usuario:
        st.warning("⚠️ Faltan datos: Asegurate de cargar la prenda y tu foto.")
    else:
        with st.spinner("Procesando... (Manteniendo tamaño original)"):
            try:
                # 1. Medimos tu foto original
                orig_w, orig_h = img_usuario.size
                
                # 2. Prompt estricto
                prompt = (
                    "Virtual Try-On task. "
                    "Replace the clothes of the person in the first image with the garment in the second image. "
                    "Keep the background, the person's pose, and the image aspect ratio exactly the same. "
                    "Output a realistic photo."
                )

                # 3. Llamada a IA
                response = client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=[prompt, img_usuario, img_prenda]
                )

                if not response.candidates:
                    st.error("La IA no devolvió resultado. Intenta con otra foto.")
                else:
                    # 4. Procesar y redimensionar
                    generated_data = response.candidates[0].content.parts[0].inline_data.data
                    final_img = PIL.Image.open(io.BytesIO(generated_data))
                    
                    # 5. EL PASO CRÍTICO: Volver al tamaño exacto de tu foto
                    final_img = final_img.resize((orig_w, orig_h), PIL.Image.Resampling.LANCZOS)

                    st.success("¡Prueba completada!")
                    st.image(final_img, caption="Resultado Final", use_container_width=True)

            except Exception as e:
                st.error(f"Error técnico: {str(e)}")
