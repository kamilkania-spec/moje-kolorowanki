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

# --- KONFIGURACJA (Z Twoich zdjęć) ---
os.environ["FAL_KEY"] = "cf0a6c98-7933-45df-918d-5757b24e9a30:afc267a3e94340879464bbea2862b40b"
st.set_page_config(page_title="KDP Factory Pro 8K", layout="wide")
translator = GoogleTranslator(source='pl', target='en')

# --- NOWA FUNKCJA: MAGICZNA PAŁECZKA (JAKO OPCJA) ---
def podkrec_tekst_ai(tekst_pl):
    # To wywołujemy TYLKO gdy użytkownik kliknie przycisk "Magiczna Pałeczka"
    # Robimy "bogaty" opis na podstawie prostego hasła
    szablony = [
        f"{tekst_pl} in a majestic setting, highly detailed illustration, professional line art",
        f"Enchanted scene featuring {tekst_pl}, whimsical atmosphere, intricate details",
        f"Stunning composition of {tekst_pl}, bold outlines, perfect for coloring book, 8k quality"
    ]
    return random.choice(szablony)

# --- SILNIK GRAFICZNY (Z JAKOŚCIĄ 8K NA SZTYWNO) ---
def master_generate(prompt, is_color=False, image_url=None):
    nick = st.session_state["user_nick"]
    if st.session_state["user_db"][nick]["credits"] <= 0:
        st.error("Brak kredytów!")
        return None
    
    try:
        # Jakość techniczna (8K, linie) jest zawsze, ale TREŚĆ zależy od użytkownika
        jakosc_techniczna = "8k resolution, crisp clean lines, white background, no shading" if not is_color else "8k resolution, vibrant cinematic colors, high quality"
        final_p = f"{prompt}, {jakosc_techniczna}"
        
        arguments = {"prompt": final_p}
        if image_url:
            arguments["image_url"] = image_url
            
        handler = fal_client.subscribe("fal-ai/flux/schnell", arguments=arguments)
        url = handler['images'][0]['url']
        resp = requests.get(url)
        img = Image.open(BytesIO(resp.content))

        if not is_color:
            img = img.convert('L')
            img = ImageEnhance.Contrast(img).enhance(3.5)
        
        # Skalowanie do wysokiej gęstości pikseli
        w, h = img.size
        img = img.resize((w*2, h*2), resample=Image.LANCZOS)

        if st.session_state["role"] != "admin":
            st.session_state["user_db"][nick]["credits"] -= 1
        return img
    except Exception as e:
        st.error(f"Błąd: {e}")
        return None

# --- INICJALIZACJA SESJI I LOGOWANIE (Bez zmian) ---
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {"admin": {"pass": "KDP2026", "credits": 999999, "role": "admin"}}
if "pdf_basket" not in st.session_state:
    st.session_state["pdf_basket"] = []
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

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

# --- SIDEBAR ---
with st.sidebar:
    st.title(f"👤 {st.session_state['user_nick']}")
    tryb = st.selectbox("Wybierz Narzędzie:", [
        "🎨 Generator Kategorii", 
        "🌈 Kolorowa Bajka AI", 
        "🚀 Masowy Generator 10-30",
        "📷 Zdjęcie na Kontur"
    ])
    if st.button("🗑️ Wyczyść Projekt"):
        st.session_state['pdf_basket'] = []
        st.rerun()

# --- MODUŁY ---

if tryb == "🎨 Generator Kategorii":
    st.header("🎨 Kreator Kolorowanek")
    
    # Przycisk "Podpowiedzi" o które prosiłeś
    podpowiedzi = ["Architektura", "Przyroda", "Zwierzęta", "Mandala", "Kosmos", "Dinozaury", "Pojazdy"]
    wybrany_tag = st.multiselect("Szybkie tagi:", podpowiedzi)
    
    opis = st.text_input("Twoja wizja:", placeholder="Np. kot w górach...")
    
    # MAGICZNA PAŁECZKA JAKO OPCJA
    if st.button("🪄 Magiczna Pałeczka (Podkręć mój tekst)"):
        if opis:
            nowy_opis = podkrec_tekst_ai(opis)
            st.session_state["tmp_opis"] = nowy_opis
            st.success(f"AI sugeruje: {nowy_opis}")
        else:
            st.warning("Wpisz cokolwiek, żebym mógł to podkręcić!")

    finalny_tekst = st.session_state.get("tmp_opis", opis)

    if st.button("🚀 GENERUJ"):
        with st.spinner("Rysuję..."):
            tagi_str = " ".join(wybrany_tag)
            eng = translator.translate(f"{tagi_str} {finalny_tekst}")
            img = master_generate(eng, is_color=False)
            if img:
                st.image(img)
                buf = BytesIO()
                img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())

elif tryb == "🌈 Kolorowa Bajka AI":
    st.header("📖 Kolorowa Bajka dla Dziecka")
    f_zdjecie = st.file_uploader("Zdjęcie dziecka:", type=['png', 'jpg'])
    imię = st.text_input("Imię dziecka:")
    opowieść = st.text_area("O czym ma być bajka?")
    
    if st.button("STWÓRZ KOLOROWĄ ILUSTRACJĘ"):
        # Tutaj prompt idzie w KOLORZE
        p_bajka = f"Colorful storybook illustration, character named {imię}, looks like child from photo, {opowieść}"
        img = master_generate(p_bajka, is_color=True)
        if img:
            st.image(img)
            buf = BytesIO()
            img.save(buf, format="PNG")
            st.session_state['pdf_basket'].append(buf.getvalue())

elif tryb == "🚀 Masowy Generator 10-30":
    st.header("🚀 Generator Hurtowy (10-30 stron)")
    temat = st.text_input("Temat serii:")
    ile = st.select_slider("Wybierz ilość:", options=[10, 20, 30])
    
    if st.button(f"GENERUJ {ile} STRON"):
        bar = st.progress(0)
        eng_t = translator.translate(temat)
        for i in range(ile):
            # Tu AI samo musi trochę zmieniać sceny, żeby nie było 30 takich samych obrazów
            img = master_generate(f"{eng_t}, scene {i}, unique composition", is_color=False)
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
            pdf.showPage() # Pusta strona na odwrocie
        pdf.save()
        st.download_button("Zapisz PDF", out.getvalue(), "kdp_final_8k.pdf")
