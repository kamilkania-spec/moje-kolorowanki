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

# --- KONFIGURACJA KLUCZA ---
os.environ["FAL_KEY"] = "cf0a6c98-7933-45df-918d-5757b24e9a30:afc267a3e94340879464bbea2862b40b"
st.set_page_config(page_title="KDP Factory Pro 8K - STABLE", layout="wide")
translator = GoogleTranslator(source='pl', target='en')

# --- SILNIK GENERUJĄCY (FLUX DEV - NAJWYŻSZA JAKOŚĆ) ---
def master_generate(prompt, styl, mode="bw", seed=None):
    try:
        # Budowanie promptu w zależności od wybranego kafelka
        if mode == "color":
            final_p = f"Professional kids storybook illustration, {prompt}, vibrant colors, clean lines, 8k"
        elif "mandala" in styl.lower():
            final_p = f"Intricate mandala coloring page, {prompt}, symmetrical geometric patterns, thick black lines, white background, NO shading"
        else:
            final_p = f"Coloring book page for kids, {styl}, {prompt}, thick bold black outlines, pure white background, NO shading, NO gray, NO textures, 8k"

        actual_seed = seed if seed else random.randint(1, 1000000)
        
        # Używamy modelu DEV dla braku błędów w napisach i anatomii
        handler = fal_client.subscribe("fal-ai/flux/dev", arguments={
            "prompt": final_p,
            "seed": actual_seed,
            "num_inference_steps": 28,
            "guidance_scale": 3.5
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
if "wybrany_styl" not in st.session_state: st.session_state["wybrany_styl"] = "line art"
if "ai_hint" not in st.session_state: st.session_state["ai_hint"] = ""

# --- LOGOWANIE ---
if not st.session_state["auth"]:
    st.title("🔐 KDP Factory Login")
    u = st.text_input("Nick")
    p = st.text_input("Hasło", type="password")
    if st.button("Zaloguj"):
        if u == "admin" and p == "KDP2026":
            st.session_state["auth"] = True
            st.rerun()
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.title("📦 PANEL KDP")
    tryb = st.radio("WYBIERZ NARZĘDZIE:", ["🎨 Generator Kategorii", "🌈 Bajka AI", "🚀 Masowy Generator"])
    if st.button("🗑️ WYCZYŚĆ PROJEKT"):
        st.session_state["pdf_basket"] = []
        st.rerun()

# --- MODUŁ 1: GENERATOR Z KAFELKAMI ---
if tryb == "🎨 Generator Kategorii":
    st.header("🎨 Generator Kategorii 8K")
    
    # Przywrócenie kafelków stylów
    st.subheader("Wybierz Styl:")
    style_cols = st.columns(6)
    styles = {
        "🏠 Architektura": "architecture",
        "🌿 Przyroda": "nature landscape",
        "🦁 Zwierzęta": "animal portrait",
        "☸️ Mandala": "mandala",
        "🧙 Fantasy": "fantasy",
        "🏎️ Pojazdy": "vehicle"
    }
    
    for i, (name, val) in enumerate(styles.items()):
        if style_cols[i].button(name):
            st.session_state["wybrany_styl"] = val
            st.toast(f"Wybrano: {name}")

    st.info(f"Obecny styl: **{st.session_state['wybrany_styl']}**")
    
    opis = st.text_input("Twoja wizja (np. Kot na wakacjach):", value=st.session_state["ai_hint"])
    ile = st.slider("Ile różnych grafik wygenerować?", 1, 15, 1)
    
    if st.button("🚀 GENERUJ 8K"):
        eng = translator.translate(opis)
        cols = st.columns(2) # Podgląd w dwóch kolumnach
        for i in range(ile):
            with st.spinner(f"Tworzę wariant {i+1}..."):
                img = master_generate(eng, st.session_state["wybrany_styl"], seed=random.randint(1,999999))
                if img:
                    cols[i % 2].image(img, caption=f"Wariant {i+1}")
                    buf = BytesIO()
                    img.save(buf, format="PNG")
                    st.session_state["pdf_basket"].append(buf.getvalue())
        st.success(f"Dodano {ile} grafik do PDF!")

    st.divider()
    slowo = st.text_input("Podpowiedź AI (wpisz słowo):")
    if st.button("✨ Podpowiedz mi"):
        poms = [f"{slowo} w lesie", f"mały {slowo}", f"szalony {slowo}"]
        st.session_state["ai_hint"] = random.choice(poms)
        st.rerun()

# --- POZOSTAŁE MODUŁY (STABILNE) ---
elif tryb == "🌈 Bajka AI":
    st.header("🌈 Bajka AI (Kolor)")
    b_opis = st.text_area("Opisz scenę do bajki:")
    if st.button("GENERUJ ILUSTRACJĘ"):
        img = master_generate(translator.translate(b_opis), "storybook", mode="color")
        if img:
            st.image(img)
            buf = BytesIO()
            img.save(buf, format="PNG")
            st.session_state["pdf_basket"].append(buf.getvalue())

elif tryb == "🚀 Masowy Generator":
    st.header("🚀 Masowy Generator (10-30)")
    m_temat = st.text_input("Temat serii:")
    m_ile = st.select_slider("Ilość:", options=[10, 20, 30])
    if st.button("START"):
        eng_m = translator.translate(m_temat)
        for i in range(m_ile):
            img = master_generate(eng_m, "line art", seed=random.randint(1,999999))
            if img:
                buf = BytesIO()
                img.save(buf, format="PNG")
                st.session_state["pdf_basket"].append(buf.getvalue())
        st.success("Seria gotowa!")

# --- EKSPORT PDF (FIXED TYPE ERROR) ---
if st.session_state["pdf_basket"]:
    st.divider()
    st.subheader(f"📄 Twój Projekt: {len(st.session_state['pdf_basket'])} stron")
    if st.button("📥 POBIERZ PDF DO AMAZON KDP"):
        try:
            out = BytesIO()
            pdf = canvas.Canvas(out, pagesize=(8.5*inch, 11*inch))
            for data in st.session_state["pdf_basket"]:
                img_reader = ImageReader(BytesIO(data))
                pdf.drawImage(img_reader, 0.5*inch, 0.5*inch, width=7.5*inch, height=10*inch, preserveAspectRatio=True)
                pdf.showPage()
            pdf.save()
            st.download_button("💾 Zapisz plik PDF", out.getvalue(), "kdp_final.pdf", "application/pdf")
        except Exception as e:
            st.error(f"Błąd tworzenia PDF: {e}")
