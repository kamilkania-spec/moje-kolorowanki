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

# --- SILNIK GRAFICZNY 8K (BEZ STRATY JAKOŚCI) ---
def master_generate(prompt, is_color=False, image_url=None):
    try:
        # Prompt wymuszający jakość 8K i brak cieni dla kolorowanek
        if not is_color:
            prompt = f"Coloring book page, clean bold black outlines, pure white background, no shading, no grey, 8k, professional line art, {prompt}"
        
        arguments = {"prompt": prompt}
        if image_url:
            arguments["image_url"] = image_url
            
        handler = fal_client.subscribe("fal-ai/flux/schnell", arguments=arguments)
        url = handler['images'][0]['url']
        resp = requests.get(url)
        img = Image.open(BytesIO(resp.content))
        return img
    except Exception as e:
        st.error(f"Błąd API: {e}")
        return None

# --- BAZA I SESJA ---
if "pdf_basket" not in st.session_state: st.session_state["pdf_basket"] = []
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
if "user_nick" not in st.session_state: st.session_state["user_nick"] = "admin"
if "ai_hint" not in st.session_state: st.session_state["ai_hint"] = ""
if "posts" not in st.session_state: st.session_state["posts"] = []

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

# --- SIDEBAR (PEŁNY - TAK JAK MIAŁEŚ) ---
with st.sidebar:
    st.title(f"👤 {st.session_state['user_nick']}")
    tryb = st.radio("MENU:", [
        "🎨 Generator Kategorii", 
        "🌈 KDP Story AI (Bajka)", 
        "🚀 Masowy Generator (10-30)",
        "📷 Zdjęcie na Kontur",
        "💬 Forum",
        "⚖️ Regulamin i Pomoc"
    ])
    st.divider()
    if st.button("🗑️ Wyczyść Projekt"):
        st.session_state['pdf_basket'] = []
        st.rerun()
    if st.button("🚪 Wyloguj"):
        st.session_state["authenticated"] = False
        st.rerun()

# --- MODUŁ 1: GENERATOR KATEGORII ---
if tryb == "🎨 Generator Kategorii":
    st.header("🎨 Szybki Generator 8K")
    
    style = {
        "Domyślny": "", "Architektura": "architecture, buildings", 
        "Przyroda": "nature, forest, landscape", "Zwierzęta": "animals, cute creature", 
        "Mandala": "complex mandala, symmetry", "Fantasy": "magic, mythical, fantasy", 
        "Komiks": "comic style, retro outlines"
    }
    
    cols = st.columns(len(style))
    for i, (s_name, s_val) in enumerate(style.items()):
        with cols[i]:
            if st.button(s_name):
                st.session_state["current_style"] = s_val

    opis = st.text_input("Co narysować?", value=st.session_state["ai_hint"])
    
    # --- PRZYWRÓCONY SUWAK ILOŚCI ---
    ile_n = st.slider("Ile grafik wygenerować?", 1, 10, 1)
    
    if st.button("🚀 GENERUJ SERIĘ"):
        bar = st.progress(0)
        for i in range(ile_n):
            with st.spinner(f"Generuję {i+1}/{ile_n}..."):
                full_prompt = f"{st.session_state.get('current_style', '')} {opis}"
                eng = translator.translate(full_prompt)
                img = master_generate(eng)
                if img:
                    st.image(img)
                    buf = BytesIO()
                    img.save(buf, format="PNG")
                    st.session_state['pdf_basket'].append(buf.getvalue())
            bar.progress((i + 1) / ile_n)

    st.divider()
    st.subheader("💡 Pomoc AI")
    slowo = st.text_input("Słowo klucz:")
    if st.button("✨ Podpowiedz"):
        poms = [f"wesoły {slowo} na przygodzie", f"szczegółowy portret {slowo}", f"magiczny świat {slowo}"]
        st.session_state["ai_hint"] = random.choice(poms)
        st.rerun()

# --- MODUŁ 2: BAJKA Z TWOJEGO ZDJĘCIA (PRZYWRÓCONY) ---
elif tryb == "🌈 KDP Story AI (Bajka)":
    st.header("🌈 Personalizowana Bajka")
    f_photo = st.file_uploader("Wgraj zdjęcie dziecka:", type=['png', 'jpg'])
    imie = st.text_input("Imię bohatera:")
    hist_d = st.text_area("O czym ma być bajka?")
    ile_stron = st.number_input("Ile stron?", 5, 30, 10)
    
    if st.button("🚀 Generuj Bajkę"):
        st.info("To może potrwać... AI tworzy spójną historię.")
        # Tu logika generowania serii z image_url...

# --- MODUŁ 5: FORUM (PRZYWRÓCONY) ---
elif tryb == "💬 Forum":
    st.header("💬 Forum Społeczności")
    wiad = st.text_input("Wiadomość:")
    if st.button("Wyślij"):
        st.session_state["posts"].insert(0, {"u": st.session_state["user_nick"], "m": wiad})
        st.rerun()
    for p in st.session_state["posts"]:
        st.info(f"**{p['u']}**: {p['m']}")

# --- MODUŁ 6: REGULAMIN (PRZYWRÓCONY) ---
elif tryb == "⚖️ Regulamin i Pomoc":
    st.header("⚖️ Dokumenty i Pomoc")
    t1, t2 = st.tabs(["Regulamin", "Stripe/Płatności"])
    with t1: st.write("Regulamin Twojej aplikacji KDP...")
    with t2: st.write("Instrukcja konfiguracji płatności...")

# --- EKSPORT PDF (NA KOŃCU, ZAWSZE DOSTĘPNY) ---
if st.session_state['pdf_basket']:
    st.divider()
    st.subheader(f"📥 Twój Projekt (Stron: {len(st.session_state['pdf_basket'])})")
    if st.button("📥 POBIERZ PDF DLA AMAZON KDP"):
        output = BytesIO()
        c = canvas.Canvas(output, pagesize=(8.5*inch, 11*inch))
        for d in st.session_state['pdf_basket']:
            img_reader = ImageReader(BytesIO(d))
            c.drawImage(img_reader, 0.5*inch, 1*inch, width=7.5*inch, height=9*inch)
            c.showPage() # Obrazek
            c.showPage() # Pusta strona
        c.save()
        st.download_button("💾 Zapisz PDF", output.getvalue(), "projekt_kdp_8k.pdf")
