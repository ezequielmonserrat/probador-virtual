import streamlit as st
import requests
from bs4 import BeautifulSoup
import PIL.Image
import PIL.ImageOps
import io
from google import genai

# 1. Configuración de página y Estilo Profesional (Marca Blanca)
st.set_page_config(page_title="Probador Virtual | Solo Deportes", page_icon="👕", layout="centered")

# CSS para ocultar menús de Streamlit y aplicar colores de marca
st.markdown("""
    <style>
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp { background-color: #FFFFFF; }
    
    /* Botón con el Cian exacto (#0082C9) */
    div.stButton > button:first-child {
        background-color: #0082C9; 
        color: white; 
        border: none; 
        width: 100%; 
        font-weight: bold;
        border-radius: 4px;
        transition: all 0.3s ease;
    }
    /* Hover con el Magenta exacto (#E30052) */
    div.stButton > button:first-child:hover {
        background-color: #E30052;
        color: white;
    }
    /* Borde verde para inputs (#009B3A) */
    .stTextInput input { border-color: #009B3A !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("👕 PROBADOR VIRTUAL")
st.markdown("<p style='color: #666;'>Probá las prendas de <b>Solo Deportes</b> con alta fidelidad.</p>", unsafe_allow_html=True)

# 2. Conexión con Gemini
try:
    client = genai.Client(
