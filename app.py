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

st.set_page_config(page_title="KDP Factory Pro - iColoring Style", layout="wide")
translator = GoogleTranslator(source='pl', target='en')

# --- BAZA DANYCH ---
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {
        "admin": {"pass": "KDP2026", "credits": 999999, "role": "admin"},
        "tester": {"pass": "KDP123", "credits": 50, "role": "user"}
    }
if "pdf_basket" not in st.session_state: st.session_state["pdf_basket"] = []
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False

# --- LOGOWANIE ---
if not st.session_state["authenticated"]:
    st.title("✨ KDP Factory: Design Studio")
    u = st.text_input("Nick:")
    p = st.text_input("Hasło:", type="password")
    if st.button("Zaloguj się"):
        if u in st.session_state["user_db"] and st.session_state["user_db"][u]["pass"] == p:
            st.session_state["authenticated"] = True
            st.session_state["user_nick"] = u
            st.session_state["role"] = st.session_state["user_db"][u]["role"]
            st.rerun()
    st.stop()

# --- SILNIK GRAFICZNY PRO (iColoring Optimized) ---
def master_generate(prompt, seed=None):
    try:
        gen_seed = seed if seed is not None else random.randint(0, 9999999)
        # Optymalizacja pod czyste linie icoloring.ai
        clean_prompt = f"{prompt}, high quality line art, sharp edges, pure white background, zero grayscale, professional coloring book style"
        
        arguments = {"prompt": clean_prompt, "image_size": "square_hd", "seed": gen_seed}
        handler = fal_client.subscribe("fal-ai/flux/schnell", arguments=arguments)
        url = handler['images'][0]['url']
        resp = requests.get(url)
        img = Image.open(BytesIO(resp.content))
        
        # Konwersja na czysty kontur
        img = img.convert('L')
        img = ImageEnhance.Contrast(img).enhance(4.0)
        
        # Skalowanie 8K
        w, h = img.size
        img = img.resize((w*2, h*2), resample=Image.LANCZOS)
        return img
    except Exception as e:
        st.error(f"⚠️ Błąd AI: {e}")
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.title(f"Studio: {st.session_state['user_nick']}")
    st.write(f"🪙 Credits: {'∞' if st.session_state['role'] == 'admin' else st.session_state['user_db'][st.session_state['user_nick']]['credits']}")
    st.divider()
    if st.button("🗑️ Wyczysc sesje"):
        st.session_state['pdf_basket'] = []; st.rerun()

# --- INTERFEJS W STYLU ICOLORING.AI ---
st.title("🎨 Create Your Masterpiece")
st.subheader("Select Category & Bulk Generate")

# Wizualny wybór kategorii
col_cat1, col_cat2, col_cat3 = st.columns(3)
with col_cat1:
    cat = st.selectbox("Category:", ["🌿 Nature & Plants", "🐾 Animals", "💠 Mandalas"])
with col_cat2:
    style_type = st.selectbox("Style:", ["Fine Lines (Detailed)", "Bold & Easy", "Zentangle"])
with col_cat3:
    count = st.slider("Pages to generate:", 1, 50, 20)

prompt_input = st.text_input("What's on your mind? (e.g. 'cat in a garden', 'mystic owl'):")

# --- PROMPT MAPPING ---
cat_map = {
    "🌿 Nature & Plants": "botanical illustrations, garden scenes, forest landscapes",
    "🐾 Animals": "highly detailed animals, wildlife, cute creature portraits",
    "💠 Mandalas": "intricate mandalas, geometric patterns, sacred symmetry"
}

style_map = {
    "Fine Lines (Detailed)": "extremely intricate, thin lines, complex patterns",
    "Bold & Easy": "bold thick lines, simple shapes, easy to color",
    "Zentangle": "zen doodle, repetitive patterns, ornamental"
}

if st.button("🔥 START BULK GENERATION (KDP READY)"):
    if not prompt_input:
        st.warning("Please describe your idea first!")
    else:
        bar = st.progress(0)
        status = st.empty()
        
        eng_p = translator.translate(prompt_input)
        final_base_prompt = f"{cat_map[cat]}, {style_map[style_type]}, {eng_p}"
        
        cols = st.columns(4) # Podgląd w siatce jak na icoloring
        
        for i in range(count):
            status.info(f"Generating page {i+1} of {count}...")
            
            # Unikalność każdej strony w serii
            p = f"{final_base_prompt}, unique composition {random.randint(0, 1000)}"
            img = master_generate(p)
            
            if img:
                buf = BytesIO(); img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())
                
                # Wyświetlanie w siatce
                with cols[i % 4]:
                    st.image(img, use_container_width=True)
            
            bar.progress((i+1)/count)
        
        status.success(f"Successfully generated {count} pages!")

# --- EKSPORT PDF ---
if st.session_state['pdf_basket']:
    st.divider()
    st.subheader("📦 Final Book Package")
    if st.button("📥 DOWNLOAD KDP READY PDF (8.5x11)"):
        out = BytesIO()
        pdf = canvas.Canvas(out, pagesize=(8.5*inch, 11*inch))
        for d in st.session_state['pdf_basket']:
            pdf.drawImage(BytesIO(d), 0.75*inch, 1*inch, width=7*inch, height=9*inch)
            pdf.showPage()
            pdf.showPage() # Blank back page
        pdf.save()
        st.download_button("💾 Save PDF", out.getvalue(), "icoloring_kdp_batch.pdf")
