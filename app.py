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
# To jest Twoje paliwo - upewnij się, że masz doładowane konto na fal.ai
os.environ["FAL_KEY"] = "cf0a6c98-7933-45df-918d-5757b24e9a30:afc267a3e94340879464bbea2862b40b"

# Twoje stałe dane admina
ADMIN_NICK = "admin"
ADMIN_PASS = "KDP2026"

st.set_page_config(page_title="KDP Factory - Admin Mode", layout="wide")
translator = GoogleTranslator(source='pl', target='en')

# --- INICJALIZACJA SYSTEMU ---
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
if "pdf_basket" not in st.session_state: st.session_state["pdf_basket"] = []
if "posts" not in st.session_state: st.session_state["posts"] = []
if "last_topic" not in st.session_state: st.session_state["last_topic"] = ""

# --- LOGOWANIE ---
if not st.session_state["authenticated"]:
    st.title("🔐 Panel Zarządzania Fabryką")
    col1, _ = st.columns([1, 2])
    with col1:
        u = st.text_input("Nick:")
        p = st.text_input("Hasło:", type="password")
        if st.button("Wejdź jako Szef"):
            if u == ADMIN_NICK and p == ADMIN_PASS:
                st.session_state["authenticated"] = True
                st.session_state["role"] = "admin"
                st.session_state["user_nick"] = u
                st.rerun()
            else:
                st.error("Błąd autoryzacji!")
    st.stop()

# --- SILNIK GENERUJĄCY 8K (BEZ LIMITÓW DLA ADMINA) ---
def master_generate(prompt):
    try:
        # Używamy subscribe dla stabilności połączenia
        handler = fal_client.subscribe("fal-ai/flux/schnell", arguments={"prompt": prompt})
        url = handler['images'][0]['url']
        resp = requests.get(url)
        img = Image.open(BytesIO(resp.content)).convert('L')
        # Upscaling 8K
        w, h = img.size
        img = img.resize((w*2, h*2), resample=Image.LANCZOS)
        return ImageEnhance.Contrast(img).enhance(3.5)
    except Exception as e:
        st.error(f"⚠️ Problem z API: {e}")
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.title(f"👑 ADMIN: {st.session_state['user_nick']}")
    st.success("Masz dostęp nielimitowany")
    tryb = st.selectbox("Wybierz narzędzie:", 
                        ["✏️ Generator Kategorii", "📖 Opowieść (Story Mode)", 
                         "🦁 Niche Blaster", "💬 Forum Społeczności", "📸 Zdjęcie na Kontur"])
    st.divider()
    st.write(f"Stron w sesji: {len(st.session_state['pdf_basket'])}")
    if st.button("🗑️ Wyczyść wszystko"):
        st.session_state['pdf_basket'] = []; st.rerun()

# --- MODUŁY ---

if tryb == "✏️ Generator Kategorii":
    st.header("🎨 Tworzenie Kolorowanek 8K")
    # TWOJE KATEGORIE
    kategoria = st.radio("Wybierz styl:", ["Przyroda", "Geometria", "Pejzaż", "Architektura", "Dowolny"], horizontal=True)
    opis = st.text_input("Co dokładnie narysować?")
    
    if st.button("🚀 GENERUJ TERAZ"):
        if opis:
            with st.spinner("Admin Mode: Generowanie bez limitów..."):
                eng = translator.translate(opis)
                final_prompt = f"Coloring book page, {kategoria if kategoria != 'Dowolny' else ''} {eng}, 8k, black and white, bold clean lines, white background, masterpiece"
                img = master_generate(final_prompt)
                if img:
                    buf = BytesIO(); img.save(buf, format="PNG")
                    st.session_state['pdf_basket'].append(buf.getvalue())
                    st.session_state['last_topic'] = opis
                    st.image(img, caption="Obraz gotowy i dodany do PDF")

elif tryb == "💬 Forum Społeczności":
    st.header("💬 Forum (Podgląd Admina)")
    msg = st.text_input("Napisz ogłoszenie dla użytkowników:")
    if st.button("Opublikuj"):
        if msg:
            st.session_state["posts"].insert(0, {"u": "ADMIN", "m": msg})
            st.rerun()
    for p in st.session_state["posts"]:
        st.info(f"**{p['u']}**: {p['m']}")

# --- RESZTA FUNKCJI (STORY MODE ITP.) ---
elif tryb == "📖 Opowieść (Story Mode)":
    st.header("📖 Generowanie całych książek")
    h = st.text_area("Zarys historii:")
    s = st.number_input("Ile stron wygenerować naraz?", 5, 50, 10)
    if st.button("URUCHOM PROCES"):
        bar = st.progress(0)
        eng_h = translator.translate(h)
        for i in range(s):
            img = master_generate(f"Step {i+1} of {s}: {eng_h}. Coloring page, 8k, bold lines")
            if img:
                buf = BytesIO(); img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())
            bar.progress((i+1)/s)

# --- EKSPORT PDF ---
if st.session_state['pdf_basket']:
    st.divider()
    if st.button("📥 POBIERZ PROJEKT (PDF)"):
        out = BytesIO()
        p = canvas.Canvas(out, pagesize=(8.5*inch, 11*inch))
        for d in st.session_state['pdf_basket']:
            p.drawImage(BytesIO(d), 0.5*inch, 1*inch, width=7.5*inch, height=9*inch)
            p.showPage(); p.showPage()
        p.save()
        st.download_button("Zapisz PDF", out.getvalue(), "kdp_final_project.pdf")
