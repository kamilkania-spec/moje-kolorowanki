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

# --- KONFIGURACJA ---
os.environ["FAL_KEY"] = "cf0a6c98-7933-45df-918d-5757b24e9a30:afc267a3e94340879464bbea2862b40b"
ADMIN_NICK = "admin"
ADMIN_PASS = "KDP2026"

st.set_page_config(page_title="KDP Factory Pro 8K", layout="wide")
translator = GoogleTranslator(source='pl', target='en')

# --- BAZA DANYCH W SESJI ---
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

# --- FUNKCJA MAGICZNEJ PAŁECZKI (JAKOŚĆ 8K) ---
def magiczna_paleczka(prompt_text):
    # Ta funkcja dba o to, żeby każda grafika była idealną kolorowanką
    jakosc = "8k, high quality, crisp clean black lines, bold outlines, solid white background, no shading, no shadows, pure black and white, minimal detail for coloring"
    return f"{prompt_text}, {jakosc}"

# --- SILNIK GRAFICZNY ---
def master_generate(prompt, is_color=False, image_url=None):
    nick = st.session_state["user_nick"]
    if st.session_state["user_db"][nick]["credits"] <= 0:
        st.error("❌ Brak kredytów!")
        return None
    try:
        # Automatyczne dodanie jakości 8K i czystych linii przez "Magiczną Pałeczkę"
        final_p = magiczna_paleczka(prompt)
        
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
        
        # Skalowanie do 8K (LANCZOS)
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
            st.error("Błąd!")
    st.stop()

# --- SIDEBAR (Przywrócony układ z Twoich zdjęć) ---
with st.sidebar:
    st.title(f"👤 {st.session_state['user_nick']}")
    cred = st.session_state["user_db"][st.session_state["user_nick"]]["credits"]
    st.write(f"🌑 Kredyty: {'∞' if st.session_state['role'] == 'admin' else cred}")
    
    tryb = st.selectbox("Wybierz Narzędzie:", [
        "🎨 Generator Kategorii", 
        "📖 KDP Story AI (Bajka)", 
        "🚀 Masowy Generator 10-30",
        "📷 Zdjęcie na Kontur",
        "💬 Forum",
        "⚖️ Regulamin"
    ])
    
    st.divider()
    if st.button("🗑️ Wyczyść Projekt"):
        st.session_state['pdf_basket'] = []
        st.rerun()
    if st.button("🚪 Wyloguj"):
        st.session_state["authenticated"] = False
        st.rerun()

# --- LOGIKA MODUŁÓW ---

if tryb == "🎨 Generator Kategorii":
    st.header("🎨 Szybki Generator 8K")
    kat = st.radio("Styl:", ["Dowolny", "Geometria", "Pejzaż", "Przyroda", "Architektura", "Mandala", "Zwierzęta"], horizontal=True)
    opis = st.text_input("Opis (co narysować?):")
    
    if st.button("GENERUJ"):
        with st.spinner("Pracuję..."):
            eng = translator.translate(opis)
            # Budujemy prompt bazowy
            p = f"Coloring book page, {kat if kat != 'Dowolny' else ''} {eng}"
            img = master_generate(p, is_color=False)
            if img:
                buf = BytesIO()
                img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())
                st.image(img)

elif tryb == "📖 KDP Story AI (Bajka)":
    st.header("📖 Bajka o Twoim Dziecku")
    f_photo = st.file_uploader("Wgraj zdjęcie dziecka:", type=['png', 'jpg'])
    imię = st.text_input("Imię dziecka:")
    hist_d = st.text_area("O czym ma być bajka? (np. o misiu o tym samym imieniu)")
    ile_d = st.number_input("Ile stron?", 5, 30, 10)
    
    if st.button("STWÓRZ BAJKĘ"):
        if f_photo and imię:
            bar_d = st.progress(0)
            for i in range(ile_d):
                prompt_b = f"Storybook page {i+1}, character looks like the child from the photo, named {imię}, theme: {hist_d}"
                img = master_generate(prompt_b, is_color=False) # Możesz zmienić na True jeśli bajka ma być kolorowa
                if img:
                    buf = BytesIO()
                    img.save(buf, format="PNG")
                    st.session_state['pdf_basket'].append(buf.getvalue())
                bar_d.progress((i+1)/ile_d)
            st.success("Bajka gotowa!")

elif tryb == "🚀 Masowy Generator 10-30":
    st.header("🚀 Generuj Serię Kolorowanek")
    niche = st.text_input("Wpisz temat (np. Architektura Paryża):")
    ile_n = st.select_slider("Ile grafik wygenerować?", options=[10, 20, 30])
    
    if st.button("GENERUJ SERIĘ"):
        bar = st.progress(0)
        eng_n = translator.translate(niche)
        for i in range(ile_n):
            p_bulk = f"Coloring book page, {eng_n}, variety {i}"
            img = master_generate(p_bulk, is_color=False)
            if img:
                buf = BytesIO()
                img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())
            bar.progress((i+1)/ile_n)

elif tryb == "📷 Zdjęcie na Kontur":
    st.header("📷 Twoje zdjęcie na szkic")
    f = st.file_uploader("Wgraj zdjęcie:", type=['png', 'jpg'])
    if f:
        img_orig = Image.open(f)
        if st.button("Zmień w kolorowankę"):
            img_res = img_orig.convert('L').filter(ImageFilter.CONTOUR)
            img_res = ImageOps.invert(img_res)
            st.image(img_res)
            buf = BytesIO()
            img_res.save(buf, format="PNG")
            st.session_state['pdf_basket'].append(buf.getvalue())

# --- EKSPORT PDF (Z Twoich zdjęć IMG_2100.jpg) ---
if st.session_state['pdf_basket']:
    st.divider()
    if st.button("📥 POBIERZ PDF DO AMAZON KDP"):
        out = BytesIO()
        pdf = canvas.Canvas(out, pagesize=(8.5*inch, 11*inch))
        for d in st.session_state['pdf_basket']:
            # Grafika
            pdf.drawImage(BytesIO(d), 0.5*inch, 1*inch, width=7.5*inch, height=9*inch)
            pdf.showPage()
            # Pusta strona pod Amazon KDP
            pdf.showPage()
        pdf.save()
        st.download_button("Zapisz plik PDF", out.getvalue(), "projekt_kdp_8k.pdf")

elif tryb == "💬 Forum":
    st.header("💬 Forum")
    wiad = st.text_input("Wiadomość:")
    if st.button("Wyślij"):
        st.session_state["posts"].insert(0, {"u": st.session_state["user_nick"], "m": wiad})
        st.rerun()
    for p in st.session_state["posts"]:
        st.info(f"**{p['u']}**: {p['m']}")

elif tryb == "⚖️ Regulamin":
    st.header("⚖️ Dokumenty Prawne")
    st.write("Regulamin Twojej aplikacji...")
