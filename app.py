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

# --- SILNIK GRAFICZNY PRO Z OBSŁUGĄ SEED I ZDJĘĆ ---
def master_generate(prompt, is_color=False, image_url=None, seed=None):
    nick = st.session_state["user_nick"]
    if st.session_state["user_db"][nick]["credits"] <= 0:
        st.error("❌ Brak kredytów!")
        return None
    
    status_msg = st.empty()
    try:
        status_msg.info("⏳ Łączę z serwerem KDP 8K...")
        gen_seed = seed if seed is not None else random.randint(0, 9999999)
        
        arguments = {"prompt": prompt, "image_size": "square_hd", "seed": gen_seed}
        if image_url: arguments["image_url"] = image_url

        handler = fal_client.subscribe("fal-ai/flux/schnell", arguments=arguments)
        status_msg.info(f"🎨 AI tworzy unikalną stronę (Seed: {gen_seed})...")
        
        url = handler['images'][0]['url']
        resp = requests.get(url)
        img = Image.open(BytesIO(resp.content))
        
        if not is_color:
            img = img.convert('L')
            img = ImageEnhance.Contrast(img).enhance(3.8)
            
        w, h = img.size
        img = img.resize((w*2, h*2), resample=Image.LANCZOS)
        
        if st.session_state["role"] != "admin":
            st.session_state["user_db"][nick]["credits"] -= 1
        return img
    except Exception as e:
        st.error(f"⚠️ Błąd: {e}")
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.title(f"👤 {st.session_state['user_nick']}")
    st.write(f"🪙 Kredyty: {'∞' if st.session_state['role'] == 'admin' else st.session_state['user_db'][st.session_state['user_nick']]['credits']}")
    
    tryb = st.selectbox("WYBIERZ MODUŁ:", 
                        ["🚀 HURTOWA PRODUKCJA (20+ stron)", 
                         "🦁 NICHE FINDER & SEO", 
                         "📖 KDP STORY AI (Foto-Bajka)", 
                         "📖 STORY MODE (Książka Cz-B)",
                         "📸 ZDJĘCIE NA KONTUR 8K", 
                         "💬 FORUM TWÓRCÓW",
                         "⚖️ REGULAMIN I POMOC"])
    
    st.divider()
    if st.button("🗑️ CZYŚĆ PROJEKT"):
        st.session_state['pdf_basket'] = []; st.rerun()

# --- LOGIKA MODUŁÓW ---

if tryb == "🚀 HURTOWA PRODUKCJA (20+ stron)":
    st.header("🚀 Hurtowa Produkcja Książki (Format 8.5x11)")
    temat = st.text_input("Temat (np. Mandale, Koty, Kwiaty):")
    ile = st.number_input("Liczba stron:", 1, 100, 20)
    if st.button("🔥 URUCHOM HURTOWĄ PRODUKCJĘ"):
        bar = st.progress(0)
        wariacje = ["intricate", "geometric", "floral", "swirls", "nature", "abstract"]
        for i in range(ile):
            v = random.choice(wariacje)
            p = f"Professional coloring page, {translator.translate(temat)}, {v} style, 8k, black and white, bold lines, white background"
            img = master_generate(p)
            if img:
                buf = BytesIO(); img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())
                st.image(img, width=200, caption=f"Strona {i+1}")
            bar.progress((i+1)/ile)

elif tryb == "🦁 NICHE FINDER & SEO":
    st.header("🦁 Analiza Nisz Amazon USA/UK")
    if st.button("🔍 SKANUJ TRENDY"):
        st.success("**TOP NISZE:** 1. Easter Biblical, 2. Bold & Easy Cozy, 3. Celestial Animals")
        st.info("SEO: coloring book for adults, stress relief, kdp, 2026 trends")

elif tryb == "📖 KDP STORY AI (Foto-Bajka)":
    st.header("📖 Personalizowana Bajka ze zdjęcia")
    f_photo = st.file_uploader("📸 Wgraj zdjęcie dziecka:", type=['png', 'jpg'])
    imię = st.text_input("Imię dziecka:")
    postać = st.selectbox("Zamień w:", ["Misia", "Superbohatera", "Robota"])
    if f_photo and st.button("🚀 GENERUJ BAJKĘ"):
        photo_bytes = f_photo.read()
        photo_base64 = base64.b64encode(photo_bytes).decode('utf-8')
        p_url = f"data:{f_photo.type};base64,{photo_base64}"
        f_seed = random.randint(0, 999999) # Stały wygląd postaci
        for i in range(5):
            p = f"Coloring book illustration, {imię} as a {postać} based on photo, whimsical, step {i}, consistent"
            img = master_generate(p, image_url=p_url, seed=f_seed, is_color=True)
            if img:
                buf = BytesIO(); img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())

elif tryb == "📸 ZDJĘCIE NA KONTUR 8K":
    st.header("📸 Twoje zdjęcie na profesjonalny kontur")
    f = st.file_uploader("Wgraj zdjęcie:", type=['png', 'jpg'])
    if f and st.button("KONWERTUJ"):
        img = Image.open(f).convert('L')
        img_edges = ImageOps.invert(img.filter(ImageFilter.FIND_EDGES))
        st.image(ImageEnhance.Contrast(img_edges).enhance(3.5))

# --- EKSPORT PDF (FORMAT KDP) ---
if st.session_state['pdf_basket']:
    st.divider()
    if st.button("📥 POBIERZ GOTOWY PDF (8.5x11)"):
        out = BytesIO()
        pdf = canvas.Canvas(out, pagesize=(8.5*inch, 11*inch))
        for d in st.session_state['pdf_basket']:
            pdf.drawImage(BytesIO(d), 0.75*inch, 1.5*inch, width=7*inch, height=8*inch)
            pdf.showPage() # Rysunek
            pdf.showPage() # Pusta strona
        pdf.save()
        st.download_button("Zapisz PDF", out.getvalue(), "PROJEKT_KDP_FINAL.pdf")
