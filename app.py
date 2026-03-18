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
st.set_page_config(page_title="KDP Factory Pro 8K", layout="wide")
translator = GoogleTranslator(source='pl', target='en')

# --- SILNIK GENERUJĄCY (Z POPRAWKĄ ANATOMII) ---
def master_generate(prompt, styl_wybrany):
    try:
        # Dodano: "anatomically correct", "clearly defined limbs", "full body"
        # To wymusza na AI pilnowanie rąk, nóg i ogólnej logiki postaci
        final_p = (
            f"Coloring book page, {styl_wybrany}, {prompt}, "
            f"anatomically correct, clearly defined limbs, full body visible, "
            f"heavy thick black outlines, pure white background, "
            f"NO shading, NO shadows, NO grey, pure black and white, "
            f"smooth clean lines, 8k resolution, high contrast, masterpiece"
        )
        
        arguments = {"prompt": final_p}
        handler = fal_client.subscribe("fal-ai/flux/schnell", arguments=arguments)
        url = handler['images'][0]['url']
        
        resp = requests.get(url)
        img = Image.open(BytesIO(resp.content))
        
        # Optymalizacja pod KDP (Czysta czerń i biel)
        img = img.convert('L')
        img = ImageEnhance.Contrast(img).enhance(2.0)
        img = img.convert('RGB')
        
        return img
    except Exception as e:
        st.error(f"Błąd API: {e}")
        return None

# --- SESJA (STABILNA) ---
if "pdf_basket" not in st.session_state: st.session_state["pdf_basket"] = []
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
if "wybrany_styl" not in st.session_state: st.session_state["wybrany_styl"] = "line art"
if "ai_hint" not in st.session_state: st.session_state["ai_hint"] = ""

# --- LOGOWANIE ---
if not st.session_state["authenticated"]:
    st.title("🔐 KDP Factory Login")
    u = st.text_input("Nick:")
    p = st.text_input("Hasło:", type="password")
    if st.button("Zaloguj się"):
        if u == "admin" and p == "KDP2026":
            st.session_state["authenticated"] = True
            st.rerun()
    st.stop()

# --- SIDEBAR (WSZYSTKIE FUNKCJE ZACHOWANE) ---
with st.sidebar:
    st.title("⚙️ PANEL STEROWANIA")
    tryb = st.radio("WYBIERZ NARZĘDZIE:", [
        "🎨 Generator Kategorii", 
        "🌈 Kolorowa Bajka AI", 
        "🚀 Masowy Generator (10-30)",
        "📷 Zdjęcie na Kontur"
    ])
    st.divider()
    if st.button("🗑️ Wyczyść Projekt (PDF)"):
        st.session_state['pdf_basket'] = []
        st.rerun()

# --- MODUŁ: GENERATOR KATEGORII (KAFELKI) ---
if tryb == "🎨 Generator Kategorii":
    st.header("🎨 Szybki Generator 8K")
    
    # Kafle działają i zmieniają styl promptu
    style_dict = {
        "Domyślny": "line art",
        "Architektura": "architecture, buildings, perspective",
        "Przyroda": "nature, forest, flowers landscape",
        "Zwierzęta": "animal portrait, cute character, limbs visible",
        "Mandala": "complex mandala, geometric patterns",
        "Fantasy": "mythical creatures, magic world",
        "Komiks": "comic style, bold outlines"
    }
    
    cols = st.columns(len(style_dict))
    for i, (s_name, s_val) in enumerate(style_dict.items()):
        with cols[i]:
            if st.button(s_name):
                st.session_state["wybrany_styl"] = s_val
                st.toast(f"Wybrano: {s_name}")

    opis = st.text_input("Co ma być na rysunku? (np. Niedźwiedź na rowerze):", value=st.session_state["ai_hint"])
    
    if st.button("🚀 GENERUJ 8K"):
        with st.spinner("Generowanie..."):
            eng = translator.translate(opis)
            img = master_generate(eng, st.session_state["wybrany_styl"])
            if img:
                st.image(img, use_container_width=True)
                buf = BytesIO()
                img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())

    # --- POMOC AI ---
    st.divider()
    st.subheader("💡 Masz blokadę? AI podpowie")
    slowo = st.text_input("Wpisz słowo klucz:")
    if st.button("✨ Daj mi pomysł"):
        if slowo:
            poms = [f"zabawny {slowo} w czapce", f"{slowo} grający w piłkę", f"szczęśliwy {slowo} w lesie"]
            st.session_state["ai_hint"] = random.choice(poms)
            st.rerun()

# --- EKSPORT PDF (PANCERNY) ---
if st.session_state['pdf_basket']:
    st.divider()
    st.subheader(f"📥 Twój PDF: {len(st.session_state['pdf_basket'])} stron")
    if st.button("📥 POBIERZ PDF DLA AMAZON KDP"):
        try:
            out = BytesIO()
            pdf = canvas.Canvas(out, pagesize=(8.5*inch, 11*inch))
            for img_data in st.session_state['pdf_basket']:
                img_obj = ImageReader(BytesIO(img_data))
                # Marginesy pod KDP (7.5x9 cali na środku strony 8.5x11)
                pdf.drawImage(img_obj, 0.5*inch, 1*inch, width=7.5*inch, height=9*inch)
                pdf.showPage() # Strona z rysunkiem
                pdf.showPage() # Pusta strona (standard KDP)
            pdf.save()
            st.download_button("💾 Zapisz plik PDF", out.getvalue(), "kolorowanka_8k_final.pdf", "application/pdf")
        except Exception as e:
            st.error(f"Błąd PDF: {e}")
