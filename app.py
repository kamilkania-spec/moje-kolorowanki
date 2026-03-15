import streamlit as st
import os
import fal_client
from deep_translator import GoogleTranslator
from PIL import Image, ImageEnhance, ImageOps
import requests
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# --- KONFIGURACJA ---
os.environ["FAL_KEY"] = "cf0a6c98-7933-45df-918d-5757b24e9a30:afc267a3e94340879464bbea2862b40b"
ADMIN_USER = "admin"
ADMIN_PASS = "KDP2026"

st.set_page_config(page_title="KDP Factory Pro 8K", layout="wide")
translator = GoogleTranslator(source='pl', target='en')

# --- INICJALIZACJA SESJI ---
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
if "pdf_basket" not in st.session_state: st.session_state["pdf_basket"] = []
if "posts" not in st.session_state: st.session_state["posts"] = []
if "last_topic" not in st.session_state: st.session_state["last_topic"] = ""

# --- LOGOWANIE ---
if not st.session_state["authenticated"]:
    st.title("🔐 Logowanie do Fabryki")
    u = st.text_input("Nick:")
    p = st.text_input("Hasło:", type="password")
    if st.button("Zaloguj się"):
        if u == ADMIN_USER and p == ADMIN_PASS:
            st.session_state["authenticated"] = True
            st.session_state["user_nick"] = u
            st.rerun()
        else: st.error("Błąd!")
    st.stop()

# --- SILNIK GRAFICZNY ---
def get_final_image(prompt):
    """Prawdziwe generowanie obrazu przez API"""
    handler = fal_client.submit("fal-ai/flux/schnell", arguments={"prompt": prompt})
    result = handler.get()
    url = result['images'][0]['url']
    resp = requests.get(url)
    img = Image.open(BytesIO(resp.content)).convert('L')
    # Upscaling do 8K (cyfrowy)
    w, h = img.size
    img = img.resize((w*2, h*2), resample=Image.LANCZOS)
    return ImageEnhance.Contrast(img).enhance(3.5)

# --- SIDEBAR ---
with st.sidebar:
    st.title(f"👤 {st.session_state['user_nick']}")
    tryb = st.selectbox("Wybierz moduł:", 
                        ["✏️ Tekst na Kolorowankę", "📸 Zdjęcie na Kolorowankę", 
                         "📖 Opowieść (Story Mode)", "🦁 Generuj Serię Niszy", 
                         "💬 Forum Społeczności"])
    st.divider()
    st.write(f"Stron w projekcie: {len(st.session_state['pdf_basket'])}")
    if st.button("🗑️ Wyczyść projekt"):
        st.session_state['pdf_basket'] = []; st.rerun()

# --- LOGIKA MODUŁÓW ---

if tryb == "✏️ Tekst na Kolorowankę":
    st.header("🎨 Generator z Kategoriami")
    kat = st.radio("Wybierz styl domyślny:", ["Dowolny", "Geometria", "Pejzaż", "Przyroda", "Architektura"])
    opis = st.text_input("Co narysować?")
    
    if st.button("GENERUJ 8K"):
        if opis:
            with st.spinner("AI pracuje nad Twoim obrazem..."):
                eng_opis = translator.translate(opis)
                full_prompt = f"Coloring book page, {kat if kat != 'Dowolny' else ''} {eng_opis}, 8k, black and white, clean bold lines, no shading"
                
                final_img = get_final_image(full_prompt)
                
                buf = BytesIO()
                final_img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())
                st.session_state['last_topic'] = opis
                st.image(final_img, caption="Obraz wygenerowany i dodany do PDF!")

elif tryb == "💬 Forum Społeczności":
    st.header("💬 Forum")
    msg = st.text_input("Twoja wiadomość:")
    if st.button("Wyślij"):
        if msg:
            st.session_state["posts"].insert(0, {"u": st.session_state["user_nick"], "m": msg})
            st.rerun()
    for p in st.session_state["posts"]:
        st.write(f"**{p['u']}**: {p['m']}")

elif tryb == "📖 Opowieść (Story Mode)":
    st.header("📖 Buduj książkę")
    hist = st.text_area("O czym historia?")
    ile = st.number_input("Ile stron?", 5, 50, 10)
    if st.button("GENERUJ CAŁOŚĆ"):
        st.session_state['last_topic'] = hist
        bar = st.progress(0)
        eng_hist = translator.translate(hist)
        for i in range(ile):
            p = f"Step {i+1} of {ile}: {eng_hist}. Coloring page, 8k, bold outlines"
            img = get_final_image(p)
            buf = BytesIO(); img.save(buf, format="PNG")
            st.session_state['pdf_basket'].append(buf.getvalue())
            bar.progress((i+1)/ile)

elif tryb == "🦁 Generuj Serię Niszy":
    st.header("🦁 Niche Blaster")
    nisza = st.text_input("Nisza (np. Dinozaury):")
    ile_n = st.number_input("Ile grafik?", 5, 50, 10)
    if st.button("GENERUJ SERIĘ"):
        st.session_state['last_topic'] = nisza
        eng_n = translator.translate(nisza)
        bar_n = st.progress(0)
        for i in range(ile_n):
            p = f"Coloring page, {eng_n}, 8k, unique composition, bold outlines"
            img = get_final_image(p)
            buf = BytesIO(); img.save(buf, format="PNG")
            st.session_state['pdf_basket'].append(buf.getvalue())
            bar_n.progress((i+1)/ile_n)

elif tryb == "📸 Zdjęcie na Kolorowankę":
    st.header("📸 Zdjęcie -> Kontur")
    foto = st.file_uploader("Wgraj plik", type=['png', 'jpg'])
    if foto and st.button("Konwertuj"):
        img = Image.open(foto).convert('L')
        img = ImageEnhance.Contrast(img).enhance(2.5).point(lambda p: 0 if p < 140 else 255)
        buf = BytesIO(); img.save(buf, format="PNG")
        st.session_state['pdf_basket'].append(buf.getvalue())
        st.image(img)

# --- PDF I SEO ---
if st.session_state['pdf_basket']:
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📥 POBIERZ PDF"):
            out = BytesIO()
            p = canvas.Canvas(out, pagesize=(8.5*inch, 11*inch))
            for d in st.session_state['pdf_basket']:
                p.drawImage(BytesIO(d), 0.5*inch, 1*inch, width=7.5*inch, height=9*inch)
                p.showPage(); p.showPage()
            p.save()
            st.download_button("Zapisz plik PDF", out.getvalue(), "kdp_final.pdf")
    with c2:
        if st.session_state['last_topic']:
            st.write("**Sugestia SEO:**")
            st.write(f"Tytuł: {st.session_state['last_topic'].capitalize()} Coloring Book for Adults")
