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

st.set_page_config(page_title="KDP Factory Ultimate 8K", layout="wide")
translator = GoogleTranslator(source='pl', target='en')

# --- BAZA KREDYTÓW ---
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {
        "admin": {"pass": "KDP2026", "credits": 999999, "role": "admin"},
        "tester": {"pass": "KDP123", "credits": 50, "role": "user"}
    }

if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
if "pdf_basket" not in st.session_state: st.session_state["pdf_basket"] = []
if "posts" not in st.session_state: st.session_state["posts"] = [{"u": "System", "m": "Witaj w fabryce!"}]
if "last_topic" not in st.session_state: st.session_state["last_topic"] = ""

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
        else: st.error("Błąd!")
    st.stop()

# --- GŁÓWNY SILNIK GENERUJĄCY ---
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
        # Skalowanie 8K
        w, h = img.size
        img = img.resize((w*2, h*2), resample=Image.LANCZOS)
        if st.session_state["role"] != "admin":
            st.session_state["user_db"][nick]["credits"] -= 1
        return ImageEnhance.Contrast(img).enhance(3.5)
    except Exception as e:
        st.error(f"Błąd API: {e}")
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.title(f"👤 {st.session_state['user_nick']}")
    cred = st.session_state["user_db"][st.session_state['user_nick']]['credits']
    st.write(f"🪙 Kredyty: {'∞' if st.session_state['role'] == 'admin' else cred}")
    tryb = st.selectbox("Wybierz moduł:", 
                        ["✏️ Generator Kategorii", "📖 Opowieść (Story Mode)", 
                         "🦁 Niche Blaster", "📸 Zdjęcie na Kontur", "💬 Forum"])
    if st.button("🗑️ Wyczyść Projekt"):
        st.session_state['pdf_basket'] = []; st.rerun()
    if st.button("🚪 Wyloguj"):
        st.session_state["authenticated"] = False; st.rerun()

# --- LOGIKA MODUŁÓW ---

if tryb == "✏️ Generator Kategorii":
    st.header("🎨 Generator 8K")
    kat = st.radio("Styl:", ["Przyroda", "Geometria", "Pejzaż", "Architektura", "Dowolny"], horizontal=True)
    opis = st.text_input("Co narysować?")
    if st.button("GENERUJ"):
        with st.spinner("Rysuję..."):
            eng = translator.translate(opis)
            img = master_generate(f"Coloring book page, {kat if kat != 'Dowolny' else ''} {eng}, 8k, bold lines")
            if img:
                buf = BytesIO(); img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())
                st.session_state['last_topic'] = opis
                st.image(img)

elif tryb == "📖 Opowieść (Story Mode)":
    st.header("📖 Story Mode - Cała Książka")
    zarys = st.text_area("Opisz historię:")
    ile_s = st.number_input("Ile stron?", 5, 50, 10)
    if st.button("🚀 GENERUJ OPOWIEŚĆ"):
        st.session_state['last_topic'] = zarys
        bar = st.progress(0)
        eng_z = translator.translate(zarys)
        for i in range(ile_s):
            img = master_generate(f"Step {i+1} of {ile_s}: {eng_z}. Coloring page, 8k, consistent style, bold outlines")
            if img:
                buf = BytesIO(); img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())
            bar.progress((i+1)/ile_s)

elif tryb == "🦁 Niche Blaster":
    st.header("🦁 Niche Blaster - Seria Tematyczna")
    nisza = st.text_input("Jaka nisza (np. Dinozaury)?")
    ile_n = st.number_input("Ile grafik?", 5, 50, 10)
    if st.button("🔥 GENERUJ SERIĘ"):
        st.session_state['last_topic'] = nisza
        bar = st.progress(0)
        eng_n = translator.translate(nisza)
        for i in range(ile_n):
            img = master_generate(f"Coloring page, {eng_n}, 8k, unique composition, bold outlines")
            if img:
                buf = BytesIO(); img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())
            bar.progress((i+1)/ile_n)

elif tryb == "📸 Zdjęcie na Kontur":
    st.header("📸 Twoje zdjęcie -> Kolorowanka")
    f = st.file_uploader("Wgraj zdjęcie:", type=['png', 'jpg'])
    if f and st.button("Konwertuj"):
        img = Image.open(f).convert('L')
        img = ImageEnhance.Contrast(img).enhance(2.5).point(lambda p: 0 if p < 140 else 255)
        buf = BytesIO(); img.save(buf, format="PNG")
        st.session_state['pdf_basket'].append(buf.getvalue())
        st.image(img)

elif tryb == "💬 Forum":
    st.header("💬 Forum")
    m = st.text_input("Wiadomość:")
    if st.button("Wyślij"):
        st.session_state["posts"].insert(0, {"u": st.session_state["user_nick"], "m": m})
        st.rerun()
    for p in st.session_state["posts"]: st.info(f"**{p['u']}**: {p['m']}")

# --- PDF ---
if st.session_state['pdf_basket']:
    st.divider()
    if st.button("📥 POBIERZ PDF"):
        out = BytesIO()
        pdf = canvas.Canvas(out, pagesize=(8.5*inch, 11*inch))
        for d in st.session_state['pdf_basket']:
            pdf.drawImage(BytesIO(d), 0.5*inch, 1*inch, width=7.5*inch, height=9*inch)
            pdf.showPage(); pdf.showPage()
        pdf.save()
        st.download_button("Zapisz PDF", out.getvalue(), "kdp_book.pdf")
