import streamlit as st
import os
import fal_client
from deep_translator import GoogleTranslator
from PIL import Image
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

# --- KLUCZ DO JAKOŚCI 8K (Naprawiony prompt i brak psucia obrazu) ---
def master_generate(prompt, styl_wybrany):
    try:
        # Ten prompt wymusza ultra jakość bez szarości
        final_p = f"Coloring book page for KDP, {styl_wybrany}, {prompt}, thick black outlines, pure white background, 8k resolution, high contrast, clean professional line art, no shading, no background noise, masterpiece"
        
        arguments = {"prompt": final_p}
        handler = fal_client.subscribe("fal-ai/flux/schnell", arguments=arguments)
        url = handler['images'][0]['url']
        
        resp = requests.get(url)
        img = Image.open(BytesIO(resp.content))
        
        # NIE konwertujemy na '1' (to psuło jakość na zdjęciach!)
        # Zostawiamy czyste RGB z wysokim kontrastem
        return img
    except Exception as e:
        st.error(f"Błąd API: {e}")
        return None

# --- SESJA I LOGOWANIE ---
if "pdf_basket" not in st.session_state: st.session_state["pdf_basket"] = []
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
if "wybrany_styl" not in st.session_state: st.session_state["wybrany_styl"] = "Domyślny"
if "ai_hint" not in st.session_state: st.session_state["ai_hint"] = ""

if not st.session_state["authenticated"]:
    st.title("🔐 KDP Factory Login")
    u = st.text_input("Nick:")
    p = st.text_input("Hasło:", type="password")
    if st.button("Zaloguj się"):
        if u == "admin" and p == "KDP2026":
            st.session_state["authenticated"] = True
            st.rerun()
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ PANEL")
    tryb = st.radio("MENU:", ["🎨 Generator Kategorii", "🌈 Bajka AI", "🚀 Masowy Generator"])
    if st.button("🗑️ Wyczyść Wszystko"):
        st.session_state['pdf_basket'] = []
        st.rerun()

# --- GŁÓWNY GENERATOR (NAPRAWIONE KAFLE I JAKOŚĆ) ---
if tryb == "🎨 Generator Kategorii":
    st.header("🎨 Szybki Generator 8K")
    
    # Naprawione kafle - teraz styl faktycznie zmienia prompt!
    style = {
        "Domyślny": "minimalist line art", 
        "Architektura": "detailed architecture buildings", 
        "Przyroda": "forest and nature landscape", 
        "Zwierzęta": "animal portrait", 
        "Mandala": "complex mandala pattern", 
        "Fantasy": "magic fantasy world", 
        "Komiks": "comic book style outlines"
    }
    
    cols = st.columns(len(style))
    for i, (s_name, s_val) in enumerate(style.items()):
        with cols[i]:
            if st.button(f"{s_name}"):
                st.session_state["wybrany_styl"] = s_val
                st.toast(f"Wybrano styl: {s_name}")

    opis = st.text_input("Co narysować?", value=st.session_state["ai_hint"])
    
    if st.button("🚀 GENERUJ 8K"):
        with st.spinner("Generowanie żyletki 8K..."):
            eng = translator.translate(opis)
            img = master_generate(eng, st.session_state["wybrany_styl"])
            if img:
                st.image(img, use_container_width=True)
                buf = BytesIO()
                img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())

    # --- POMOC AI ---
    st.divider()
    st.subheader("💡 Pomoc AI")
    slowo = st.text_input("Wpisz słowo:")
    if st.button("✨ Podpowiedz"):
        if slowo:
            poms = [f"{slowo} w stylu zen", f"szczegółowy {slowo} dla dorosłych", f"bajkowy {slowo}"]
            st.session_state["ai_hint"] = random.choice(poms)
            st.rerun()

# --- EKSPORT PDF (NAPRAWIONY BŁĄD Z BYTESIO) ---
if st.session_state['pdf_basket']:
    st.divider()
    if st.button("📥 POBIERZ PDF (AMAZON KDP)"):
        try:
            output = BytesIO()
            c = canvas.Canvas(output, pagesize=(8.5*inch, 11*inch))
            for img_bytes in st.session_state['pdf_basket']:
                # Użycie ImageReader rozwiązuje błąd ze zdjęcia
                img_reader = ImageReader(BytesIO(img_bytes))
                c.drawImage(img_reader, 0.5*inch, 1*inch, width=7.5*inch, height=9*inch)
                c.showPage()
                c.showPage() # Pusta strona pod KDP
            c.save()
            st.download_button("💾 Pobierz gotowy plik", output.getvalue(), "kdp_project.pdf", "application/pdf")
        except Exception as e:
            st.error(f"Błąd PDF: {e}")
