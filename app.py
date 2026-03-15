import streamlit as st
import os
import fal_client
from deep_translator import GoogleTranslator
from PIL import Image, ImageEnhance
import requests
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# --- KONFIGURACJA ---
os.environ["FAL_KEY"] = "cf0a6c98-7933-45df-918d-5757b24e9a30:afc267a3e94340879464bbea2862b40b"
ADMIN_NICK = "admin"
ADMIN_PASS = "KDP2026"

st.set_page_config(page_title="KDP Factory - Credit System", layout="wide")
translator = GoogleTranslator(source='pl', target='en')

# --- BAZA UŻYTKOWNIKÓW I KREDYTÓW (Symulacja bazy danych) ---
# Docelowo te dane będą w zewnętrznej bazie danych
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {
        "admin": {"pass": "KDP2026", "credits": 999999, "role": "admin"},
        "tester": {"pass": "KDP123", "credits": 50, "role": "user"}
    }

if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
if "pdf_basket" not in st.session_state: st.session_state["pdf_basket"] = []
if "posts" not in st.session_state: st.session_state["posts"] = []
if "last_topic" not in st.session_state: st.session_state["last_topic"] = ""

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
        else: st.error("Błędny nick lub hasło!")
    st.stop()

# --- FUNKCJA SPRAWDZAJĄCA KREDYTY ---
def can_generate():
    nick = st.session_state["user_nick"]
    if st.session_state["user_db"][nick]["credits"] > 0:
        return True
    return False

def use_credit(amount=1):
    nick = st.session_state["user_nick"]
    if st.session_state["role"] != "admin": # Admin nie traci kredytów
        st.session_state["user_db"][nick]["credits"] -= amount

# --- SILNIK GRAFICZNY ---
def master_generate(prompt):
    if not can_generate():
        st.error("❌ Brak kredytów! Doładuj konto, aby generować dalej.")
        return None
    try:
        handler = fal_client.subscribe("fal-ai/flux/schnell", arguments={"prompt": prompt})
        url = handler['images'][0]['url']
        resp = requests.get(url)
        img = Image.open(BytesIO(resp.content)).convert('L')
        w, h = img.size
        img = img.resize((w*2, h*2), resample=Image.LANCZOS)
        use_credit(1) # Zabierz 1 kredyt po udanym generowaniu
        return ImageEnhance.Contrast(img).enhance(3.5)
    except Exception as e:
        st.error(f"⚠️ Błąd API: {e}")
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.title(f"👤 {st.session_state['user_nick']}")
    curr_credits = st.session_state["user_db"][st.session_state["user_nick"]]["credits"]
    
    if st.session_state["role"] == "admin":
        st.success("💎 Status: ADMIN (Unlimited)")
    else:
        st.warning(f"🪙 Pozostałe kredyty: {curr_credits}")
    
    tryb = st.selectbox("Menu:", ["✏️ Generator 8K", "📖 Opowieść", "💬 Forum", "📸 Zdjęcie"])
    st.divider()
    if st.button("🚪 Wyloguj"):
        st.session_state["authenticated"] = False; st.rerun()

# --- LOGIKA MODUŁÓW ---

if tryb == "✏️ Generator 8K":
    st.header("🎨 Twórz Kolorowanki")
    kat = st.radio("Styl:", ["Przyroda", "Geometria", "Pejzaż", "Dowolny"], horizontal=True)
    opis = st.text_input("Twój opis pomysłu:")
    
    if st.button("GENERUJ (-1 Kredyt)"):
        if can_generate():
            with st.spinner("AI pracuje..."):
                eng = translator.translate(opis)
                p = f"Coloring book page, {kat if kat != 'Dowolny' else ''} {eng}, 8k, bold lines"
                img = master_generate(p)
                if img:
                    buf = BytesIO(); img.save(buf, format="PNG")
                    st.session_state['pdf_basket'].append(buf.getvalue())
                    st.image(img)
        else:
            st.error("Nie masz już kredytów!")

elif tryb == "💬 Forum":
    st.header("💬 Forum Społeczności")
    m = st.text_input("Twoja wiadomość:")
    if st.button("Wyślij"):
        st.session_state["posts"].insert(0, {"u": st.session_state["user_nick"], "m": m})
        st.rerun()
    for p in st.session_state["posts"]:
        st.info(f"**{p['u']}**: {p['m']}")

# --- EKSPORT PDF ---
if st.session_state['pdf_basket']:
    st.divider()
    if st.button("📥 POBIERZ PDF"):
        out = BytesIO()
        pdf = canvas.Canvas(out, pagesize=(8.5*inch, 11*inch))
        for d in st.session_state['pdf_basket']:
            pdf.drawImage(BytesIO(d), 0.5*inch, 1*inch, width=7.5*inch, height=9*inch)
            pdf.showPage(); pdf.showPage()
        pdf.save()
        st.download_button("Zapisz PDF", out.getvalue(), "kdp_final.pdf")
