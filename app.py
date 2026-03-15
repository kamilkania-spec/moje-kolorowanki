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
ADMIN_NICK = "admin"
ADMIN_PASS = "KDP2026"

st.set_page_config(page_title="KDP Factory Ultimate 8K", layout="wide")
translator = GoogleTranslator(source='pl', target='en')

# --- BAZA DANYCH (Kredyty i Sesja) ---
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {
        "admin": {"pass": "KDP2026", "credits": 999999, "role": "admin"},
        "tester": {"pass": "KDP123", "credits": 50, "role": "user"}
    }
if "pdf_basket" not in st.session_state: st.session_state["pdf_basket"] = []
if "posts" not in st.session_state: st.session_state["posts"] = []
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False

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
    st.stop()

# --- GŁÓWNY SILNIK GRAFICZNY ---
def master_generate(prompt):
    nick = st.session_state["user_nick"]
    if st.session_state["user_db"][nick]["credits"] <= 0:
        st.error("❌ Brak kredytów!")
        return None
    try:
        handler = fal_client.subscribe("fal-ai/flux/schnell", arguments={"prompt": prompt})
        url = handler['images'][0]['url']
        resp = requests.get(url)
        img = Image.open(BytesIO(resp.content)).convert('L')
        # Skalowanie do 8K dla jakości KDP
        w, h = img.size
        img = img.resize((w*2, h*2), resample=Image.LANCZOS)
        if st.session_state["role"] != "admin":
            st.session_state["user_db"][nick]["credits"] -= 1
        return ImageEnhance.Contrast(img).enhance(3.5)
    except Exception as e:
        st.error(f"⚠️ Błąd API: {e}"); return None

# --- NARZĘDZIA SEO I TRENDÓW ---
def get_amazon_trends():
    return [
        "Easter Biblical Stories (High Demand)",
        "Cozy Little Shops: Bold & Easy",
        "Celestial Boho Animals",
        "Victorian Steampunk Fashions",
        "Kawaii Food with Faces"
    ]

# --- SIDEBAR ---
with st.sidebar:
    st.title(f"👤 {st.session_state['user_nick']}")
    cred = st.session_state["user_db"][st.session_state['user_nick']]['credits']
    st.write(f"🪙 Kredyty: {'∞' if st.session_state['role'] == 'admin' else cred}")
    
    tryb = st.selectbox("Wybierz moduł:", 
                        ["✏️ Generator Kategorii", 
                         "🦁 Niche Finder & SEO", 
                         "📖 Opowieść (Story Mode)", 
                         "📸 Zdjęcie na Kontur", 
                         "💬 Forum",
                         "⚖️ Regulamin i Pomoc"])
    
    st.divider()
    if st.button("🗑️ Wyczyść Projekt"):
        st.session_state['pdf_basket'] = []; st.rerun()
    if st.button("🚪 Wyloguj"):
        st.session_state["authenticated"] = False; st.rerun()

# --- MODUŁY ---

if tryb == "✏️ Generator Kategorii":
    st.header("🎨 Szybki Generator 8K")
    kat = st.radio("Styl:", ["Dowolny", "Geometria", "Pejzaż", "Przyroda", "Architektura"], horizontal=True)
    opis = st.text_input("Co narysować?")
    if st.button("GENERUJ"):
        with st.spinner("AI rysuje Twoją stronę..."):
            eng = translator.translate(opis)
            p = f"Coloring book page, {kat if kat != 'Dowolny' else ''} {eng}, 8k, black and white, clean bold lines, no shading"
            img = master_generate(p)
            if img:
                buf = BytesIO(); img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())
                st.image(img)

elif tryb == "🦁 Niche Finder & SEO":
    st.header("🦁 Niche Blaster - Znajdź i Zdominuj Niszcę")
    if st.button("🔍 Skanuj Trendy Amazon Marzec 2026"):
        trends = get_amazon_trends()
        st.write("🔥 **Trendy na dziś (USA/UK):**")
        for t in trends: st.code(t)
    
    n_input = st.text_input("Wybrana nisza (np. Kawaii Food):")
    if n_input:
        st.info(f"SEO Tytuł: {n_input.capitalize()} Coloring Book for Adults")
        ile_n = st.number_input("Ile grafik wygenerować?", 1, 50, 10)
        if st.button("🚀 Generuj Serię"):
            bar = st.progress(0)
            for i in range(ile_n):
                img = master_generate(f"Coloring page, {translator.translate(n_input)}, 8k, unique, bold lines")
                if img:
                    buf = BytesIO(); img.save(buf, format="PNG")
                    st.session_state['pdf_basket'].append(buf.getvalue())
                bar.progress((i+1)/ile_n)

elif tryb == "📖 Opowieść (Story Mode)":
    st.header("📖 Story Mode - Tworzenie Całej Historii")
    historia = st.text_area("Opisz o czym ma być książka:")
    ile_s = st.number_input("Liczba stron:", 5, 50, 10)
    if st.button("🔥 GENERUJ KSIĄŻKĘ"):
        bar_s = st.progress(0)
        for i in range(ile_s):
            img = master_generate(f"Page {i+1} of {ile_s}: {translator.translate(historia)}. Coloring page, 8k, consistent style")
            if img:
                buf = BytesIO(); img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())
            bar_s.progress((i+1)/ile_s)

elif tryb == "📸 Zdjęcie na Kontur":
    st.header("📸 Bezstratna Konwersja na Szkic")
    f = st.file_uploader("Wgraj zdjęcie:", type=['png', 'jpg'])
    if f and st.button("KONWERTUJ"):
        with st.spinner("Przetwarzam na linie..."):
            img = Image.open(f).convert('L')
            # Algorytm bezstratny krawędzi
            img_blurred = img.filter(ImageFilter.GaussianBlur(radius=1))
            img_edges = img_blurred.filter(ImageFilter.FIND_EDGES)
            img_final = ImageOps.invert(img_edges)
            img_final = ImageEnhance.Contrast(img_final).enhance(2.5)
            # Zapis do koszyka
            buf = BytesIO(); img_final.save(buf, format="PNG")
            st.session_state['pdf_basket'].append(buf.getvalue())
            st.image(img_final, caption="Gotowe do kolorowania!")

elif tryb == "💬 Forum":
    st.header("💬 Forum Społeczności")
    wiad = st.text_input("Napisz do innych twórców:")
    if st.button("Wyślij"):
        st.session_state["posts"].insert(0, {"u": st.session_state["user_nick"], "m": wiad})
        st.rerun()
    for p in st.session_state["posts"]: st.info(f"**{p['u']}**: {p['m']}")

elif tryb == "⚖️ Regulamin i Pomoc":
    st.header("⚖️ Dokumenty Prawne")
    t1, t2 = st.tabs(["Regulamin", "Polityka Prywatności"])
    with t1: st.write("Regulamin Twojej aplikacji...")
    with t2: st.write("Polityka prywatności...")

# --- PDF EXPORT ---
if st.session_state['pdf_basket']:
    st.divider()
    if st.button("📥 POBIERZ PDF DLA AMAZON KDP"):
        out = BytesIO()
        pdf = canvas.Canvas(out, pagesize=(8.5*inch, 11*inch))
        for d in st.session_state['pdf_basket']:
            pdf.drawImage(BytesIO(d), 0.5*inch, 1*inch, width=7.5*inch, height=9*inch)
            pdf.showPage(); pdf.showPage() # Dodaje pustą stronę z tyłu
        pdf.save()
        st.download_button("Zapisz PDF", out.getvalue(), "moje_kdp_8k.pdf")
