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

# --- KONFIGURACJA ---
os.environ["FAL_KEY"] = "cf0a6c98-7933-45df-918d-5757b24e9a30:afc267a3e94340879464bbea2862b40b"
st.set_page_config(page_title="KDP Factory Pro 8K", layout="wide")
translator = GoogleTranslator(source='pl', target='en')

# --- FUNKCJA ULEPSZANIA PROMPTU ---
def ulepsz_prompt_kdp(tekst, styl, czy_kolor=False):
    if czy_kolor:
        jakosc = "vibrant colors, storybook illustration, highly detailed, 8k resolution, masterpiece"
    else:
        # TWOJE WYMAGANIA: Zero cieni, czyste linie
        jakosc = "line art style, coloring book page, heavy thick black outlines, pure white background, NO shading, NO shadows, NO gradients, NO grey, pure black and white, smooth lines, 8k"
    return f"{styl} {tekst}, {jakosc}"

# --- SILNIK GENERUJĄCY ---
def master_generate(prompt, styl_wybrany, is_color=False):
    try:
        final_p = ulepsz_prompt_kdp(prompt, styl_wybrany, czy_kolor=is_color)
        arguments = {"prompt": final_p}
        handler = fal_client.subscribe("fal-ai/flux/schnell", arguments=arguments)
        url = handler['images'][0]['url']
        resp = requests.get(url)
        img = Image.open(BytesIO(resp.content))

        if not is_color:
            img = img.convert('L')
            img = ImageEnhance.Contrast(img).enhance(5.0) 
            img = img.point(lambda p: 255 if p > 140 else 0, mode='1') 
            # KLUCZOWA POPRAWKA DLA PDF: Konwersja na RGB przed zapisem
            img = img.convert('RGB')
        
        w, h = img.size
        img = img.resize((w*2, h*2), resample=Image.LANCZOS)
        return img
    except Exception as e:
        st.error(f"Błąd API: {e}")
        return None

# --- BAZA I SESJA ---
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
            st.session_state["user_nick"] = u
            st.rerun()
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.title(f"👤 {st.session_state['user_nick']}")
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

# --- MODUŁ: GENERATOR KATEGORII ---
if tryb == "🎨 Generator Kategorii":
    st.header("🎨 Wybierz Styl i Opisz Wizję")
    
    style = {
        "Domyślny": "🎨", "Architektura": "🏛️", "Przyroda": "🌿", 
        "Zwierzęta": "🦁", "Mandala": "☸️", "Fantasy": "🧙", "Komiks": "💥"
    }
    
    col_style = st.columns(len(style))
    for i, (s_name, s_icon) in enumerate(style.items()):
        with col_style[i]:
            if st.button(f"{s_icon}\n{s_name}"):
                st.session_state["wybrany_styl"] = s_name

    st.info(f"Wybrany styl: **{st.session_state['wybrany_styl']}**")
    
    opis = st.text_input("Twoja wizja:", value=st.session_state["ai_hint"])
    
    if st.button("🚀 GENERUJ 8K"):
        with st.spinner("Pracuję..."):
            eng = translator.translate(opis)
            img = master_generate(eng, st.session_state["wybrany_styl"], is_color=False)
            if img:
                st.image(img)
                buf = BytesIO()
                img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())

    st.divider()
    st.subheader("💡 Nie masz pomysłu? Napisz słowo, AI Ci pomoże")
    slowo = st.text_input("Wpisz jedno słowo:", key="helper_input")
    
    if st.button("✨ Podpowiedz mi"):
        if slowo:
            pomysly = [f"{slowo} bawiący się w magicznym lesie", f"portret {slowo} fantasy", f"wesoły {slowo} na wakacjach"]
            st.session_state["ai_hint"] = random.choice(pomysly)
            st.rerun()

# --- EKSPORT PDF (Z NAPRAWIONYM BŁĘDEM TYPEERROR) ---
if st.session_state['pdf_basket']:
    st.divider()
    st.subheader("📥 Twój Projekt PDF")
    st.write(f"Ilość stron w kolejce: {len(st.session_state['pdf_basket'])}")
    
    if st.button("📥 POBIERZ PDF DO AMAZON KDP"):
        try:
            out = BytesIO()
            pdf = canvas.Canvas(out, pagesize=(8.5*inch, 11*inch))
            for d in st.session_state['pdf_basket']:
                # Rysowanie obrazu z bufora
                img_data = BytesIO(d)
                pdf.drawImage(img_data, 0.5*inch, 1*inch, width=7.5*inch, height=9*inch)
                pdf.showPage() # Strona z obrazkiem
                pdf.showPage() # Pusta strona (standard KDP)
            pdf.save()
            st.download_button("💾 Zapisz plik PDF na komputerze", out.getvalue(), "projekt_kdp_8k.pdf", mime="application/pdf")
        except Exception as e:
            st.error(f"Błąd podczas tworzenia PDF: {e}")
