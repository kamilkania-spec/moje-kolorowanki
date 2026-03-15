import streamlit as st
import os
import fal_client
from deep_translator import GoogleTranslator
from PIL import Image, ImageEnhance, ImageFilter, ImageOps  # Dodałem ImageOps tutaj
import requests
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# --- KONFIGURACJA ---
os.environ["FAL_KEY"] = "cf0a6c98-7933-45df-918d-5757b24e9a30:afc267a3e94340879464bbea2862b40b"
ADMIN_NICK = "admin"
ADMIN_PASS = "KDP2026"

st.set_page_config(page_title="KDP Factory Pro 8K - FULL SUITE", layout="wide")
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

# --- NARZĘDZIA SEO ---
def get_amazon_trends():
    return [
        "Easter Biblical Stories (Seasonally High)",
        "Bold & Easy: Cozy Little Shops",
        "Celestial Boho Animals",
        "Victorian Steampunk Fashions",
        "Kawaii Food with Expressions"
    ]

def generate_listing_info(niche):
    return {
        "title": f"{niche.capitalize()} Coloring Book for Adults",
        "subtitle": f"Stress Relief: Relaxing Designs in 8K - {niche} Theme - Large Print",
        "keywords": f"{niche}, coloring book, kdp, amazon, adult coloring, meditation, 2026 trends"
    }

# --- SILNIK GRAFICZNY ---
def master_generate(prompt):
    nick = st.session_state["user_nick"]
    if st.session_state["user_db"][nick]["credits"] <= 0:
        st.error("Brak kredytów!")
        return None
    try:
        handler = fal_client.subscribe("fal-ai/flux/schnell", arguments={"prompt": prompt})
        url = handler['images'][0]['url']
        resp = requests.get(url)
        img = Image.open(BytesIO(resp.content)).convert('L')
        w, h = img.size
        img = img.resize((w*2, h*2), resample=Image.LANCZOS)
        if st.session_state["role"] != "admin":
            st.session_state["user_db"][nick]["credits"] -= 1
        return ImageEnhance.Contrast(img).enhance(3.5)
    except Exception as e:
        st.error(f"Błąd API: {e}"); return None

# --- SIDEBAR ---
with st.sidebar:
    st.title(f"👤 {st.session_state['user_nick']}")
    cred = st.session_state["user_db"][st.session_state['user_nick']]['credits']
    st.write(f"🪙 Kredyty: {'∞' if st.session_state['role'] == 'admin' else cred}")
    tryb = st.selectbox("Wybierz moduł:", 
                        ["✏️ Generator Kategorii", "🦁 Niche Finder & SEO", "📖 Opowieść (Story Mode)", "📸 Zdjęcie na Kontur", "💬 Forum"])
    st.divider()
    if st.button("🗑️ Wyczyść Projekt"):
        st.session_state['pdf_basket'] = []; st.rerun()
    if st.button("🚪 Wyloguj"):
        st.session_state["authenticated"] = False; st.rerun()

# --- MODUŁY ---
if tryb == "✏️ Generator Kategorii":
    st.header("🎨 Szybki Generator 8K")
    kat = st.radio("Styl:", ["Dowolny", "Geometria", "Pejzaż", "Przyroda", "Architektura"], horizontal=True)
    opis = st.text_input("Opis:")
    if st.button("GENERUJ"):
        with st.spinner("Pracuję..."):
            eng = translator.translate(opis)
            p = f"Coloring book page, {kat if kat != 'Dowolny' else ''} {eng}, 8k, bold lines, white background"
            img = master_generate(p)
            if img:
                buf = BytesIO(); img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())
                st.image(img)

elif tryb == "🦁 Niche Finder & SEO":
    st.header("🦁 Niche Blaster")
    if st.button("🔍 Skanuj Trendy"):
        for t in get_amazon_trends(): st.code(t)
    n_input = st.text_input("Wpisz niszę:")
    if n_input:
        info = generate_listing_info(n_input)
        st.success(f"Tytuł: {info['title']}")
        ile_n = st.number_input("Ile grafik?", 1, 50, 5)
        if st.button("🚀 Generuj"):
            bar = st.progress(0)
            for i in range(ile_n):
                img = master_generate(f"Coloring page, {translator.translate(n_input)}, 8k, bold lines")
                if img:
                    buf = BytesIO(); img.save(buf, format="PNG")
                    st.session_state['pdf_basket'].append(buf.getvalue())
                bar.progress((i+1)/ile_n)

elif tryb == "📖 Opowieść (Story Mode)":
    st.header("📖 Story Mode")
    historia = st.text_area("Fabuła:")
    ile_s = st.number_input("Strony:", 5, 50, 10)
    if st.button("🔥 GENERUJ"):
        bar_s = st.progress(0)
        for i in range(ile_s):
            img = master_generate(f"Step {i+1} of {ile_s}: {translator.translate(historia)}. Coloring page, 8k, bold lines")
            if img:
                buf = BytesIO(); img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())
            bar_s.progress((i+1)/ile_s)

elif tryb == "📸 Zdjęcie na Kontur":
    st.header("📸 Bezstratny Szkic 8K")
    f = st.file_uploader("Wgraj zdjęcie:", type=['png', 'jpg'])
    if f and st.button("KONWERTUJ"):
        with st.spinner("Przetwarzam..."):
            img_pil = Image.open(f).convert('L')
            # Ulepszony algorytm bezstratnego konturu
            img_blurred = img_pil.filter(ImageFilter.GaussianBlur(radius=1
