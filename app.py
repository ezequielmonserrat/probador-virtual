import streamlit as st
import requests
from bs4 import BeautifulSoup
import PIL.Image
import io
from google import genai

# Configuración de página
st.set_page_config(page_title="Probador Virtual AI", page_icon="👕")

# Título actualizado
st.title("👕 Probador Virtual Inteligente")
st.markdown("---")

# --- CONEXIÓN SEGURA A LA API (Oculta para el usuario) ---
# Intentamos obtener la clave de los Secrets de Streamlit
try:
    api_key_interna = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key_interna)
except Exception:
    st.error("⚠️ Error de configuración: API Key no encontrada en Secrets.")
    st.stop()

# Campos de entrada limpios (Ya no pedimos la clave aquí)
url_producto = st.text_input("1. Pegá el link de la prenda que te gusta:")
foto_usuario = st.file_uploader("2. Subí tu foto 📸", type=['jpg', 'png', 'jpeg'])

if st.button("Ver cómo me queda 😎"):
    if not url_producto or not foto_usuario:
        st.error("¡Ups! Cargá el link y tu foto para empezar.")
    else:
        try:
            with st.spinner("🪄 Preparando tu prenda..."):
                # Scraping del producto
                res = requests.get(url_producto, headers={'User-Agent': 'Mozilla/5.0'})
                soup = BeautifulSoup(res.text, 'html.parser')
                img_url = soup.find("meta", property="og:image")['content']
                img_prenda = PIL.Image.open(io.BytesIO(requests.get(img_url).content))
                
                # Identificación precisa (Anti-Marca)
                h1 = soup.find("h1")
                titulo_raw = h1.text.strip().lower() if h1 else "prenda"
                prompt_nombre = f"Extrae solo el nombre del objeto (remera, camiseta, etc) de: '{titulo_raw}'"
                nombre_obj = client.models.generate_content(model='gemini-2.0-flash', contents=[prompt_nombre]).text.strip().lower()

                # Generación de alta fidelidad
                img_user = PIL.Image.open(foto_usuario)
                instruccion = f"Sustituye la ropa del usuario por la {nombre_obj} de la Imagen 2. Mantén color y marca exactos."
                
                resultado = client.models.generate_content(
                    model='gemini-2.5-flash-image',
                    contents=[instruccion, img_user, img_prenda]
                )
                
                # Resultado final motivador
                for part in resultado.candidates[0].content.parts:
                    if part.inline_data:
                        final_img = PIL.Image.open(io.BytesIO(part.inline_data.data))
                        st.image(final_img, caption=f"🔥 ¡Esa {nombre_obj} te queda espectacular!")
                        
        except Exception:
            st.error("⚠️ No pudimos procesar este link. Intentá con otro producto.")

st.info("Nota: Esta es una simulación por IA con fines ilustrativos.")
