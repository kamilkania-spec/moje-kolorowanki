import streamlit as st
import os
import fal_client
import requests
import random
import base64
from deep_translator import GoogleTranslator
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# --- KONFIGURACJA ---
os.environ["FAL_KEY"] = "cf0a6c98-7933-45df-918d-5757b24e9a30:afc267a3e94340879464bbea2862b40b"

st.set_page_config(page_title="KDP Factory Pro - FINAL FIX", layout="wide")
translator = GoogleTranslator(source='pl', target='en')

if "pdf_basket" not in st.session_state: st.session_state["pdf_basket"] = []
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False

# --- LOGOWANIE ---
if not st.session_state["authenticated"]:
    st.title("🔐 KDP Factory Login")
    u, p = st.text_input("Nick:"), st.text_input("Hasło:", type="password")
    if st.button("Zaloguj"):
        if u == "admin" and p == "KDP2026":
            st.session_state["authenticated"] = True
            st.rerun()
    st.stop()

# --- POPRAWIONY SILNIK GRAFICZNY (JAKOŚĆ 8K + UNIKALNOŚĆ) ---
def master_generate(prompt, is_color=False, image_url=None, current_seed=None):
    try:
        # Jeśli nie podano seeda, losuj nowy dla KAŻDEGO obrazka
        final_seed = current_seed if current_seed is not None else random.randint(0, 10**8)
        
        # Profesjonalny Prompt 8K
        clean_p = f"{prompt}, high quality line art, sharp solid black contours, pure white background, no shading, professional adult coloring book style, masterpiece, 8k resolution"
        
        arguments = {"prompt": clean_p, "image_size": "square_hd", "seed": final_seed}
        if image_url: arguments["image_url"] = image_url

        handler = fal_client.subscribe("fal-ai/flux/schnell", arguments=arguments)
        img = Image.open(BytesIO(requests.get(handler['images'][0]['url']).content))
        
        if not is_color:
            img = img.convert('L')
            # Poprawiona jakość linii - bez chujowej pikselozy
            img = ImageEnhance.Contrast(img).enhance(2.8) 
            img = img.filter(ImageFilter.SHARPEN) # Wyostrzenie linii
        
        # High-Res Upscale
        w, h = img.size
        img = img.resize((w*2, h*2), resample=Image.LANCZOS)
        return img
    except Exception as e:
        st.error(f"Błąd: {e}")
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Panel Dowodzenia")
    tryb = st.selectbox("NARZĘDZIE:", ["🚀 HURTOWA PRODUKCJA (20+)", "🦁 NICHE FINDER", "📖 KDP STORY AI", "📸 KONTUR"])
    if st.button("🗑️ CZYŚĆ PROJEKT"):
        st.session_state['pdf_basket'] = []; st.rerun()

# --- MODUŁ HURTOWY (FIXED) ---
if tryb == "🚀 HURTOWA PRODUKCJA (20+)":
    st.header("🚀 Hurtowa Produkcja (20 różnych grafik)")
    c1, c2, c3 = st.columns(3)
    kat = c1.selectbox("Kategoria:", ["Przyroda", "Mandale", "Zwierzęta", "Architektura", "Fantastyka"])
    styl = c2.selectbox("Styl:", ["Szczegółowe", "Bold & Easy", "Zentangle"])
    ile = c3.number_input("Ile sztuk:", 1, 50, 20)
    
    temat = st.text_input("Temat (np. sowa w dziupli):")
    
    if st.button("🔥 URUCHOM GENEROWANIE 20 SZTUK"):
        cols = st.columns(4)
        bar = st.progress(0)
        
        kat_p = {"Przyroda": "nature scenery", "Mandale": "complex mandala", "Zwierzęta": "wild animal", "Architektura": "gothic building", "Fantastyka": "dragon fantasy"}
        styl_p = {"Szczegółowe": "intricate lines", "Bold & Easy": "very thick bold lines", "Zentangle": "ornamental patterns"}
        
        eng_t = translator.translate(temat)
        
        for i in range(ile):
            # KLUCZ: Każda iteracja ma własny, unikalny seed
            p = f"Coloring page, {kat_p[kat]}, {styl_p[styl]}, {eng_t}, variation_{i}"
            img = master_generate(p)
            
            if img:
                buf = BytesIO(); img.save(buf, format="PNG")
