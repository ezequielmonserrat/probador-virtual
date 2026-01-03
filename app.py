import streamlit as st
import requests
from bs4 import BeautifulSoup
import PIL.Image
import io
from google import genai

# Configuración de página
st.set_page_config(page_title="Probador Virtual", page_icon="👕")

st.title("👕 PROBADOR VIRTUAL")
st.markdown("---")

# Conexión con la API Key oculta
try:
    api_key_interna = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key_interna)
except Exception:
    st.error("⚠️ Error: No se encontró la API Key en los Secrets.")
    st.stop()

# Interfaz de usuario
url_producto = st.text_input("1. Pegá el link de la prenda aquí:")
foto_usuario = st.file_uploader("2. Subí tu foto 📸", type=['jpg', 'png', 'jpeg'])

if st.button("Ver cómo me queda 😎"):
    if not url_producto or not foto_usuario:
        st.error("Por favor, cargá el link y tu foto.")
    else:
        try:
            with st.spinner("🪄 Procesando tu imagen..."):
                # 1. Obtener imagen de la prenda
                res = requests.get(url_producto, headers={'User-Agent': 'Mozilla/5.0'})
                soup = BeautifulSoup(res.text, 'html.parser')
                img_url = soup.find("meta", property="og:image")['content']
                img_prenda = PIL.Image.open(io.BytesIO(requests.get(img_url).content))
                
                # 2. Identificar objeto
                h1 = soup.find("h1")
                titulo = h1.text.strip().lower() if h1 else "prenda"
                prompt_n = f"Extrae el nombre del objeto (una palabra) de: {titulo}"
                nombre_obj = client.models.generate_content(model='gemini-2.0-flash', contents=[prompt_n]).text.strip().lower()

                # 3. Generar resultado
                img_user = PIL.Image.open(foto_usuario)
                instruccion = f"Sustituye la prenda del usuario por la {nombre_obj} de la Imagen 2. Mantené la pose del usuario."
                
                resultado = client.models.generate_content(
                    model='gemini-2.5-flash-image',
                    contents=[instruccion, img_user, img_prenda]
                )
                
                # 4. Entrega final con CORRECCIÓN DE ROTACIÓN
                for part in resultado.candidates[0].content.parts:
                    if part.inline_data:
                        from PIL import ImageOps
                        img_cruda = PIL.Image.open(io.BytesIO(part.inline_data.data))
                        
                        # Corregir rotación automática
                        final_img = ImageOps.exif_transpose(img_cruda)
                        
                        # Forzar vertical si el ancho es mayor al alto
                        w, h = final_img.size
                        if w > h:
                            final_img = final_img.rotate(-90, expand=True)
                        
                        st.image(final_img, use_container_width=True)
                        st.balloons()
                
                st.success(f"🔥 ¡Esa {nombre_obj} te queda espectacular!")
                        
        except Exception as e:
            st.error(f"Hubo un problema técnico: {e}")

st.caption("Nota: Representación por IA con fines ilustrativos.")
