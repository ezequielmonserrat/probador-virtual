import streamlit as st
import requests
from bs4 import BeautifulSoup
import PIL.Image
import PIL.ImageOps
import io
from google import genai

# Configuración y Limpieza de Interfaz
st.set_page_config(page_title="Probador Virtual Pro", page_icon="👕", layout="centered")

st.markdown("""
    <style>
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp { background-color: #FFFFFF; }
    div.stButton > button:first-child {
        background-color: #0082C9; color: white; border: none; width: 100%; font-weight: bold; border-radius: 4px;
    }
    div.stButton > button:first-child:hover { background-color: #E30052; }
    </style>
    """, unsafe_allow_html=True)

st.title("👕 PROBADOR VIRTUAL")
st.markdown("<p style='color: #666;'>Probador de alta precisión para E-commerce</p>", unsafe_allow_html=True)

try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception:
    st.error("Error: Revisa tu GEMINI_API_KEY en los Secrets.")
    st.stop()

# Historial para comparar pruebas
if 'historial' not in st.session_state:
    st.session_state.historial = []

url_producto = st.text_input("1. Link del producto exacto:")
foto_usuario = st.file_uploader("2. Foto del usuario 📸", type=['jpg', 'png', 'jpeg'])

if st.button("GENERAR PRUEBA FIEL"):
    if not url_producto or not foto_usuario:
        st.error("Por favor completa los campos.")
    else:
        try:
            with st.spinner("📦 Obteniendo diseño original y procesando..."):
                # 1. Scraping Avanzado: Buscamos la imagen real del producto
                headers = {'User-Agent': 'Mozilla/5.0'}
                res = requests.get(url_producto, headers=headers)
                soup = BeautifulSoup(res.text, 'html.parser')
                
                # Buscamos la imagen principal del producto con prioridad
                img_src = None
                meta_img = soup.find("meta", property="og:image") or soup.find("meta", name="twitter:image")
                if meta_img:
                    img_src = meta_img['content']
                
                if not img_src:
                    st.error("No pudimos extraer la imagen de este sitio.")
                    st.stop()
                
                img_prenda = PIL.Image.open(io.BytesIO(requests.get(img_src).content))
                
                # 2. Procesar usuario y detectar su orientación
                img_user_raw = PIL.Image.open(foto_usuario)
                img_user = PIL.ImageOps.exif_transpose(img_user_raw)
                ancho_u, alto_u = img_user.size

                # 3. PROMPT DE ALTA FIDELIDAD
                # Aquí obligamos a la IA a ignorar sus sesgos y copiar la Imagen 2.
                instruccion = (
                    "TAREA: Reemplazo de prenda con fidelidad absoluta. "
                    "Imagen 1: Persona usuaria. Imagen 2: Prenda de referencia. "
                    "INSTRUCCIÓN CRÍTICA: Ignora cualquier diseño preexistente que conozcas. "
                    "Copia EXACTAMENTE el diseño, los logos, la posición de las tiras, el escudo y el sponsor de la Imagen 2. "
                    "La prenda final debe ser un clon visual de la Imagen 2 adaptado al cuerpo de la Imagen 1. "
                    "Respeta la iluminación y las sombras naturales."
                )
                
                resultado = client.models.generate_content(
                    model='gemini-2.5-flash-image',
                    contents=[instruccion, img_user, img_prenda]
                )
                
                # 4. Entrega y Corrección Dinámica de Rotación
                for part in resultado.candidates[0].content.parts:
                    if part.inline_data:
                        final_img = PIL.Image.open(io.BytesIO(part.inline_data.data))
                        final_img = PIL.ImageOps.exif_transpose(final_img)
                        
                        # Si el usuario subió vertical y la IA devolvió horizontal, forzamos giro
                        if alto_u > ancho_u and final_img.width > final_img.height:
                            final_img = final_img.rotate(-90, expand=True)
                        
                        st.image(final_img, use_container_width=True)
                        st.session_state.historial.append(final_img)
                        st.balloons()
                        
        except Exception as e:
            st.error(f"Error técnico: {e}")

# Sección de historial
if st.session_state.historial:
    st.markdown("---")
    st.subheader("🕒 Tus últimas pruebas")
    cols = st.columns(3)
    for idx, img in enumerate(reversed(st.session_state.historial[-3:])):
        cols[idx % 3].image(img, use_container_width=True)

st.markdown("<br><center><small>Probador Virtual Independiente</small></center>", unsafe_allow_html=True)
