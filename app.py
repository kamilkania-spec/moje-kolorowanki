import streamlit as st
import os
import fal_client
from deep_translator import GoogleTranslator
from PIL import Image, ImageEnhance
import requests
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
import random

# --- KONFIGURACJA ---
os.environ["FAL_KEY"] = "cf0a6c98-7933-45df-918d-5757b24e9a30:afc267a3e94340879464bbea2862b40b"
st.set_page_config(page_title="KDP Factory ULTRA FIX", layout="wide")
translator = GoogleTranslator(source='pl', target='en')

# --- SILNIK GENERUJĄCY (STABILNY) ---
def master_generate(prompt, mode="bw", seed=None):
    try:
        if mode == "color":
            final_p = f"Vibrant kids book illustration, {prompt}, clean lines, high resolution, masterpiece"
        else:
            final_p = (
                f"Coloring book page, {prompt}, heavy thick black outlines, "
                "pure white background, NO shading, NO gray, NO textures, 8k resolution"
            )
        
        actual_seed = seed if seed else random.randint(1, 1000000)
        # Przełączam na Schnell dla szybkości i stabilności po tylu błędach
        handler = fal_client.subscribe("fal-ai/flux/schnell", arguments={
            "prompt": final_p,
            "seed": actual_seed
        })
        url = handler['images'][0]['url']
        resp = requests.get(url)
        img = Image.open(BytesIO(resp.content))
        
        if mode == "bw":
            img = img.convert('L')
            img = ImageEnhance.Contrast(img).enhance(2.5)
            img = img.convert('RGB')
        return img
    except Exception as e:
        st.error(f"Błąd API: {e}")
        return None

# --- INICJALIZACJA SESJI ---
if "pdf_basket" not in st.session_state: st.session_state["pdf_basket"] = []
if "auth" not in st.session_state: st.session_state["auth"] = False
if "ai_hint" not in st.session_state: st.session_state["ai_hint"] = ""

# --- LOGOWANIE ---
if not st.session_state["auth"]:
    st.title("🔐 Login")
    u = st.text_input("Nick")
    p = st.text_input("Hasło", type="password")
    if st.button("Zaloguj"):
        if u == "admin" and p == "KDP2026":
            st.session_state["auth"] = True
            st.rerun()
    st.stop()

# --- SIDEBAR (MENU) ---
with st.sidebar:
    st.title("📦 MENU")
    tryb = st.radio("Wybierz:", ["🎨 Generator", "🌈 Bajka", "🚀 Masowy", "📷 Foto"])
    if st.button("🗑️ CZYŚĆ WSZYSTKO"):
        st.session_state["pdf_basket"] = []
        st.rerun()

# --- MODUŁY ---
if tryb == "🎨 Generator":
    st.header("🎨 Generator Kategorii")
    opis = st.text_input("Twoja wizja:", value=st.session_state["ai_hint"])
    ile = st.slider("Ilość:", 1, 15, 1)
    
    if st.button("🚀 GENERUJ"):
        eng = translator.translate(opis)
        for i in range(ile):
            with st.spinner(f"Tworzę {i+1}..."):
                img = master_generate(eng, seed=random.randint(1,999999))
                if img:
                    st.image(img)
                    buf = BytesIO()
                    img.save(buf, format="PNG")
                    st.session_state["pdf_basket"].append(buf.getvalue())
    
    st.divider()
    slowo = st.text_input("Nie masz pomysłu? Wpisz słowo:")
    if st.button("✨ Podpowiedz mi"):
        poms = [f"{slowo} na wakacjach", f"uroczy {slowo}", f"mandala {slowo}"]
        st.session_state["ai_hint"] = random.choice(poms)
        st.rerun()

elif tryb == "🌈 Bajka":
    st.header("🌈 Bajka AI")
    b_opis = st.text_area("Opisz scenę bajki (kolorowa):")
    if st.button("🚀 GENERUJ KOLOR"):
        eng = translator.translate(b_opis)
        img = master_generate(eng, mode="color")
        if img:
            st.image(img)
            buf = BytesIO()
            img.save(buf, format="PNG")
            st.session_state["pdf_basket"].append(buf.getvalue())

elif tryb == "🚀 Masowy":
    st.header("🚀 Masowy Generator")
    m_opis = st.text_input("Temat serii (np. Samochody):")
    if st.button("🚀 GENERUJ 10 SZTUK"):
        eng = translator.translate(m_opis)
        for i in range(10):
            img = master_generate(eng, seed=random.randint(1,999999))
            if img:
                buf = BytesIO()
                img.save(buf, format="PNG")
                st.session_state["pdf_basket"].append(buf.getvalue())
        st.success("Dodano 10 grafik!")

elif tryb == "📷 Foto":
    st.header("📷 Zdjęcie na Kontur")
    st.write("Wgraj plik (opcja w budowie)...")

# --- EKSPORT PDF ---
if st.session_state["pdf_basket"]:
    st.divider()
    st.subheader(f"Twoja Kolejka: {len(st.session_state['pdf_basket'])} stron")
    if st.button("📥 POBIERZ PDF DLA KDP"):
        try:
            out = BytesIO()
            pdf = canvas.Canvas(out, pagesize=(8.5*inch, 11*inch))
            for data in st.session_state["pdf_basket"]:
                img_obj = ImageReader(BytesIO(data))
                pdf.drawImage(img_obj, 0.5*inch, 1*inch, width=7.5*inch, height=9*inch)
                pdf.showPage()
            pdf.save()
            st.download_button("💾 Zapisz Plik PDF", out.getvalue(), "kdp_project.pdf", "application/pdf")
        except Exception as e:
            st.error(f"Błąd PDF: {e}")
