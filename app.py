import streamlit as st
import os
import fal_client
from deep_translator import GoogleTranslator
from PIL import Image, ImageEnhance, ImageOps
import requests
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# --- KONFIGURACJA KLUCZY ---
os.environ["FAL_KEY"] = "cf0a6c98-7933-45df-918d-5757b24e9a30:afc267a3e94340879464bbea2862b40b"

# --- TYMCZASOWE DANE LOGOWANIA (TUTAJ BĘDZIE BAZA DANYCH) ---
ADMIN_USER = "admin"
ADMIN_PASS = "KDP2026"

st.set_page_config(page_title="KDP Multi-Studio Ultra 8K", layout="wide")
translator = GoogleTranslator(source='pl', target='en')

# --- SYSTEM LOGOWANIA ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

def login_form():
    st.title("🔐 KDP Factory Login")
    col1, col2 = st.columns([1, 1])
    with col1:
        username = st.text_input("Nazwa użytkownika (Nick):")
        password = st.text_input("Hasło:", type="password")
        if st.button("Zaloguj się"):
            if username == ADMIN_USER and password == ADMIN_PASS:
                st.session_state["authenticated"] = True
                st.session_state["user_nick"] = username
                st.success(f"Witaj {username}!")
                st.rerun()
            else:
                st.error("Błędny nick lub hasło!")
    st.stop()

if not st.session_state["authenticated"]:
    login_form()

# --- INICJALIZACJA KOSZYKA ---
if 'pdf_basket' not in st.session_state:
    st.session_state['pdf_basket'] = []
if 'last_topic' not in st.session_state:
    st.session_state['last_topic'] = ""

# --- FUNKCJE SILNIKA ---
def process_8k(img_source):
    resp = requests.get(img_source)
    img = Image.open(BytesIO(resp.content)).convert('L')
    w, h = img.size
    img = img.resize((w*2, h*2), resample=Image.LANCZOS)
    return ImageEnhance.Contrast(img).enhance(3.5)

def photo_to_outline(uploaded_file):
    img = Image.open(uploaded_file).convert('L')
    img = ImageEnhance.Contrast(img).enhance(2.5).point(lambda p: 0 if p < 140 else 255)
    return img

def generate_seo(topic):
    top = topic.capitalize()
    return {
        "title": f"{top} Coloring Book for Adults",
        "subtitle": f"Stress Relief Designs with {top} Themes - 8.5 x 11 Large Print Edition",
        "keywords": f"{topic}, adult coloring book, stress relief, gift idea, mindfulness, artistic designs",
        "description": f"Embark on a creative journey with our '{top} Coloring Book'. Unique high-quality illustrations."
    }

# --- INTERFEJS GŁÓWNY ---
with st.sidebar:
    st.title(f"👤 {st.session_state['user_nick']}")
    tryb = st.selectbox("Wybierz moduł:", 
                        ["✏️ Tekst na Kolorowankę", 
                         "📸 Zdjęcie na Kolorowankę", 
                         "📖 Opowieść (Story Mode)",
                         "🦁 Generuj Serię Niszy"])
    st.divider()
    st.write(f"Stron w projekcie: {len(st.session_state['pdf_basket'])}")
    if st.button("🗑️ Wyczyść projekt"):
        st.session_state['pdf_basket'] = []
        st.rerun()
    if st.button("🚪 Wyloguj"):
        st.session_state["authenticated"] = False
        st.rerun()

# --- MODUŁ 1: TEKST ---
if tryb == "✏️ Tekst na Kolorowankę":
    st.header("🎨 Opis -> Grafika 8K")
    prompt_pl = st.text_input("Co narysować?")
    if st.button("Generuj i Dodaj"):
        if prompt_pl:
            st.session_state['last_topic'] = prompt_pl
            with st.spinner("Pracuję..."):
                eng = translator.translate(prompt_pl)
                res = fal_client.submit("fal-ai/flux/schnell", arguments={"prompt": f"Coloring page, {eng}, 8k, black and white, bold lines"})
                img_final = process_8k(res.get()['images'][0]['url'])
                buf = BytesIO(); img_final.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())
                st.image(img_final)

# --- MODUŁ 2: ZDJĘCIE ---
elif tryb == "📸 Zdjęcie na Kolorowankę":
    st.header("📸 Twoje zdjęcie -> Kolorowanka")
    foto = st.file_uploader("Wgraj plik:", type=['jpg', 'png'])
    if foto and st.button("Przerób"):
        img_out = photo_to_outline(foto)
        buf = BytesIO(); img_out.save(buf, format="PNG")
        st.session_state['pdf_basket'].append(buf.getvalue())
        st.image(img_out)

# --- MODUŁ 3: STORY MODE ---
elif tryb == "📖 Opowieść (Story Mode)":
    st.header("📖 AI Architect: Cała Książka")
    zarys = st.text_area("O czym ma być historia?")
    ile_s = st.number_input("Ile stron?", 5, 100, 20)
    if st.button("🚀 GENERUJ MASOWO"):
        st.session_state['last_topic'] = zarys
        eng_b = translator.translate(zarys)
        bar = st.progress(0)
        for i in range(ile_s):
            p = f"Step {i+1} of {ile_s}: {eng_b}. Coloring page, 8k, bold outlines"
            res = fal_client.submit("fal-ai/flux/schnell", arguments={"prompt": p})
            img_s = process_8k(res.get()['images'][0]['url'])
            buf = BytesIO(); img_s.save(buf, format="PNG")
            st.session_state['pdf_basket'].append(buf.getvalue())
            bar.progress((i+1)/ile_s)

# --- MODUŁ 4: NISZA ---
elif tryb == "🦁 Generuj Serię Niszy":
    st.header("🦁 Seria tematyczna 8K")
    nisza = st.text_input("Nisza (np. Zwierzęta dżungli):")
    styl = st.text_input("Styl (np. Prosty dla dzieci):")
    ile_n = st.number_input("Ilość grafik?", 10, 50, 25)
    if st.button("🔥 GENERUJ SERIĘ"):
        st.session_state['last_topic'] = nisza
        en_n, en_s = translator.translate(nisza), translator.translate(styl)
        bar_n = st.progress(0)
        for i in range(ile_n):
            pr = f"Coloring page, {en_n}, {en_s} style, 8k, bold outlines"
            res = fal_client.submit("fal-ai/flux/schnell", arguments={"prompt": pr})
            img_n = process_8k(res.get()['images'][0]['url'])
            buf = BytesIO(); img_n.save(buf, format="PNG")
            st.session_state['pdf_basket'].append(buf.getvalue())
            bar_n.progress((i+1)/ile_n)

# --- EKSPORT I SEO ---
if st.session_state['pdf_basket']:
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📥 POBIERZ PDF"):
            out = BytesIO()
            p = canvas.Canvas(out, pagesize=(8.5*inch, 11*inch))
            for d in st.session_state['pdf_basket']:
                p.drawImage(BytesIO(d), 0.5*inch, 1*inch, width=7.5*inch, height=9*inch)
                p.showPage(); p.showPage()
            p.save()
            st.download_button("Zapisz PDF", out.getvalue(), "book_8k.pdf")
    with c2:
        if st.session_state['last_topic']:
            s = generate_seo(st.session_state['last_topic'])
            st.code(f"Title: {s['title']}\nSubtitle: {s['subtitle']}\nKeywords: {s['keywords']}")
