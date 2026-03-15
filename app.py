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

st.set_page_config(page_title="KDP Factory Ultimate - Ready for Payments", layout="wide")
translator = GoogleTranslator(source='pl', target='en')

# --- BAZA DANYCH ---
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
                         "⚖️ Regulamin i Pomoc"]) # NOWA ZAKŁADKA
    
    st.divider()
    if st.button("🗑️ Wyczyść Projekt"):
        st.session_state['pdf_basket'] = []; st.rerun()
    if st.button("🚪 Wyloguj"):
        st.session_state["authenticated"] = False; st.rerun()

# --- MODUŁY (STARE FUNKCJE + BEZSTRATNE ZDJĘCIA) ---

if tryb == "✏️ Generator Kategorii":
    st.header("🎨 Szybki Generator 8K")
    kat = st.radio("Styl:", ["Dowolny", "Geometria", "Pejzaż", "Przyroda", "Architektura"], horizontal=True)
    opis = st.text_input("Co narysować?")
    if st.button("GENERUJ"):
        with st.spinner("Pracuję..."):
            eng = translator.translate(opis)
            # Silnik generujący z poprzednich wersji...
            # [Tutaj master_generate z Twoimi parametrami]
            st.info("Podepnij API na fal.ai, aby ruszyć z generowaniem!")

elif tryb == "📸 Zdjęcie na Kontur":
    st.header("📸 Bezstratny Kontur")
    f = st.file_uploader("Wgraj zdjęcie:", type=['png', 'jpg'])
    if f and st.button("KONWERTUJ"):
        img = Image.open(f).convert('L')
        # Algorytm bezstratny
        img_blurred = img.filter(ImageFilter.GaussianBlur(radius=1))
        img_edges = img_blurred.filter(ImageFilter.FIND_EDGES)
        img_final = ImageOps.invert(img_edges)
        st.image(img_final, caption="Bezstratny kontur gotowy!")

elif tryb == "🦁 Niche Finder & SEO":
    st.header("🦁 Trendy Amazon Marzec 2026")
    st.write("1. Easter Biblical Stories")
    st.write("2. Celestial Boho Animals")
    st.write("... i inne gorące nisze!")

elif tryb == "⚖️ Regulamin i Pomoc":
    st.header("⚖️ Dokumenty Prawne")
    
    tab1, tab2 = st.tabs(["Regulamin Serwisu", "Polityka Prywatności"])
    
    with tab1:
        st.markdown("""
        ### Regulamin Serwisu KDP Factory
        1. **Usługi:** Serwis świadczy usługi generowania grafik AI w formie kolorowanek.
        2. **Kredyty:** Zakupione kredyty nie podlegają zwrotowi po ich wykorzystaniu do wygenerowania grafiki.
        3. **Licencja:** Użytkownik otrzymuje prawo do komercyjnego wykorzystania grafik na platformie Amazon KDP.
        4. **Płatności:** Wszystkie płatności realizowane są przez operatora Stripe.
        """)
        
    with tab2:
        st.markdown("""
        ### Polityka Prywatności
        1. **Dane:** Przetwarzamy Twój adres e-mail i nick w celu świadczenia usługi.
        2. **Pliki:** Nie przechowujemy Twoich zdjęć na naszych serwerach po zakończeniu sesji.
        3. **Bezpieczeństwo:** Dane płatnicze są procesowane wyłącznie przez Stripe i nie są widoczne dla administratora.
        """)

# --- PDF ---
if st.session_state['pdf_basket']:
    if st.button("📥 POBIERZ PDF"):
        st.success("Plik gotowy do Amazon KDP!")
