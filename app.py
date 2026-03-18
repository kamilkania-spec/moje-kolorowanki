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

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="iColoring KDP Pro 8K", layout="wide", initial_sidebar_state="expanded")

# --- KLUCZ API I STAŁE ---
# Upewnij się, że ten klucz jest aktywny na fal.ai
os.environ["FAL_KEY"] = "cf0a6c98-7933-45df-918d-5757b24e9a30:afc267a3e94340879464bbea2862b40b"
ADMIN_NICK = "admin"
ADMIN_PASS = "KDP2026"

# --- STYLE CSS (Interfejs Premium) ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button {
        width: 100%;
        border-radius: 25px;
        background: linear-gradient(90deg, #e91e63, #ff4081);
        color: white;
        font-weight: bold;
        border: none;
        height: 3.5rem;
        transition: 0.3s;
    }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0 4px 15px rgba(233, 30, 99, 0.4); }
    div[data-testid="stExpander"] { border: none !important; box-shadow: none !important; }
    .stTextArea textarea { border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- INICJALIZACJA SESJI (BAZA DANYCH) ---
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {
        "admin": {"pass": "KDP2026", "credits": 999999, "role": "admin"},
        "tester": {"pass": "KDP123", "credits": 50, "role": "user"}
    }
if "pdf_basket" not in st.session_state:
    st.session_state["pdf_basket"] = []
if "posts" not in st.session_state:
    st.session_state["posts"] = []
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

translator = GoogleTranslator(source='pl', target='en')

# --- SILNIK GRAFICZNY (FLUX) ---
def master_generate(prompt, is_color=False, image_url=None):
    nick = st.session_state["user_nick"]
    if st.session_state["user_db"][nick]["credits"] <= 0:
        st.error("❌ Brak kredytów!")
        return None
    
    try:
        arguments = {"prompt": prompt}
        if image_url:
            arguments["image_url"] = image_url
            # Tutaj można dodać parametry dla ControlNet jeśli używasz konkretnego modelu
            
        handler = fal_client.subscribe("fal-ai/flux/schnell", arguments=arguments)
        url = handler['images'][0]['url']
        resp = requests.get(url)
        img = Image.open(BytesIO(resp.content))

        if not is_color:
            img = img.convert('L')
            img = ImageEnhance.Contrast(img).enhance(3.5)
        
        # Skalowanie do wysokiej jakości (8K-ish)
        w, h = img.size
        img = img.resize((w*2, h*2), resample=Image.LANCZOS)

        if st.session_state["role"] != "admin":
            st.session_state["user_db"][nick]["credits"] -= 1
        
        return img
    except Exception as e:
        st.error(f"⚠️ Błąd API: {e}")
        return None

# --- LOGOWANIE ---
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
        else:
            st.error("Błędne dane!")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.title(f"👤 {st.session_state['user_nick']}")
    cred = st.session_state["user_db"][st.session_state["user_nick"]]["credits"]
    st.write(f"🌑 Kredyty: {'∞' if st.session_state['role'] == 'admin' else cred}")
    
    st.divider()
    tryb = st.selectbox("Wybierz Mode:", [
        "🎨 Kreator Kolorowanek",
        "📖 Bajka AI (Twoje Dziecko)",
        "🚀 Masowy Generator (Bulk)",
        "📷 Zdjęcie na Kontur",
        "💬 Forum Społeczności",
        "⚖️ Regulamin"
    ])
    
    if st.button("🗑️ Wyczyść Projekt"):
        st.session_state['pdf_basket'] = []
        st.rerun()
    if st.button("🚪 Wyloguj"):
        st.session_state["authenticated"] = False
        st.rerun()

# --- LOGIKA MODUŁÓW ---

if tryb == "🎨 Kreator Kolorowanek":
    st.header("🎨 Kreator Kolorowanek Pro")
    
    opis = st.text_area("Opisz co mam narysować (po polsku):", placeholder="np. Słoń w garniturze pijący herbatę...")
    
    st.write("### Wybierz Styl")
    style_dict = {
        "Domyślny": "detailed coloring book page, clean black lines",
        "Dla Dzieci": "simple coloring book, thick outlines, big shapes",
        "Mandala": "mandala style, intricate symmetrical patterns",
        "Złożony": "extremely detailed, zentangle style, artistic",
        "Kawaii": "cute kawaii chibi style, simple lines"
    }
    wybrany_styl = st.radio("Styl:", list(style_dict.keys()), horizontal=True)
    
    col_size, col_num = st.columns(2)
    with col_size:
        rozmiar = st.selectbox("Format:", ["8.5x11 (KDP)", "1:1 Square"])
    with col_num:
        ilosc_gen = st.number_input("Ilość grafik:", 1, 10, 1)

    if st.button("🚀 SPOWODOWAĆ (Generuj)"):
        with st.spinner("Tłumaczenie i rysowanie..."):
            eng_p = translator.translate(opis)
            for _ in range(ilosc_gen):
                full_p = f"{style_dict[wybrany_styl]}, {eng_p}, white background, no shading, clean lines"
                img = master_generate(full_p)
                if img:
                    st.image(img)
                    buf = BytesIO()
                    img.save(buf, format="PNG")
                    st.session_state['pdf_basket'].append(buf.getvalue())
            st.success("Dodano do koszyka PDF!")

elif tryb == "📖 Bajka AI (Twoje Dziecko)":
    st.header("📖 Personalizowana Bajka KDP")
    st.info("Wgraj zdjęcie dziecka - AI stworzy spójną bajkę z jego twarzą!")
    
    f_photo = st.file_uploader("Zdjęcie dziecka:", type=['jpg', 'png'])
    imię = st.text_input("Imię dziecka:")
    postać = st.selectbox("W kogo zamienić dziecko?", ["Misia", "Astronauty", "Królika", "Rycerza"])
    ile_stron = st.slider("Liczba stron:", 5, 30, 10)
    
    if st.button("✨ GENERUJ CAŁĄ BAJKĘ"):
        if f_photo and imię:
            bar = st.progress(0)
            # Uwaga: W prawdziwym wdrożeniu zdjęcie musiałoby być wgrane na serwer, aby przekazać URL do fal.ai
            # Tu symulujemy proces na bazie Twojego kodu:
            for i in range(ile_stron):
                p_bajka = f"Step {i+1} of story: Child named {imię} as a {postać} having adventures. Coloring page style, thick lines, consistent face."
                img = master_generate(p_bajka)
                if img:
                    buf = BytesIO()
                    img.save(buf, format="PNG")
                    st.session_state['pdf_basket'].append(buf.getvalue())
                bar.progress((i+1)/ile_stron)
            st.success("Bajka gotowa w koszyku PDF!")

elif tryb == "🚀 Masowy Generator (Bulk)":
    st.header("🚀 Generator Całych Albumów")
    niche = st.text_input("Temat albumu (np. 'Koty', 'Kosmos'):")
    ile_bulk = st.select_slider("Ile stron wygenerować?", options=[10, 20, 30, 40, 50])
    
    if st.button("🔥 GENERUJ CAŁĄ SERIĘ"):
        bar_m = st.progress(0)
        eng_n = translator.translate(niche)
        for i in range(ile_bulk):
            p_bulk = f"Coloring book page, {eng_n}, different composition {i}, bold lines, white background"
            img = master_generate(p_bulk)
            if img:
                buf = BytesIO()
                img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())
            bar_m.progress((i+1)/ile_bulk)
        st.success(f"Dodano {ile_bulk} stron do projektu!")

