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
import base64
import json

# --- KONFIGURACJA ---
os.environ["FAL_KEY"] = "cf0a6c98-7933-45df-918d-5757b24e9a30:afc267a3e94340879464bbea2862b40b"
ADMIN_NICK = "admin"
ADMIN_PASS = "KDP2026"

st.set_page_config(page_title="KDP Factory Pro 8K - FULL SUITE", layout="wide")
translator = GoogleTranslator(source='pl', target='en')

# --- BAZA DANYCH (ZACHOWANA) ---
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {
        "admin": {"pass": "KDP2026", "credits": 999999, "role": "admin"},
        "tester": {"pass": "KDP123", "credits": 50, "role": "user"}
    }
if "pdf_basket" not in st.session_state: st.session_state["pdf_basket"] = []
if "posts" not in st.session_state: st.session_state["posts"] = []

# --- POPRAWIONY SILNIK GRAFICZNY ---
def master_generate(prompt, is_color=False, image_url=None, is_cover=False):
    nick = st.session_state.get("user_nick", "admin")
    if st.session_state["user_db"][nick]["credits"] <= 0:
        st.error("❌ Brak kredytów!")
        return None
    try:
        # Tuta była przyczyna błędu - poprawiłem rozmiary na akceptowane przez API
        if is_cover:
            size_val = "square_hd"
        else:
            size_val = "portrait_4_3" # Zmienione z portrait_4_5 na akceptowalne portrait_4_3
            
        arguments = {
            "prompt": prompt,
            "image_size": size_val, # POPRAWKA BŁĘDU Z FOTO
            "seed": random.randint(1, 999999)
        }
        
        if image_url:
            arguments["image_url"] = image_url
            
        handler = fal_client.subscribe("fal-ai/flux/schnell", arguments=arguments)
        url = handler['images'][0]['url']
        resp = requests.get(url)
        img = Image.open(BytesIO(resp.content))

        if not is_color:
            img = img.convert('L')
            img = ImageEnhance.Contrast(img).enhance(3.5)
            # Skalowanie do wysokiej rozdzielczości
            w, h = img.size
            img = img.resize((w*2, h*2), resample=Image.LANCZOS)
        
        # Odjęcie kredytu
        if st.session_state.get("role") != "admin":
            st.session_state["user_db"][nick]["credits"] -= 1
            
        return img
    except Exception as e:
        st.error(f"⚠️ Błąd silnika AI: {e}")
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
        "🦊 Niche Finder & SEO",
        "📖 KDP Story AI (Beta)",
        "📸 Zdjęcie na Kontur",
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

# --- LOGIKA MODUŁÓW (WSZYSTKIE TWOJE OPCJE ZACHOWANE) ---

if tryb == "🎨 Generator Kategorii":
    st.header("🎨 Szybki Generator 8K")
    kat = st.radio("Styl:", ["Dowolny", "Geometria", "Pejzaż", "Przyroda", "Architektura"], horizontal=True)
    opis = st.text_input("Opis (co narysować?):")
    if st.button("GENERUJ"):
        with st.spinner("Pracuję..."):
            eng = translator.translate(opis)
            p = f"Coloring book page, {kat if kat != 'Dowolny' else ''} {eng}, 8k, black and white, clean bold lines, no shading"
            img = master_generate(p, is_color=False)
            if img:
                buf = BytesIO()
                img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())
                st.image(img)

elif tryb == "🦊 Niche Finder & SEO":
    st.header("🦊 Trendy USA/UK")
    trends = ["Little Shops", "Celestial Boho Animals", "Victorian Steampunk Fashions", "Kawaii Food"]
    for t in trends: st.code(t)
    n_input = st.text_input("Wpisz wybraną niszcze:")
    if n_input:
        st.success(f"Tytuł: {n_input.capitalize()} Coloring Book for Adults")
        st.write(f"Słowa kluczowe: {n_input}, coloring book, kdp, amazon, 2026 trends")
        ile_n = st.number_input("Ile grafik?", 1, 50, 5)
        if st.button("🚀 Generuj Serię"):
            bar = st.progress(0)
            for i in range(ile_n):
                p_n = f"Coloring page, {translator.translate(n_input)}, 8k, unique, bold lines"
                img = master_generate(p_n, is_color=False)
                if img:
                    buf = BytesIO()
                    img.save(buf, format="PNG")
                    st.session_state['pdf_basket'].append(buf.getvalue())
                bar.progress((i+1)/ile_n)

elif tryb == "📖 KDP Story AI (Beta)":
    st.header("📖 Personalizowane Bajki z Twojego Zdjęcia")
    f_photo = st.file_uploader("Wgraj zdjęcie dziecka:", type=['png', 'jpg'])
    imię = st.text_input("Imię dziecka:")
    postać = st.selectbox("W kogo zamienić dziecko?", ["Misia", "Superbohatera", "Królewnę/Księcia"])
    hist_d = st.text_area("Opisz fabułę:")
    ile_d = st.number_input("Ile stron?", 5, 30, 10)
    if imię and f_photo and st.button("✨ Generuj Bajkę"):
        photo_url = fal_client.upload_image(f_photo.getvalue())
        bar_d = st.progress(0)
        for i in range(ile_d):
            p_d = f"Step {i+1} of {ile_d} in the story of {imię}. {postać} based on photo, whimsical illustration, soft lighting, {hist_d}"
            img = master_generate(p_d, is_color=True, image_url=photo_url)
            if img:
                buf = BytesIO()
                img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())
            bar_d.progress((i+1)/ile_d)

elif tryb == "📸 Zdjęcie na Kontur":
    st.header("📸 Twoje zdjęcie -> Szkic")
    f = st.file_uploader("Wgraj plik:", type=['png', 'jpg'])
    if f and st.button("Konwertuj"):
        img = Image.open(f).convert('L')
        img = img.filter(ImageFilter.CONTOUR)
        img = ImageOps.invert(img)
        st.image(img, caption="Kontur gotowy!")
        buf = BytesIO()
        img.save(buf, format="PNG")
        st.session_state['pdf_basket'].append(buf.getvalue())

elif tryb == "💬 Forum":
    st.header("💬 Forum Społeczności")
    wiad = st.text_input("Wiadomość:")
    if st.button("Wyślij"):
        st.session_state["posts"].insert(0, {"u": st.session_state["user_nick"], "m": wiad})
    for p in st.session_state["posts"]:
        st.info(f"**{p['u']}**: {p['m']}")

elif tryb == "⚖️ Regulamin i Pomoc":
    st.header("⚖️ Dokumenty Prawne")
    t1, t2 = st.tabs(["Regulamin", "Polityka Prywatności"])
    with t1: st.write("Regulamin Twojej aplikacji... (Tu wklej tekst)")
    with t2: st.write("Polityka prywatności...")

# --- EKSPORT PDF (Z TWOICH ZDJĘĆ) ---
if st.session_state['pdf_basket']:
    st.divider()
    if st.button("📥 POBIERZ PDF DO AMAZON KDP"):
        out = BytesIO()
        pdf = canvas.Canvas(out, pagesize=(8.5*inch, 11*inch))
        for d in st.session_state['pdf_basket']:
            pdf.drawImage(BytesIO(d), 0.5*inch, 1*inch, width=7.5*inch, height=9*inch)
            pdf.showPage()
            pdf.showPage() # Jedna pusta strona (standard KDP)
        pdf.save()
        st.download_button("Zapisz plik PDF", out.getvalue(), "projekt_kdp_8k.pdf")
