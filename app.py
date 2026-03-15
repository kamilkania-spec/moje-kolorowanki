import streamlit as st
import os
import fal_client
from deep_translator import GoogleTranslator
from PIL import Image, ImageEnhance, ImageOps
import requests
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# --- KONFIGURACJA ---
os.environ["FAL_KEY"] = "cf0a6c98-7933-45df-918d-5757b24e9a30:afc267a3e94340879464bbea2862b40b"
HASLO_DO_FABRYKI = "KDP2026"

st.set_page_config(page_title="KDP Multi-Studio + SEO Assistant", layout="wide")
translator = GoogleTranslator(source='pl', target='en')

# --- LOGOWANIE ---
if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    st.title("🔐 Autoryzacja Fabryki")
    h = st.text_input("Podaj hasło dostępowe:", type="password")
    if st.button("Uruchom System"):
        if h == HASLO_DO_FABRYKI:
            st.session_state["auth"] = True
            st.rerun()
        else:
            st.error("Błędne hasło!")
    st.stop()

# --- INICJALIZACJA ---
if 'pdf_basket' not in st.session_state:
    st.session_state['pdf_basket'] = []
if 'last_topic' not in st.session_state:
    st.session_state['last_topic'] = ""

# --- FUNKCJE POMOCNICZE ---
def process_8k(img_source):
    resp = requests.get(img_source)
    img = Image.open(BytesIO(resp.content)).convert('L')
    w, h = img.size
    img = img.resize((w*2, h*2), resample=Image.LANCZOS)
    return ImageEnhance.Contrast(img).enhance(3.5)

def generate_seo(topic):
    """Generuje dane SEO dla Amazon KDP"""
    top = topic.capitalize()
    seo = {
        "title": f"{top} Coloring Book for Adults",
        "subtitle": f"Stress Relief Designs with {top} Themes - 8.5 x 11 Large Print Edition",
        "keywords": f"{topic}, adult coloring book, stress relief, gift idea, mindfulness, artistic designs, {topic} art",
        "description": f"Embark on a creative journey with our '{top} Coloring Book'. This book features unique, high-quality illustrations designed to provide hours of relaxation and creative expression. Perfect for artists of all levels!"
    }
    return seo

# --- SIDEBAR ---
with st.sidebar:
    st.title("🚀 KDP Factory Pro")
    tryb = st.selectbox("Wybierz Moduł:", 
                        ["✏️ Tekst na Kolorowankę", 
                         "📸 Zdjęcie na Kolorowankę", 
                         "📖 Opowieść (Story Mode)"])
    st.divider()
    st.subheader("📦 Twój Projekt")
    st.write(f"Ilość stron w PDF: {len(st.session_state['pdf_basket'])}")
    if st.button("🗑️ Wyczyść Projekt"):
        st.session_state['pdf_basket'] = []
        st.session_state['last_topic'] = ""
        st.rerun()

# --- MODUŁY ---

if tryb == "✏️ Tekst na Kolorowankę":
    st.header("🎨 Opis -> Grafika 8K")
    prompt_pl = st.text_input("Opisz obrazek:")
    if st.button("Generuj i Dodaj"):
        if prompt_pl:
            st.session_state['last_topic'] = prompt_pl
            with st.spinner("Rysuję..."):
                eng = translator.translate(prompt_pl)
                res = fal_client.submit("fal-ai/flux/schnell", arguments={"prompt": f"Coloring page, {eng}, 8k, black and white, bold lines"})
                img_final = process_8k(res.get()['images'][0]['url'])
                buf = BytesIO()
                img_final.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())
                st.image(img_final, caption="Dodano!")

elif tryb == "📸 Zdjęcie na Kolorowankę":
    st.header("📸 Zdjęcie -> Kolorowanka")
    foto = st.file_uploader("Wgraj zdjęcie:", type=['jpg', 'png'])
    if foto and st.button("Przerób i Dodaj"):
        img = Image.open(foto).convert('L')
        img = ImageEnhance.Contrast(img).enhance(2.5).point(lambda p: 0 if p < 140 else 255)
        buf = BytesIO()
        img.save(buf, format="PNG")
        st.session_state['pdf_basket'].append(buf.getvalue())
        st.image(img, caption="Przerobiono!")

elif tryb == "📖 Opowieść (Story Mode)":
    st.header("📖 AI Architect (Cała Książka)")
    zarys = st.text_area("O czym ma być ta opowieść?")
    ile_stron = st.number_input("Ile stron?", 5, 100, 20)
    if st.button("🚀 GENERUJ MASOWO"):
        if zarys:
            st.session_state['last_topic'] = zarys
            eng_base = translator.translate(zarys)
            bar = st.progress(0)
            for i in range(ile_stron):
                p = f"Step {i+1} of {ile_stron}: {eng_base}. Coloring page, 8k, bold outlines"
                res = fal_client.submit("fal-ai/flux/schnell", arguments={"prompt": p})
                img_story = process_8k(res.get()['images'][0]['url'])
                buf = BytesIO()
                img_story.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())
                bar.progress((i+1)/ile_stron)
            st.success("Książka gotowa!")

# --- FINALIZACJA I SEO ---
if st.session_state['pdf_basket']:
    st.divider()
    col_pdf, col_seo = st.columns(2)
    
    with col_pdf:
        st.subheader("📑 Plik PDF")
        if st.button("📥 POBIERZ PDF"):
            output = BytesIO()
            p = canvas.Canvas(output, pagesize=(8.5*inch, 11*inch))
            for data in st.session_state['pdf_basket']:
                p.drawImage(BytesIO(data), 0.5*inch, 1*inch, width=7.5*inch, height=9*inch)
                p.showPage()
                p.showPage()
            p.save()
            st.download_button("Zapisz plik PDF", output.getvalue(), "kdp_master_project.pdf")

    with col_seo:
        st.subheader("📈 Dane Amazon SEO")
        if st.session_state['last_topic']:
            data_seo = generate_seo(st.session_state['last_topic'])
            st.info(f"**Title:** {data_seo['title']}")
            st.info(f"**Subtitle:** {data_seo['subtitle']}")
            st.code(f"Keywords: {data_seo['keywords']}")
            st.write(f"**Description:** {data_seo['description']}")
        else:
            st.write("Wygeneruj coś, aby zobaczyć SEO.")