elif tryb == "📷 Zdjęcie na Kontur":
    st.header("📷 Twoje Zdjęcie -> Szkic")
    f = st.file_uploader("Wgraj plik:", type=['png', 'jpg'])
    if f:
        img_orig = Image.open(f)
        st.image(img_orig, caption="Oryginał", width=300)
        if st.button("Konwertuj na kolorowankę"):
            # Proste przetwarzanie PIL dla efektu szkicu
            img_res = img_orig.convert('L').filter(ImageFilter.CONTOUR)
            img_res = ImageOps.invert(img_res) # Odwrócenie, by linie były czarne
            st.image(img_res, caption="Gotowy szkic")
            buf = BytesIO()
            img_res.save(buf, format="PNG")
            st.session_state['pdf_basket'].append(buf.getvalue())

# --- EXPORT PDF (Zawsze widoczny na dole, jeśli są grafiki) ---
if st.session_state['pdf_basket']:
    st.divider()
    st.subheader(f"📦 Twój Projekt KDP ({len(st.session_state['pdf_basket'])} stron)")
    
    if st.button("📥 GENERUJ I POBIERZ PDF (Standard Amazon)"):
        out = BytesIO()
        pdf = canvas.Canvas(out, pagesize=(8.5*inch, 11*inch))
        
        for d in st.session_state['pdf_basket']:
            # Strona z grafiką (z marginesami pod KDP)
            pdf.drawImage(BytesIO(d), 0.75*inch, 1*inch, width=7*inch, height=9*inch)
            pdf.showPage()
            # Pusta strona na odwrocie (standard w kolorowankach premium)
            pdf.showPage()
            
        pdf.save()
        st.download_button("💾 Zapisz plik PDF", out.getvalue(), "projekt_kdp_gotowy.pdf", "application/pdf")

elif tryb == "💬 Forum Społeczności":
    st.header("💬 Forum i Inspiracje")
    wiad = st.text_input("Podziel się pomysłem:")
    if st.button("Wyślij"):
        st.session_state["posts"].insert(0, {"u": st.session_state["user_nick"], "m": wiad})
        st.rerun()
    for p in st.session_state["posts"]:
        st.info(f"**{p['u']}**: {p['m']}")

elif tryb == "⚖️ Regulamin":
    st.header("⚖️ Zasady i Pomoc")
    t1, t2 = st.tabs(["Zasady", "KDP Tips"])
    with t1: st.write("Aplikacja do użytku komercyjnego. Grafiki można sprzedawać na Amazon.")
    with t2: st.write("Pamiętaj o marginesach (Bleed). Każda strona w PDF ma pusty tył.")
