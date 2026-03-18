import streamlit as st
import os
import fal_client
from deep_translator import GoogleTranslator
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import requests
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# --- KONFIGURACJA ---
os.environ["FAL_KEY"] = "cf0a6c98-7933-45df-918d-5757b24e9a30:afc267a3e94340879464bbea2862b40b"
st.set_page_config(page_title="KDP Factory Pro 8K", layout="wide")
translator = GoogleTranslator(source='pl', target='en')

# --- MAGICZNA PAŁECZKA (SZTYWNE 8K I ZERO CIENI) ---
def ulepsz_prompt_kdp(tekst, styl, czy_kolor=False):
    if czy_kolor:
        jakosc = "vibrant colors, storybook illustration, highly detailed, 8k resolution, masterpiece"
    else:
        # Tu jest "ściana" parametrów, żeby nie wyszedł render jak z tym autem
        jakosc = "clean line art, coloring book page, heavy thick black outlines, pure white background, NO shading, NO gradients, NO grey, pure black and white, smooth lines, 8k"
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
            # Agresywne czyszczenie z szarości
            img = ImageEnhance.Contrast(img).enhance(5.0) 
            img = img.point(lambda p: 255 if p > 140 else 0, mode='1') 
            img = img.convert('L')
        
        w, h = img.size
        img = img.resize((w*2, h*2), resample=Image.LANCZOS)
        return img
    except Exception as e:
        st.error(f"Błąd: {e}")
        return None

# --- BAZA I LOGOWANIE ---
if "pdf_basket" not in st.session_state: st.session_state["pdf_basket"] = []
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
if "wybrany_styl" not in st.session_state: st.session_state["wybrany_styl"] = "Domyślny"

if not st.session_state["authenticated"]:
    # Logowanie z Twojego kodu
    st.title("🔐 KDP Factory Login")
    u = st.text_input("Nick:")
    p = st.text_input("Hasło:", type="password")
    if st.button("Zaloguj się"):
        if u == "admin" and p == "KDP2026":
            st.session_state["authenticated"] = True
            st.session_state["user_nick"] = u
            st.rerun()
    st.stop()

# --- SIDEBAR (WIDOCZNY, NIE ROZSUWANY) ---
with st.sidebar:
    st.title(f"👤 {st.session_state['user_nick']}")
    # Radio zamiast selectbox, żeby opcje były od razu widoczne
    tryb = st.radio("MENU:", [
        "🎨 Generator Kategorii", 
        "🌈 Kolorowa Bajka AI", 
        "🚀 Masowy Generator (10-30)",
        "📷 Zdjęcie na Kontur",
        "💬 Forum",
        "⚖️ Regulamin"
    ])
    
    st.divider()
    if st.button("🗑️ Wyczyść Projekt"):
        st.session_state['pdf_basket'] = []
        st.rerun()

# --- MODUŁ: GENERATOR KATEGORII (KAFELKI) ---
if tryb == "🎨 Generator Kategorii":
    st.header("🎨 Wybierz Styl i Opisz Wizję")
    
    # KAFELKI STYLU (Od razu widoczne)
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
    
    opis = st.text_input("Twoja wizja (np. Kot na wakacjach):")
    
    if st.button("🚀 GENERUJ (8K CZYSZCZENIE)"):
        with st.spinner("Pracuję..."):
            eng = translator.translate(opis)
            img = master_generate(eng, st.session_state["wybrany_styl"], is_color=False)
            if img:
                st.image(img)
                buf = BytesIO()
                img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())

# --- MODUŁ: KOLOROWA BAJKA ---
elif tryb == "🌈 Kolorowa Bajka AI":
    st.header("📖 Bajka w Kolorze (8K)")
    f_photo = st.file_uploader("Zdjęcie dziecka:", type=['jpg', 'png'])
    imię = st.text_input("Imię bohatera:")
    fabula = st.text_area("O czym bajka?")
    
    if st.button("GENERUJ KOLOROWĄ ILUSTRACJĘ"):
        with st.spinner("Tworzę magię..."):
            p_b = f"Fairytale about {imię}, {fabula}, character inspired by photo"
            img = master_generate(p_b, "Storybook", is_color=True)
            if img:
                st.image(img)
                buf = BytesIO()
                img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())

# --- MODUŁ: MASOWY GENERATOR ---
elif tryb == "🚀 Masowy Generator (10-30)":
    st.header("🚀 Masowa Produkcja 8K")
    niche = st.text_input("Temat serii:")
    ile = st.select_slider("Ile stron?", options=[10, 20, 30])
    
    if st.button("ODPAL MASZYNĘ"):
        bar = st.progress(0)
        eng_n = translator.translate(niche)
        for i in range(ile):
            img = master_generate(f"{eng_n} variant {i}", "Coloring book", is_color=False)
            if img:
                buf = BytesIO()
                img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())
            bar.progress((i+1)/ile)

# --- EKSPORT PDF ---
if st.session_state['pdf_basket']:
    st.divider()
    if st.button("📥 POBIERZ PDF (Standard Amazon KDP)"):
        out = BytesIO()
        pdf = canvas.Canvas(out, pagesize=(8.5*inch, 11*inch))
        for d in st.session_state['pdf_basket']:
            pdf.drawImage(BytesIO(d), 0.5*inch, 1*inch, width=7.5*inch, height=9*inch)
            pdf.showPage()
            pdf.showPage() # Pusta strona
        pdf.save()
        st.download_button("Zapisz plik PDF", out.getvalue(), "projekt_kdp.pdf")
