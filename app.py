import streamlit as st
import requests
from bs4 import BeautifulSoup
import PIL.Image
import io
from google import genai

# 1. Configuración de página
st.set_page_config(page_title="Probador Virtual", page_icon="👕")

# 2. Título Actualizado
st.title("👕 PROBADOR VIRTUAL")
st.markdown("---")

# 3. Conexión Silenciosa (Usa el Secret que ya configuraste)
try:
    api_key_interna = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key_interna)
except Exception:
    st.error("⚠️ Configuración incompleta en Secrets.")
    st.stop()

# 4. Interfaz para el usuario (Sin sidebar de clave)
url_producto = st.text_input("1. Pegá el link de la prenda aquí:")
foto_usuario = st.file_uploader("2. Subí tu foto 📸", type=['jpg', 'png', 'jpeg'])

if st.button("Ver cómo me queda 😎"):
    if not url_producto or not foto_usuario:
        st.error("Por favor, completá ambos pasos.")
    else:
        try:
            with st.spinner("🪄 Procesando..."):
                # Lógica de scraping
                res = requests.get(url_producto, headers={'User-Agent': 'Mozilla/5.0'})
                soup = BeautifulSoup(res.text, 'html.parser')
                img_url = soup.find("meta", property="og:image")['content']
                img_prenda = PIL.Image.open(io.BytesIO(requests.get(img_url).content))
                
                # Nombre real del producto
                h1 = soup.find("h1")
                titulo = h1.text.strip().lower() if h1 else "prenda"
                prompt_n = f"Extrae el nombre del objeto (una palabra) de: {titulo}"
                nombre_obj = client.models.generate_content(model='gemini-2.0-flash', contents=[prompt_n]).text.strip().lower()

                # Generación
                img_user = PIL.Image.open(foto_usuario)
                instruccion = f"Sustituye la prenda del usuario por la {nombre_obj} de la Imagen 2. Mantén marca y color."
                
                resultado = client.models.generate_content(
                    model='gemini-2.5-flash-image',
                    contents=[instruccion, img_user, img_prenda]
                )
                
                # Entrega final
                for part in resultado.candidates[0].content.parts:
                    if part.inline_data:
                        st.image(PIL.Image.open(io.BytesIO(part.inline_data.data)))
                        st.balloons() # ¡Efecto de globos para celebrar!
                
                st.success(f"🔥 ¡Esa {nombre_obj} te queda espectacular!")
                        
        except Exception:
            st.error("No pudimos leer este producto. Probá con otro link.")

st.caption("Nota: Representación por IA con fines ilustrativos.")
