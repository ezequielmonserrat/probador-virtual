import streamlit as st
import requests
from bs4 import BeautifulSoup
import PIL.Image
import PIL.ImageOps
import io
from google import genai

# --- 1. CONFIGURACIÓN E INTERFAZ LIMPIA ---
st.set_page_config(page_title="Probador Virtual 2.0", layout="centered")

# Estilos CSS para ocultar elementos molestos y mejorar botones
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    div.stButton > button {
        background-color: #0082C9; color: white; width: 100%; 
        border-radius: 8px; font-weight: bold; padding: 0.5rem;
    }
    div.stButton > button:hover { background-color: #005f9e; }
    </style>
""", unsafe_allow_html=True)

st.title("👕 Probador Virtual: Reset")

# --- 2. GESTIÓN DE API KEY ---
# Intentamos leer de secrets, si no, pedimos input (para facilitar pruebas)
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    api_key = st.text_input("Ingresa tu Gemini API Key:", type="password")

if not api_key:
    st.warning("⚠️ Necesitas una API Key para continuar.")
    st.stop()

client = genai.Client(api_key=api_key)

# --- 3. FUNCIONES ROBUSTAS (El corazón del arreglo) ---

def corregir_orientacion(imagen):
    """Evita que las fotos de celular salgan rotadas."""
    return PIL.ImageOps.exif_transpose(imagen)

def obtener_imagen_desde_url(url):
    """Intenta descargar imagen simulando ser un navegador real."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # Lanza error si es 404 o 403
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Estrategia: Buscar solo OpenGraph (el estándar más seguro)
        meta_img = soup.find("meta", property="og:image")
        
        if meta_img and meta_img.get("content"):
            img_url = meta_img["content"]
            # Descargar la imagen final
            img_resp = requests.get(img_url, headers=headers, timeout=10)
            return PIL.Image.open(io.BytesIO(img_resp.content))
        else:
            return None # No encontró etiqueta, devolvemos None limpiamente
            
    except Exception as e:
        print(f"Error scraping: {e}")
        return None # Cualquier error de red, devolvemos None

# --- 4. INTERFAZ DE USUARIO ---

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. La Prenda")
    metodo = st.radio("Fuente:", ["Subir Foto (Recomendado)", "Link Solo Deportes"])
    
    img_prenda = None
    
    if metodo == "Link Solo Deportes":
        url = st.text_input("Pega el link aquí:")
        if url:
            with st.spinner("Buscando imagen en la web..."):
                img_prenda = obtener_imagen_desde_url(url)
                if img_prenda is None:
                    st.error("❌ No pudimos sacar la foto del link automáticamente (seguridad de la web). Por favor, descargá la foto y usá la opción 'Subir Foto'.")
    else:
        uploaded_prenda = st.file_uploader("Sube la foto de la ropa", type=["jpg", "png", "jpeg"])
        if uploaded_prenda:
            img_prenda = PIL.Image.open(uploaded_prenda)

    if img_prenda:
        st.image(img_prenda, caption="Prenda seleccionada", width=150)

with col2:
    st.subheader("2. Tu Foto")
    uploaded_user = st.file_uploader("Sube tu foto de cuerpo entero", type=["jpg", "png", "jpeg"])
    img_usuario = None
    if uploaded_user:
        # CORRECCIÓN 1: Arreglar rotación al cargar
        img_usuario = corregir_orientacion(PIL.Image.open(uploaded_user))
        st.image(img_usuario, caption="Tu foto", width=150)

# --- 5. LÓGICA DE GENERACIÓN ---

if st.button("✨ GENERAR PRUEBA"):
    if not img_prenda or not img_usuario:
        st.error("Faltan imágenes. Asegúrate de tener la prenda y tu foto cargadas.")
    else:
        with st.spinner("La IA está trabajando... (esto puede tardar unos 15 seg)"):
            try:
                # CORRECCIÓN 2: Guardar dimensiones originales
                orig_w, orig_h = img_usuario.size
                
                # Prompt enfocado en mantener estructura
                prompt = (
                    "Virtual Try-On task. "
                    "Replace the clothes of the person in the first image with the garment in the second image. "
                    "Keep the background, the person's pose, and the image aspect ratio exactly the same. "
                    "Output a realistic photo."
                )

                response = client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=[prompt, img_usuario, img_prenda]
                )

                # Validación de seguridad de respuesta
                if not response.candidates:
                    st.error("La IA bloqueó la generación por motivos de seguridad o no devolvió nada.")
                    st.stop()

                # Procesar salida
                generated_data = response.candidates[0].content.parts[0].inline_data.data
                final_img = PIL.Image.open(io.BytesIO(generated_data))

                # CORRECCIÓN 3: Forzar el tamaño original (Adiós deformación)
                final_img = final_img.resize((orig_w, orig_h), PIL.Image.Resampling.LANCZOS)

                st.success("¡Listo!")
                st.image(final_img, caption="Resultado Final", use_container_width=True)

            except Exception as e:
                st.error(f"Ocurrió un error técnico: {str(e)}")
