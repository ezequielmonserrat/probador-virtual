import streamlit as st
import requests
from bs4 import BeautifulSoup
import PIL.Image
import PIL.ImageOps # Librería para respetar la orientación
import io
from google import genai

# Configuración de página
st.set_page_config(page_title="Probador Virtual", page_icon="👕")

st.title("👕 PROBADOR VIRTUAL")
st.markdown("---")

# Conexión Segura
try:
    api_key_interna = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key_interna)
except Exception:
    st.error("⚠️ Error: Configurá la API Key en los Secrets.")
    st.stop()

url_producto = st.text_input("1. Pegá el link de la prenda aquí:")
foto_usuario = st.file_uploader("2. Subí tu foto 📸", type=['jpg', 'png', 'jpeg'])

if st.button("Ver cómo me queda 😎"):
    if not url_producto or not foto_usuario:
        st.error("Por favor, completá ambos campos.")
    else:
        try:
            with st.spinner("🪄 Procesando..."):
                # 1. Obtener imagen de la prenda
                res = requests.get(url_producto, headers={'User-Agent': 'Mozilla/5.0'})
                soup = BeautifulSoup(res.text, 'html.parser')
                img_url = soup.find("meta", property="og:image")['content']
                img_prenda = PIL.Image.open(io.BytesIO(requests.get(img_url).content))
                
                # 2. Corregir orientación de la foto del USUARIO antes de mandarla a la IA
                # Esto hace que si la sacaste vertical, la IA la reciba vertical.
                img_user_raw = PIL.Image.open(foto_usuario)
                img_user = PIL.ImageOps.exif_transpose(img_user_raw) 

                # 3. Identificar objeto
                h1 = soup.find("h1")
                titulo = h1.text.strip().lower() if h1 else "prenda"
                prompt_n = f"Extrae el nombre del objeto (una palabra) de: {titulo}"
                nombre_obj = client.models.generate_content(model='gemini-2.0-flash', contents=[prompt_n]).text.strip().lower()

                # 4. Generación
                instruccion = f"Sustituye la prenda del usuario por la {nombre_obj} de la Imagen 2. Mantené la orientación original."
                
                resultado = client.models.generate_content(
                    model='gemini-2.5-flash-image',
                    contents=[instruccion, img_user, img_prenda]
                )
                
                # 5. Entrega final respetando la orientación procesada
                for part in resultado.candidates[0].content.parts:
                    if part.inline_data:
                        final_res = PIL.Image.open(io.BytesIO(part.inline_data.data))
                        # Volvemos a aplicar la corrección al resultado por seguridad
                        final_res = PIL.ImageOps.exif_transpose(final_res)
                        st.image(final_res, use_container_width=True)
                        st.balloons()
                
                st.success(f"🔥 ¡Esa {nombre_obj} te queda espectacular!")
                        
        except Exception as e:
            st.error(f"Error técnico: {e}")

st.caption("Nota: Representación por IA con fines ilustrativos.")
