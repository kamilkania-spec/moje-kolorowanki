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
import json

# --- KONFIGURACJA ---
os.environ["FAL_KEY"] = "cf0a6c98-7933-45df-918d-5757b24e9a30:afc267a3e94340879464bbea2862b40b"

st.set_page_config(page_title="KDP Factory ULTRA 8K - FULL SUITE", layout="wide")
translator = GoogleTranslator(source='pl', target='en')

# --- BAZA DANYCH (ZACHOWANA I ROZBUDOWANA) ---
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {
        "admin": {"pass": "KDP2026", "credits": 999999, "role": "admin"},
        "tester": {"pass": "KDP123", "credits": 50, "role": "user"}
    }
if "pdf_basket" not in st.session_state: st.session_state["pdf_basket"] = []
if "posts" not in st.session_state: st.session_state["posts"] = []
if "p_magic" not in st.session_state: st.session_state["p_magic"] = ""

# --- RDZEŃ GENERUJĄCY (POPRAWIONY BŁĄD IMAGE_SIZE) ---
def master_generate(prompt, is_color=False, image_url=None, is_cover=False):
    nick = st.session_state.get("user_nick", "admin")
    if st.session_state["user_db"][nick]["credits"] <= 0:
        st.error("❌ Brak kredytów!")
        return None
    try:
        # ROZWIĄZANIE TWOJEGO BŁĘDU: portrait_4_3 zamiast portrait_4_5
        size_val = "square_hd" if is_cover else "portrait_4_3"
            
        arguments = {
            "prompt": prompt,
            "image_size": size_val,
            "seed": random.randint(1, 999999)
        }
        if image_url: arguments["image_url"] = image_url
            
        handler = fal_client.subscribe("fal-ai/flux/schnell", arguments=arguments)
        url = handler['images'][0]['url']
        resp = requests.get(url)
        img = Image.open(BytesIO(resp.content))

        if not is_color:
            img = img.convert('L')
            img = ImageEnhance.Contrast(img).enhance(3.5)
            # Skalowanie do 8K (Lanczos)
            w, h = img.size
            img = img.resize((w*2, h*2), resample=Image.LANCZOS)
        
        if st.session_state.get("role") != "admin":
            st.session_state["user_db"][nick]["credits"] -= 1
        return img
    except Exception as e:
        st.error(f"⚠️ Błąd API: {e}")
        return None

# --- LOGOWANIE ---
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
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
    cred = st.session_state["user_db"][st.session_state['user_nick']]['credits']
    st.write(f"🌑 Kredyty: {'∞' if st.session_state['role'] == 'admin' else cred}")
    
    tryb = st.selectbox("Wybierz Narzędzie:", [
        "🎨 Generator Kategorii",
        "🪄 Magiczna Pałeczka (Seria)",
        "🦊 Niche Finder & SEO",
        "📖 KDP Story AI (Bajka - Kolor)",
        "🖍️ Story Mode (Bajka - Czarno-Biała)",
        "📸 Zdjęcie na Kontur",
        "🖼️ Generator Okładek",
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

# --- MODUŁY ---

if tryb == "🎨 Generator Kategorii":
    st.header("🎨 Szybki Generator 8K")
    kat = st.radio("Styl:", ["Dowolny", "Geometria", "Pejzaż", "Przyroda", "Architektura"], horizontal=True)
    opis = st.text_input("Opis:")
    if st.button("GENERUJ"):
        img = master_generate(f"Coloring book page, {kat} {translator.translate(opis)}, clean lines", is_color=False)
        if img:
            st.image(img)
            buf = BytesIO(); img.save(buf, format="PNG")
            st.session_state['pdf_basket'].append(buf.getvalue())

elif tryb == "🪄 Magiczna Pałeczka (Seria)":
    st.header("🪄 Magiczne Generowanie Serii")
    user_in = st.text_area("Twój pomysł:")
    ile = st.number_input("Ile sztuk?", 1, 50, 5)
    if st.button("Użyj Magii i Generuj"):
        p = f"Professional intricate coloring book page, {translator.translate(user_in)}, high contrast, 8k"
        bar = st.progress(0)
        for i in range(ile):
            img = master_generate(p, is_color=False)
            if img:
                buf = BytesIO(); img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())
                st.image(img, width=300)
            bar.progress((i+1)/ile)

elif tryb == "🦊 Niche Finder & SEO":
    st.header("🦊 Trendy i SEO")
    st.write("🔥 **Trendy USA/UK:** `Celestial Boho`, `Victorian Steampunk`, `Kawaii Food`")
    n_in = st.text_input("Wpisz niszcze:")
    if n_in:
        st.success(f"Tytuł: {n_in.capitalize()} Coloring Book")
        st.write(f"Tagi: {n_in}, coloring book, kdp, amazon, 2026")

elif tryb == "📖 KDP Story AI (Bajka - Kolor)":
    st.header("📖 Bajka z Twojego Zdjęcia (Kolorowa)")
    f_photo = st.file_uploader("Zdjęcie dziecka:", type=['png', 'jpg'])
    imię = st.text_input("Imię bohatera:")
    hist = st.text_area("Fabuła:")
    if f_photo and st.button("Generuj Bajkę"):
        url = fal_client.upload_image(f_photo.getvalue())
        for i in range(5):
            img = master_generate(f"Children's story book, {imię}, {hist}, page {i+1}, consistent face", is_color=True, image_url=url)
            if img:
                buf = BytesIO(); img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())
                st.image(img, width=300)

