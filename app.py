import streamlit as st
import os
import fal_client
from deep_translator import GoogleTranslator
from PIL import Image, ImageEnhance
import requests
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
import random

# --- KLUCZ ---
os.environ["FAL_KEY"] = "cf0a6c98-7933-45df-918d-5757b24e9a30:afc267a3e94340879464bbea2862b40b"
st.set_page_config(page_title="KDP Factory Pro 8K", layout="wide")
translator = GoogleTranslator(source='pl', target='en')

def master_generate(prompt, styl_wybrany, is_color=False, seed=None):
    try:
        # Bardziej rygorystyczny prompt dla czystości linii
        if is_color:
            final_p = f"Professional kids book illustration, {prompt}, vibrant colors, clean lines, high resolution"
        else:
            final_p = (
                f"Clean coloring page for kids, {styl_wybrany}, {prompt}. "
                "Pure black and white, thick bold black outlines, solid white background. "
                "NO shading, NO gradients, NO gray scale, NO textures, NO realistic fur, NO muscle detail. "
                "Minimalistic vector style, professional line art, 8k."
            )
        
        actual_seed = seed if seed else random.randint(1, 1000000)
        
        # Przełączamy na model DEV dla lepszej jakości detali
        arguments = {
            "prompt": final_p,
            "seed": actual_seed,
            "image_size": "landscape_4_3" if "pojazd" in prompt.lower() else "portrait_4_3",
            "guidance_scale": 3.5,
            "num_inference_steps": 28 # Więcej kroków = lepsza jakość linii
        }
        
        handler = fal_client.subscribe("fal-ai/flux/dev", arguments=arguments)
        url = handler['images'][0]['url']
        
        resp = requests.get(url)
        img = Image.open(BytesIO(resp.content))
        
        if not is_color:
            img = img.convert('L') # Czarno-białe
            img = ImageEnhance.Contrast(img).enhance(2.5) # Mocniejszy kontrast dla białego tła
            img = img.convert('RGB')
        
        return img
    except Exception as e:
        st.error(f"Błąd: {e}")
        return None

# --- SESJA I LOGOWANIE ---
if "pdf_basket" not in st.session_state: st.session_state["pdf_basket"] = []
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔐 KDP Factory Login")
    u = st.text_input("Nick:")
    p = st.text_input("Hasło:", type="password")
    if st.button("Zaloguj się"):
        if u == "admin" and p == "KDP2026":
            st.session_state["authenticated"] = True
            st.rerun()
    st.stop()

# --- INTERFEJS ---
with st.sidebar:
    st.title("⚙️ PANEL STEROWANIA")
    tryb = st.radio("WYBIERZ:", ["🎨 Generator", "🚀 Masowy", "🌈 Bajka"])
    if st.button("🗑️ Wyczyść Projekt"):
        st.session_state['pdf_basket'] = []
        st.rerun()

if tryb == "🎨 Generator":
    st.header("🎨 Profesjonalny Generator Konturów")
    
    opis = st.text_input("Co rysujemy? (np. sportowe auto, uroczy kotek)")
    ile = st.slider("Ile wariantów?", 1, 15, 1)
    
    if st.button(f"🚀 GENERUJ"):
        eng = translator.translate(opis)
        cols = st.columns(2)
        for i in range(ile):
            with st.spinner(f"Generuję {i+1}..."):
                img = master_generate(eng, "simple line art", seed=random.randint(1,999999))
                if img:
                    cols[i % 2].image(img, use_container_width=True)
                    buf = BytesIO()
                    img.save(buf, format="PNG")
                    st.session_state['pdf_basket'].append(buf.getvalue())
        st.success("Dodano do PDF!")

# --- PDF ---
if st.session_state['pdf_basket']:
    st.divider()
    if st.button("📥 POBIERZ PDF (8.5x11 cali)"):
        out = BytesIO()
        pdf = canvas.Canvas(out, pagesize=(8.5*inch, 11*inch))
        for d in st.session_state['pdf_basket']:
            img_obj = ImageReader(BytesIO(d))
            # Skalowanie, żeby nie ucinało brzegów
            pdf.drawImage(img_obj, 0.25*inch, 0.5*inch, width=8*inch, height=10*inch, preserveAspectRatio=True)
            pdf.showPage()
        pdf.save()
        st.download_button("💾 Zapisz plik PDF", out.getvalue(), "kolorowanka_premium.pdf")
