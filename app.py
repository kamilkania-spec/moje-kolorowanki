import streamlit as st
import os
import fal_client
from deep_translator import GoogleTranslator
from PIL import Image, ImageEnhance
import requests
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# --- KONFIGURACJA ---
os.environ["FAL_KEY"] = "cf0a6c98-7933-45df-918d-5757b24e9a30:afc267a3e94340879464bbea2862b40b"
ADMIN_NICK = "admin"
ADMIN_PASS = "KDP2026"

st.set_page_config(page_title="KDP Factory PRO + Niche Finder", layout="wide")
translator = GoogleTranslator(source='pl', target='en')

# --- BAZA KREDYTÓW I SESJI ---
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {"admin": {"pass": "KDP2026", "credits": 999999, "role": "admin"}}
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

# --- FUNKCJE SEO I NISZ ---
def get_niche_suggestions():
    # Symulacja analizy trendów Amazon 2026
    return ["Kawaii Food with Faces", "Cyberpunk Forest Creatures", "Minimalist Boho Patterns", "Victorian Steampunk Animals"]

def generate_kdp_listing(topic):
    t = topic.capitalize()
    return {
        "title": f"{t} Coloring Book for Adults",
        "subtitle": f"Stress Relief Designs: {t} Theme - Large Print 8.5x11 - 2026 Edition",
        "keywords": f"{topic}, adult coloring, gift for artists, stress relief, creative hobby, kdp, trending"
    }

# --- SILNIK GENERUJĄCY ---
def master_generate(prompt):
    try:
        handler = fal_client.subscribe("fal-ai/flux/schnell", arguments={"prompt": prompt})
        resp = requests.get(handler['images'][0]['url'])
        img = Image.open(BytesIO(resp.content)).convert('L')
        w, h = img.size
        img = img.resize((w*2, h*2), resample=Image.LANCZOS)
        if st.session_state["role"] != "admin":
            st.session_state["user_db"][st.session_state["user_nick"]]["credits"] -= 1
        return ImageEnhance.Contrast(img).enhance(3.5)
    except Exception as e:
        st.error(f"Błąd: {e}")
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.title(f"👤 {st.session_state['user_nick']}")
    tryb = st.selectbox("Wybierz moduł:", 
                        ["✏️ Generator 8K", "🦁 Niche Finder & Blaster", "📖 Story Mode", "💬 Forum"])
    if st.button("🗑️ Wyczyść projekt"):
        st.session_state['pdf_basket'] = []; st.rerun()

# --- MODUŁY ---

if tryb == "🦁 Niche Finder & Blaster":
    st.header("🦁 Niche Finder: Co dziś sprzedać?")
    
    if st.button("🔍 Skanuj trendy Amazon (USA/UK)"):
        trends = get_niche_suggestions()
        st.write("🔥 **Gorące nisze na dziś:**")
        for t in trends:
            st.code(t)

    st.divider()
    nisza = st.text_input("Wpisz wybraną niszę:")
    if nisza:
        seo = generate_kdp_listing(nisza)
        st.info(f"✅ **Automatyczny Tytuł:** {seo['title']}")
        st.write(f"**Podtytuł:** {seo['subtitle']}")
        st.write(f"**Keywords:** {seo['keywords']}")
        
        ile = st.number_input("Ile stron wygenerować dla tej niszy?", 5, 50, 10)
        if st.button("🚀 Generuj Serię i SEO"):
            bar = st.progress(0)
            eng_n = translator.translate(nisza)
            for i in range(ile):
                img = master_generate(f"Coloring page, {eng_n}, 8k, bold outlines, white background")
                if img:
                    buf = BytesIO(); img.save(buf, format="PNG")
                    st.session_state['pdf_basket'].append(buf.getvalue())
                bar.progress((i+1)/ile)
            st.success("Seria gotowa do pobrania!")

elif tryb == "✏️ Generator 8K":
    st.header("🎨 Szybki Generator")
    opis = st.text_input("Opis:")
    if st.button("Generuj"):
        with st.spinner("Pracuję..."):
            img = master_generate(f"Coloring page, {translator.translate(opis)}, 8k, bold lines")
            if img:
                buf = BytesIO(); img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())
                st.image(img)

elif tryb == "💬 Forum":
    st.header("💬 Forum Inspiracji")
    m = st.text_input("Napisz coś:")
    if st.button("Wyślij"):
        st.session_state["posts"].insert(0, {"u": st.session_state["user_nick"], "m": m})
        st.rerun()
    for p in st.session_state["posts"]: st.info(f"**{p['u']}**: {p['m']}")

# --- PDF ---
if st.session_state['pdf_basket']:
    if st.button("📥 POBIERZ PDF"):
        out = BytesIO()
        pdf = canvas.Canvas(out, pagesize=(8.5*inch, 11*inch))
        for d in st.session_state['pdf_basket']:
            pdf.drawImage(BytesIO(d), 0.5*inch, 1*inch, width=7.5*inch, height=9*inch)
            pdf.showPage(); pdf.showPage()
        pdf.save()
        st.download_button("Zapisz PDF", out.getvalue(), "kdp_final.pdf")