elif tryb == "🖍️ Story Mode (Bajka - Czarno-Biała)":
    st.header("🖍️ Cała Opowieść do Kolorowania")
    fabula = st.text_area("Opisz historię (np. Przygody dzielnego rycerza):")
    ile_s = st.number_input("Ile stron opowieści?", 5, 50, 10)
    if st.button("Generuj Książkę"):
        p_eng = translator.translate(fabula)
        bar = st.progress(0)
        for i in range(ile_s):
            p = f"Coloring book page, story scene {i+1} of {ile_s}, {p_eng}, consistent style, black and white"
            img = master_generate(p, is_color=False)
            if img:
                buf = BytesIO(); img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())
                st.image(img, width=300)
            bar.progress((i+1)/ile_s)

elif tryb == "📸 Zdjęcie na Kontur":
    st.header("📸 Twoje zdjęcie -> Szkic")
    f = st.file_uploader("Wgraj plik:", type=['png', 'jpg'])
    if f and st.button("Konwertuj"):
        img = Image.open(f).convert('L').filter(ImageFilter.CONTOUR)
        img = ImageOps.invert(img)
        st.image(img)
        buf = BytesIO(); img.save(buf, format="PNG")
        st.session_state['pdf_basket'].append(buf.getvalue())

elif tryb == "🖼️ Generator Okładek":
    st.header("🖼️ Okładka KDP")
    opis_o = st.text_input("Opis okładki:")
    if st.button("🎨 Stwórz Okładkę"):
        img = master_generate(translator.translate(opis_o), is_color=True, is_cover=True)
        if img:
            st.image(img)
            buf = BytesIO(); img.save(buf, format="PNG")
            st.session_state['pdf_basket'].insert(0, buf.getvalue())

elif tryb == "💬 Forum":
    st.header("💬 Forum Społeczności")
    wiad = st.text_input("Wiadomość:")
    if st.button("Wyślij"):
        st.session_state["posts"].insert(0, {"u": st.session_state["user_nick"], "m": wiad})
    for p in st.session_state["posts"]: st.info(f"**{p['u']}**: {p['m']}")

elif tryb == "⚖️ Regulamin i Pomoc":
    st.header("⚖️ Dokumenty Prawne")
    st.write("Tu wklej tekst dla Stripe i regulamin serwisu.")

# --- EKSPORT PDF ---
if st.session_state['pdf_basket']:
    st.divider()
    if st.button("📥 POBIERZ PDF DO AMAZON KDP"):
        out = BytesIO()
        pdf = canvas.Canvas(out, pagesize=(8.5*inch, 11*inch))
        for d in st.session_state['pdf_basket']:
            pdf.drawImage(BytesIO(d), 0.5*inch, 1*inch, width=7.5*inch, height=9*inch)
            pdf.showPage()
            pdf.showPage() # Pusta strona
        pdf.save()
        st.download_button("Zapisz plik PDF", out.getvalue(), "projekt_kdp_ultra.pdf")
