import streamlit as st
import os
import fal_client
from deep_translator import GoogleTranslator
from PIL import Image, ImageEnhance
import requests
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import random

# --- KONFIGURACJA ---
os.environ["FAL_KEY"] = "cf0a6c98-7933-45df-918d-5757b24e9a30:afc267a3e94340879464bbea2862b40b"
st.set_page_config(page_title="KDP Factory Pro 8K", layout="wide")
translator = GoogleTranslator(source='pl', target='en')

# --- LOGIKA GENEROWANIA (Czyste 8K) ---
def master_generate(prompt, styl_wybrany, is_color=False):
    try:
        # Sztywny prompt na czyste linie
        if is_color:
            jakosc = "vibrant colors, storybook illustration, 8k resolution"
        else:
            jakosc = "coloring book page, heavy thick black outlines, white background, NO shading, NO grey, 8k"
        
        final_p = f"{styl_wybrany} {prompt}, {jakosc}"
        arguments = {"prompt": final_p}
        handler = fal_client.subscribe("fal-ai/flux/schnell", arguments=arguments)
        url = handler['images'][0]['url']
        resp = requests.get(url)
        img = Image.open(BytesIO(resp.content))

        # Obróbka na ultra-kontur
        if not is_color:
            img = img.convert('L')
            img = ImageEnhance.Contrast(img).enhance(5.0)
            img = img.point(lambda p: 255 if p > 140 else 0, mode='1')
            img = img.convert('RGB') # PDF lubi RGB nawet dla czarno-białych
        
        # Skalowanie do 8K (LANCZOS)
        w, h = img.size
        img = img.resize((w*2, h*2), resample=Image.LANCZOS)
        return img
    except Exception as e:
        st.error(f"Błąd API: {e}")
        return None

# --- SESJA ---
if "pdf_basket" not in st.session_state: st.session_state["pdf_basket"] = []
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
if "wybrany_styl" not in st.session_state: st.session_state["wybrany_styl"] = "Domyślny"
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

# --- SIDEBAR (WIDOCZNY, NIE ROZSUWANY) ---
with st.sidebar:
    st.title("⚙️ PANEL")
    tryb = st.radio("MENU:", [
        "🎨 Generator Kategorii", 
        "🌈 Kolorowa Bajka AI", 
        "🚀 Masowy Generator (10-30)",
        "📷 Zdjęcie na Kontur"
    ])
    st.divider()
    if st.button("🗑️ Wyczyść Projekt"):
        st.session_state['pdf_basket'] = []
        st.rerun()

# --- MODUŁ GŁÓWNY ---
if tryb == "🎨 Generator Kategorii":
    st.header("🎨 Wybierz Styl i Opisz Wizję")
    
    # KAFELKI (OD RAZU WIDOCZNE)
    style = {
        "Domyślny": "🎨", "Architektura": "🏛️", "Przyroda": "🌿", 
        "Zwierzęta": "🦁", "Mandala": "☸️", "Fantasy": "🧙", "Komiks": "💥"
    }
    
    cols = st.columns(len(style))
    for i, (s_name, s_icon) in enumerate(style.items()):
        with cols[i]:
            if st.button(f"{s_icon}\n{s_name}"):
                st.session_state["wybrany_styl"] = s_name

    st.write(f"Wybrany styl: **{st.session_state['wybrany_styl']}**")
    
    opis = st.text_input("Twoja wizja:", value=st.session_state["ai_hint"])
    
    if st.button("🚀 GENERUJ 8K"):
        with st.spinner("Generowanie..."):
            eng = translator.translate(opis)
            img = master_generate(eng, st.session_state["wybrany_styl"])
            if img:
                st.image(img)
                # Zapisujemy jako PNG do koszyka
                buf = BytesIO()
                img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())

    # --- OKIENKO POMOCY AI ---
    st.divider()
    st.subheader("💡 Nie masz pomysłu? Napisz słowo, AI Ci pomoże")
    slowo = st.text_input("Wpisz słowo (np. KOT):")
    if st.button("✨ Podpowiedz mi"):
        if slowo:
            poms = [f"{slowo} w magicznym lesie", f"mały uroczy {slowo}", f"{slowo} jako superbohater"]
            st.session_state["ai_hint"] = random.choice(poms)
            st.rerun()

# --- EKSPORT PDF (FIXED!) ---
if st.session_state['pdf_basket']:
    st.divider()
    st.subheader("📥 Pobierz Gotowy Projekt")
    if st.button("📥 POBIERZ PDF DO AMAZON KDP"):
        try:
            output = BytesIO()
            # Ustawiamy rozmiar strony 8.5 x 11 cali (Standard Amazon KDP)
            c = canvas.Canvas(output, pagesize=(8.5*inch, 11*inch))
            
            for img_bytes in st.session_state['pdf_basket']:
                # KLUCZOWA POPRAWKA: Zamiana bajtów na obiekt obrazu dla reportlab
                img_io = BytesIO(img_bytes)
                c.drawImage(ImageReader(img_io), 0.5*inch, 1*inch, width=7.5*inch, height=9*inch)
                c.showPage() # Obrazek
                c.showPage() # Pusta strona (standard KDP)
                
            c.save()
            st.download_button("💾 Zapisz plik PDF", output.getvalue(), "kolorowanka_8k.pdf", "application/pdf")
        except Exception as e:
            st.error(f"Coś poszło nie tak z PDF: {e}")

# Dodatkowy import wymagany do poprawki PDF
from reportlab.lib.utils import ImageReader
