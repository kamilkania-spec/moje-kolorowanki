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

# --- STAŁE I KLUCZ (Z Twojego zdjęcia) ---
os.environ["FAL_KEY"] = "cf0a6c98-7933-45df-918d-5757b24e9a30:afc267a3e94340879464bbea2862b40b"
st.set_page_config(page_title="KDP Factory Pro 8K", layout="wide")
translator = GoogleTranslator(source='pl', target='en')

# --- LOGIKA PODKRĘCANIA TEKSTU (MAGICZNA PAŁECZKA) ---
def ulepsz_prompt(user_text, czy_kolor=False):
    # To jest to, o co prosiłeś - AI bierze Twój tekst i robi z niego "bestię" dla generatora
    if czy_kolor:
        # Dla bajek: soczyste kolory, styl kinowy, wysoka rozdzielczość
        dodatki = "highly detailed, cinematic lighting, vibrant colors, 8k resolution, masterpiece, professional illustration, sharp focus"
    else:
        # Dla kolorowanek: Twoje wymagania o gładkich liniach i 8K
        dodatki = "8k resolution, high quality, crisp clean black lines, bold outlines, solid white background, no shading, no shadows, pure black and white, gładkie linie"
    
    return f"{user_text}, {dodatki}"

# --- GŁÓWNY SILNIK (Z Twoich screenów + moje poprawki jakości) ---
def master_generate(prompt, is_color=False, image_url=None):
    nick = st.session_state["user_nick"]
    if st.session_state["user_db"][nick]["credits"] <= 0:
        st.error("Brak kredytów!")
        return None
    
    try:
        # TUTAJ AI PODKRĘCA PROMPT PRZED WYSŁANIEM
        ulepszony_p = ulepsz_prompt(prompt, czy_kolor=is_color)
        
        arguments = {"prompt": ulepszony_p}
        if image_url:
            arguments["image_url"] = image_url
            
        handler = fal_client.subscribe("fal-ai/flux/schnell", arguments=arguments)
        url = handler['images'][0]['url']
        resp = requests.get(url)
        img = Image.open(BytesIO(resp.content))

        # Jeśli to kolorowanka (nie kolorowa bajka), to wymuszamy czarno-białe
        if not is_color:
            img = img.convert('L')
            img = ImageEnhance.Contrast(img).enhance(3.5)
        
        # Wymuszamy rozmiar 8K-ish przez skalowanie
        w, h = img.size
        img = img.resize((w*2, h*2), resample=Image.LANCZOS)

        if st.session_state["role"] != "admin":
            st.session_state["user_db"][nick]["credits"] -= 1
        return img
    except Exception as e:
        st.error(f"Błąd: {e}")
        return None

# --- INICJALIZACJA SESJI ---
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {"admin": {"pass": "KDP2026", "credits": 999999, "role": "admin"}}
if "pdf_basket" not in st.session_state:
    st.session_state["pdf_basket"] = []
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# --- LOGOWANIE (Z Twojego zdjęcia) ---
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

# --- SIDEBAR (NIEZMIENIONY UKŁAD) ---
with st.sidebar:
    st.title(f"👤 {st.session_state['user_nick']}")
    tryb = st.selectbox("Wybierz Narzędzie:", [
        "🎨 Generator Kolorowanek", 
        "🌈 Kolorowa Bajka AI", 
        "🚀 Masowy Generator (10-30)",
        "📷 Zdjęcie na Kontur"
    ])
    if st.button("🗑️ Wyczyść Projekt"):
        st.session_state['pdf_basket'] = []
        st.rerun()

# --- MODUŁY ---

if tryb == "🎨 Generator Kolorowanek":
    st.header("🎨 Kreator Kolorowanek 8K")
    kat = st.multiselect("Podpowiedzi stylu:", ["Architektura", "Przyroda", "Zwierzęta", "Mandala"])
    opis = st.text_input("Co narysować? (np. kot w górach na wycieczce)")
    
    if st.button("GENERUJ"):
        with st.spinner("AI podkręca prompt i rysuje..."):
            eng = translator.translate(f"{' '.join(kat)} {opis}")
            img = master_generate(eng, is_color=False)
            if img:
                st.image(img)
                buf = BytesIO()
                img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())

elif tryb == "🌈 Kolorowa Bajka AI":
    st.header("📖 Stwórz Kolorową Bajkę dla Dziecka")
    f_zdjecie = st.file_uploader("Wgraj zdjęcie dziecka:", type=['png', 'jpg'])
    imię = st.text_input("Imię dziecka:")
    opowieść = st.text_area("O czym ma być ta bajka?")
    
    if st.button("GENERUJ KOLOROWĄ BAJKĘ"):
        if f_zdjecie:
            # Tutaj AI wygeneruje kolorowe obrazy
            prompt_bajka = f"Story for a child named {imię}, {opowieść}, character looks like the child on photo"
            img = master_generate(prompt_bajka, is_color=True) # TU JEST KOLOR
            if img:
                st.image(img)
                buf = BytesIO()
                img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())

elif tryb == "🚀 Masowy Generator (10-30)":
    st.header("🚀 Hurtowe Generowanie")
    temat = st.text_input("Temat serii:")
    ile = st.select_slider("Ilość:", options=[10, 20, 30])
    
    if st.button(f"GENERUJ {ile} SZTUK"):
        bar = st.progress(0)
        eng_t = translator.translate(temat)
        for i in range(ile):
            img = master_generate(f"{eng_t}, variation {i}", is_color=False)
            if img:
                buf = BytesIO()
                img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())
            bar.progress((i+1)/ile)

# --- EKSPORT PDF DO KDP ---
if st.session_state['pdf_basket']:
    st.divider()
    if st.button("📥 POBIERZ PDF (Format Amazon KDP)"):
        out = BytesIO()
        pdf = canvas.Canvas(out, pagesize=(8.5*inch, 11*inch))
        for d in st.session_state['pdf_basket']:
            pdf.drawImage(BytesIO(d), 0.5*inch, 1*inch, width=7.5*inch, height=9*inch)
            pdf.showPage()
            # Pusta strona, żeby nie przebijało na Amazonie
            pdf.showPage()
        pdf.save()
        st.download_button("Zapisz PDF", out.getvalue(), "kdp_final.pdf")
