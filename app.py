import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import PIL.Image
import PIL.ImageOps
import io

# 1. CONFIGURACIÓN VISUAL (Mantenemos fondo oscuro y letras blancas)
st.set_page_config(page_title="Probador Virtual Pro", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    h1, h2, h3, p, label, .stMarkdown, span { color: #FFFFFF !important; }
    .stTextInput input { color: #000000 !important; }
    div.stButton > button {
        background-color: #0082C9; color: white; width: 100%; font-weight: bold; border: none;
    }
    </style>
""", unsafe_allow_html=True)

st.title("👕 Probador Virtual Pro")

# 2. CONFIGURACIÓN API (Usando la librería más estable)
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    api_key = st.text_input("Ingresa tu Gemini API Key:", type="password")
    if not api_key: st.stop()

genai.configure(api_key=api_key)

# 3. FUNCIONES (Mantenemos corrección de rotación)
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

# 4. INTERFAZ DE USUARIO
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. La Prenda")
    metodo = st.radio("Cargar desde:", ["Link Solo Deportes", "Subir Foto"])
    img_prenda = None
    if metodo == "Link Solo Deportes":
        url = st.text_input("Link del producto:")
        if url:
            img_prenda = scrap_solo_deportes(url)
            if not img_prenda: st.warning("No se pudo obtener la imagen del link.")
    else:
        f_prenda = st.file_uploader("Foto de la prenda", type=['jpg', 'png', 'jpeg'])
        if f_prenda: img_prenda = preparar_foto(f_prenda)
    
    if img_prenda: st.image(img_prenda, width=150)

with col2:
    st.subheader("2. Tu Foto")
    f_usuario = st.file_uploader("Tu foto de cuerpo entero", type=['jpg', 'png', 'jpeg'])
    img_usuario = None
    if f_usuario:
        img_usuario = preparar_foto(f_usuario)
        st.image(img_usuario, width=150)

# 5. GENERACIÓN (Lógica blindada contra errores 404)
st.divider()

if st.button("🚀 GENERAR PRUEBA"):
    if not img_prenda or not img_usuario:
        st.error("Faltan imágenes para procesar.")
    else:
        with st.spinner("La IA está trabajando..."):
            try:
                # Usamos el modelo con la nomenclatura de la librería clásica
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # Guardamos dimensiones originales
                w, h = img_usuario.size
                
                prompt = (
                    "Virtual Try-on: Take the clothing from the second image and place it "
                    "on the person in the first image. Keep the person's identity, pose, "
                    "and background identical. Output only the resulting image."
                )

                # Llamada a la API (Formato clásico)
                response = model.generate_content([prompt, img_usuario, img_prenda])
                
                # En esta librería, las imágenes se extraen así:
                if response.candidates:
                    # Buscamos la parte que contiene la imagen
                    img_result = None
                    for part in response.candidates[0].content.parts:
                        if part.inline_data:
                            img_result = PIL.Image.open(io.BytesIO(part.inline_data.data))
                            break
                    
                    if img_result:
                        # Redimensionamos al tamaño original para evitar deformación
                        img_result = img_result.resize((w, h), PIL.Image.Resampling.LANCZOS)
                        st.success("¡Listo!")
                        st.image(img_result, use_container_width=True)
                    else:
                        st.error("La IA no devolvió una imagen (posible filtro de seguridad por logos/marcas).")
                else:
                    st.error("No se pudo generar el resultado.")

            except Exception as e:
                st.error(f"Error técnico: {str(e)}")
