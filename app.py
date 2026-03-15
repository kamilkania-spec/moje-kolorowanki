import streamlit as st
import os
import fal_client
from deep_translator import GoogleTranslator
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import requests
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import random
import base64

# --- KONFIGURACJA ---
os.environ["FAL_KEY"] = "cf0a6c98-7933-45df-918d-5757b24e9a30:afc267a3e94340879464bbea2862b40b"

st.set_page_config(page_title="KDP Factory Pro - FULL BEAST MODE", layout="wide")
translator = GoogleTranslator(source='pl', target='en')

# --- BAZA DANYCH ---
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {
        "admin": {"pass": "KDP2026", "credits": 999999, "role": "admin"},
        "tester": {"pass": "KDP123", "credits": 50, "role": "user"}
    }
if "pdf_basket" not in st.session_state: st.session_state["pdf_basket"] = []
if "posts" not in st.session_state: st.session_state["posts"] = []
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False

# --- LOGOWANIE ---
if not st.session_state["authenticated"]:
    st.title("🔐 KDP Factory Login")
    u = st.text_input("Nick:")
    p = st.text_input("Hasło:", type="password")
    if st.button("Zaloguj się"):
        if u in st.session_state["user_db"] and st.session_state["user_db"][u]["pass"] == p:
            st.session_state["authenticated"] = True
            st.session_state["user_nick"] = u
            st.session_state["role"] = st.session_state["user_db"][u]["role"]
            st.rerun()
    st.stop()

# --- SILNIK GRAFICZNY PRO (iColoring Style) ---
def master_generate(prompt, is_color=False, image_url=None, seed=None):
    try:
        gen_seed = seed if seed is not None else random.randint(0, 9999999)
        # iColoring Style Injection
        clean_prompt = f"{prompt}, high quality line art, sharp edges, pure white background, zero grayscale, professional coloring book style, 8k"
        
        arguments = {"prompt": clean_prompt, "image_size": "square_hd", "seed": gen_seed}
        if image_url: arguments["image_url"] = image_url

        handler = fal_client.subscribe("fal-ai/flux/schnell", arguments=arguments)
        url = handler['images'][0]['url']
        resp = requests.get(url)
        img = Image.open(BytesIO(resp.content))
        
        if not is_color:
            img = img.convert('L')
            img = ImageEnhance.Contrast(img).enhance(4.2)
        
        w, h = img.size
        img = img.resize((w*2, h*2), resample=Image.LANCZOS)
        return img
    except Exception as e:
        st.error(f"⚠️ Błąd: {e}")
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.title(f"👤 {st.session_state['user_nick']}")
    st.write(f"🪙 Kredyty: {'∞' if st.session_state['role'] == 'admin' else st.session_state['user_db'][st.session_state['user_nick']]['credits']}")
    
    tryb = st.selectbox("WYBIERZ MODUŁ:", 
                        ["🚀 HURTOWA PRODUKCJA (Siatka)", 
                         "🦁 NICHE FINDER & SEO", 
                         "📖 KDP STORY AI (Foto-Bajka)", 
                         "📖 STORY MODE (Fabularny)",
                         "📸 ZDJĘCIE NA KONTUR 8K", 
                         "💬 FORUM TWÓRCÓW",
                         "⚖️ REGULAMIN I POMOC"])
    
    st.divider()
    if st.button("🗑️ CZYŚĆ PROJEKT"):
        st.session_state['pdf_basket'] = []; st.rerun()
    if st.button("🚪 WYLOGUJ"):
        st.session_state["authenticated"] = False; st.rerun()

# --- LOGIKA MODUŁÓW ---

if tryb == "🚀 HURTOWA PRODUKCJA (Siatka)":
    st.header("🚀 Hurtowy Generator Tematyczny (Styl iColoring)")
    c1, c2, c3 = st.columns(3)
    with c1: kat = st.selectbox("Kategoria:", ["Przyroda i Natura", "Mand
