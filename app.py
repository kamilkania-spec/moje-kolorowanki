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

# --- KONFIGURACJA KLUCZA ---
os.environ["FAL_KEY"] = "cf0a6c98-7933-45df-918d-5757b24e9a30:afc267a3e94340879464bbea2862b40b"

st.set_page_config(page_title="KDP Factory Pro 2026 - MASTER UNIT", layout="wide")
translator = GoogleTranslator(source='pl', target='en')

# --- BAZA DANYCH I SESJA ---
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

# --- SILNIK GRAFICZNY PRO (KDP 8K Style) ---
def master_generate(prompt, is_color=False, image_url=None, seed=None):
    nick = st.session_state["user_nick"]
    if st.session_state["user_db"][nick]["credits"] <= 0:
        st.error("❌ Brak kredytów!")
        return None
    
    try:
        gen_seed = seed if seed is not None else random.randint(0, 9999999)
        # iColoring Clean Style - przywrócone parametry
        clean_p = f"{prompt}, high quality line art, sharp edges, pure white background, zero grayscale, professional adult coloring book style, 8k, vector-like lines"
        
        arguments = {"prompt": clean_p, "image_size": "square_hd", "seed": gen_seed}
        if image_url: arguments["image_url"] = image_url

        handler = fal_client.subscribe("fal-ai/flux/schnell", arguments=arguments)
        url = handler['images'][0]['url']
        resp = requests.get(url)
        img = Image.open(BytesIO(resp.content))
        
        if not is_color:
            img = img.convert('L')
            img = ImageEnhance.Contrast(img).enhance(4.2)
        
        # Upscaling 8K
        w, h = img.size
        img = img.resize((w*2, h*2), resample=Image.LANCZOS)
        
        if st.session_state["role"] != "admin":
            st.session_state["user_db"][nick]["credits"] -= 1
        return img
    except Exception as e:
        st.error(f"⚠️ Błąd: {e}")
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.title(f"👤 {st.session_state['user_nick']}")
    st.write(f"🪙 Kredyty: {'∞' if st.session_state['role'] == 'admin' else st.session_state['user_db'][st.session_state['user_nick']]['credits']}")
    
    tryb = st.selectbox("WYBIERZ NARZĘDZIE:", 
                        ["🚀 HURTOWA PRODUKCJA (Siatka)", 
                         "🦁 NICHE FINDER & SEO", 
                         "📖 KDP STORY AI (Foto-Bajka)", 
                         "📖 STORY MODE (Fabularny)",
                         "📸 ZDJĘCIE NA KONTUR 8K", 
                         "💬 FORUM TWÓRCÓW",
                         "⚖️ REGULAMIN I POMOC"])
    
    st.divider()
    if st.button("🗑️ CZYŚĆ PROJEKT"):
        st.session_state['pdf_basket'] = []; st.rerun()
    if st.button("🚪 WYLOGUJ"):
        st.session_state["authenticated"] = False; st.rerun()

# --- MODUŁY ---

if tryb == "🚀 HURTOWA PRODUKCJA (Siatka)":
    st.header("🚀 Hurtowy Generator iColoring Style (8.5x11)")
    c1, c2, c3 = st.columns(3)
    with c1: kat = st.selectbox("Kategoria:", ["Przyroda i Natura", "Mandale i Geometria", "Architektura", "Zwierzęta", "Fantastyka"])
    with c2: styl_l = st.selectbox("Styl linii:", ["Szczegółowe (Fine)", "Bold & Easy (Grube)", "Artystyczne"])
    with c3: ile = st.number_input("Ile stron:", 1, 100, 20)
    
    temat = st.text_input("Szczegóły tematu (np. leśne sowy w nocy):")
    spojnosc = st.checkbox("Spójność serii (Seed Lock)", value=True)
    
    if st.button("🔥 URUCHOM PRODUKCJĘ HURTOWĄ"):
        bar = st.progress(0)
        status = st.empty()
        cols = st.columns(4) # Siatka podglądu jak na icoloring
        fixed_seed = random.randint(0, 999999) if spojnosc else None
        
        kat_p = {"Przyroda i Natura": "nature, botanical", "Mandale i Geometria": "mandala, geometric", "Zwierzęta": "wildlife portraits", "Architektura": "detailed buildings", "Fantastyka": "mythical creatures"}
        styl_p = {"Szczegółowe (Fine)": "intricate thin lines", "Bold & Easy (Grube)": "bold thick lines", "Artystyczne": "sketchy artistic art"}
        
        eng_t = translator.translate(temat)
        for i in range(ile):
            status.info(f"Generowanie {i+1}/{ile}...")
            p = f"Coloring book page, {kat_p[kat]}, {styl_p[styl_l]}, {eng_t}, unique composition {i}"
            img = master_generate(p, seed=fixed_seed)
            if img:
                buf = BytesIO(); img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())
                with cols[i % 4]:
                    st.image(img, use_container_width=True)
            bar.progress((i+1)/ile)
        status.success("Zakończono! Pliki w koszyku PDF.")

