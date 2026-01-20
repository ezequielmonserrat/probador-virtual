import streamlit as st
import requests
from bs4 import BeautifulSoup
import PIL.Image
import PIL.ImageOps
import io
from google import genai

# 1. Configuración Visual
st.set_page_config(page_title="Probador Virtual Pro", layout="centered")
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    div.stButton > button:first-child {
        background-color: #0082C9; color: white; border: none; 
        width: 100%; font-weight: bold; height: 3.5em; border-radius: 5px;
    }
    div.stButton > button:first-child:hover { background-color: #E30052; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #0082C9;'>👕 PROBADOR VIRTUAL</h1>", unsafe_allow_html=True)

# 2. Validación de API Key
try:
    if "GEMINI_API_KEY" in st.secrets:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    else:
        st.error("Falta la GEMINI_API_KEY en los Secrets.")
        st.stop()
except Exception as e:
    st.error(f"Error de configuración: {e}")
    st.stop()

# 3. Interfaz de Entrada: Opción Dual (Link o Foto)
opcion_prenda = st.radio("¿Cómo querés cargar la prenda?", ["Desde Link (Solo Deportes)", "Subir Foto Manualmente"])

img_prenda = None

if opcion_prenda == "Desde Link (Solo Deportes)":
    url_producto = st.text_input("Pegá el link aquí:")
else:
    file_prenda = st.file_uploader("Subí la foto de la camiseta 👕", type=['jpg', 'png', 'jpeg'])
    if file_prenda:
        img_prenda = PIL.Image.open(file_prenda)

foto_usuario = st.file_uploader("Subí tu foto (Formato 4:5) 📸", type=['jpg', 'png', 'jpeg'])

if st.button("VER CÓMO ME QUEDA 😎"):
    if foto_usuario and (url_producto or img_prenda):
        try:
            with st.spinner("Procesando imagen con máxima seguridad..."):
                
                # A. Obtención de la prenda (Scraping Blindado)
                if opcion_prenda == "Desde Link (Solo Deportes)" and not img_prenda:
                    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                    res = requests.get(url_producto, headers=headers, timeout=10)
                    
                    if res.status_code != 200:
                        st.error("No se pudo acceder a la página (Bloqueo de seguridad). Usá la opción 'Subir Foto Manualmente'.")
                        st.stop()
                        
                    soup = BeautifulSoup(res.text, 'html.parser')
                    
                    # Buscamos la etiqueta de forma segura usando .get() para evitar el error NoneType
                    img_tag = soup.find("meta", property="og:image")
                    
                    if img_tag and img_tag.get('content'):
                        img_url = img_tag.get('content')
                        img_prenda = PIL.Image.open(io.BytesIO(requests.get(img_url).content))
                    else:
                        st.error("No se encontró la imagen en el link automáticamente. Por favor, descargá la foto de la camiseta y subila con la opción 'Subir Foto Manualmente'.")
                        st.stop()

                # B. Procesamiento de Usuario (Preservación 4:5)
                u_img = PIL.ImageOps.exif_transpose(PIL.Image.open(foto_usuario))
                ancho_orig, alto_orig = u_img.size

                # Prompt Específico para evitar rotación
                prompt = (
                    "Realiza un virtual try-on de alta calidad. "
                    "Viste a la persona con la prenda proporcionada. "
                    f"IMPORTANTE: Mantén el lienzo de salida idéntico al original ({ancho_orig}x{alto_orig}). "
                    "No rotes la imagen, mantén la verticalidad del sujeto y el fondo intacto."
                )
                
                # C. Generación con validación de respuesta
                resultado = client.models.generate_content(
                    model='gemini-2.0-flash', 
                    contents=[prompt, u_img, img_prenda]
                )
                
                # Verificamos si la IA devolvió algo válido antes de intentar leerlo
                if not resultado.candidates or not resultado.candidates[0].content.parts:
                    st.error("La IA no pudo procesar la imagen (posible filtro de seguridad). Probá con otra foto.")
                else:
                    for part in resultado.candidates[0].content.parts:
                        if part.inline_data:
                            final = PIL.Image.open(io.BytesIO(part.inline_data.data))
                            
                            # Corrección final de tamaño (Fuerza bruta para encajar en 4:5)
                            final = final.resize((ancho_orig, alto_orig), PIL.Image.Resampling.LANCZOS)
                            
                            st.image(final, caption="Resultado Final", use_container_width=True)
                            st.success("¡Listo! Sin errores y con el tamaño correcto.")
                        
        except Exception as e:
            # Mensaje detallado para saber exactamente qué falló
            st.error(f"Error técnico detectado: {str(e)}")
            st.info("Consejo: Si el error persiste, usá la opción 'Subir Foto Manualmente'.")
    else:
        st.warning("Por favor cargá ambas fotos para continuar.")