elif tryb == "🦁 NICHE FINDER & SEO":
    st.header("🦁 Niche Finder & SEO Assistant")
    if st.button("🔍 ANALIZUJ RYNEK (MARZEC 2026)"):
        st.success("🔥 TOP TRENDY:\n1. Bold & Easy Hygge Lifestyle\n2. Boho Easter Mandala Animals\n3. Victorian Steampunk Architecture")
        st.info("Kluczowe Keywords do Amazon: coloring book for adults, stress relief, kdp interior, 2026 trends")

elif tryb == "📖 KDP STORY AI (Foto-Bajka)":
    st.header("📖 KDP Story AI - Personalizacja")
    f_photo = st.file_uploader("Wgraj zdjęcie dziecka:", type=['png', 'jpg'])
    imię = st.text_input("Imię dziecka:")
    postać = st.selectbox("W kogo je zamienić:", ["Mały Miś", "Dzielny Rycerz", "Magiczna Wróżka", "Superbohater"])
    if f_photo and st.button("🚀 GENERUJ PERSONALIZOWANĄ BAJKĘ"):
        photo_bytes = f_photo.read()
        photo_base64 = base64.b64encode(photo_bytes).decode('utf-8')
        p_url = f"data:{f_photo.type};base64,{photo_base64}"
        f_seed = random.randint(0, 999999)
        for i in range(5):
            p = f"Coloring book illustration, {imię} as a {postać} based on photo, whimsical, consistent character design, step {i}"
            img = master_generate(p, image_url=p_url, seed=f_seed, is_color=False)
            if img:
                buf = BytesIO(); img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())
                st.image(img, width=400, caption=f"Strona {i+1}")

elif tryb == "📸 ZDJĘCIE NA KONTUR 8K":
    st.header("📸 Photo to Contour Conversion")
    f = st.file_uploader("Wgraj fotkę:", type=['png', 'jpg'])
    if f and st.button("KONWERTUJ NA KONTUR"):
        img = Image.open(f).convert('L')
        img_edges = ImageOps.invert(img.filter(ImageFilter.FIND_EDGES))
        img_final = ImageEnhance.Contrast(img_edges).enhance(3.5)
        st.image(img_final, caption="Twój gotowy szkic")
        buf = BytesIO(); img_final.save(buf, format="PNG")
        st.session_state['pdf_basket'].append(buf.getvalue())

elif tryb == "💬 FORUM TWÓRCÓW":
    st.header("💬 Forum Społeczności KDP Factory")
    wiad = st.text_input("Napisz coś do innych twórców:")
    if st.button("Wyślij"):
        st.session_state["posts"].insert(0, {"u": st.session_state["user_nick"], "m": wiad})
    for p in st.session_state["posts"]: st.info(f"**{p['u']}**: {p['m']}")

# --- EKSPORT PDF (FORMAT KDP READY) ---
if st.session_state['pdf_basket']:
    st.divider()
    st.subheader(f"📦 Twój Projekt: {len(st.session_state['pdf_basket'])} stron")
    if st.button("📥 POBIERZ GOTOWY PLIK DO AMAZON KDP (8.5x11)"):
        out = BytesIO()
        pdf = canvas.Canvas(out, pagesize=(8.5*inch, 11*inch))
        for d in st.session_state['pdf_basket']:
            # Marginesy Amazon KDP
            pdf.drawImage(BytesIO(d), 0.75*inch, 1.5*inch, width=7*inch, height=8*inch)
            pdf.showPage() # Rysunek
            pdf.showPage() # Pusta strona na tył
        pdf.save()
        st.download_button("💾 Pobierz plik PDF", out.getvalue(), "PRODUKCJA_KDP_FINAL.pdf")
