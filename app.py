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
st.set_page_config(page_title="KDP Factory ULTRA 8K", layout="wide")
translator = GoogleTranslator(source='pl', target='en')

def generate_ultra(prompt, seed=None):
    try:
        # Maksymalnie uproszczony, techniczny prompt dla idealnych konturów
        final_p = (
            f"Ultra-clean coloring book page for kids, {prompt}. "
            "Pure black and white linear art, thick bold black outlines, solid flat white background. "
            "STRICTLY NO shading, NO gray, NO gradients, NO shadows, NO textures. "
            "Professional vector style, high contrast, 8k resolution."
        )
        
        actual_seed = seed if seed else random.randint(1, 1000000)
        
        # Używamy modelu DEV dla najwyższej precyzji
        arguments = {
            "prompt": final_p,
            "seed": actual_seed,
            "image_size": "portrait_4_3",
            "guidance_scale": 4.0,
            "num_inference_steps": 35 # Więcej kroków = czystsza linia
        }
        
        handler = fal_client.subscribe("fal-ai/flux/dev", arguments=arguments)
        url = handler['images'][0]['url']
        
        resp = requests.get(url)
        img = Image.open(BytesIO(resp.content))
        
        # Forsowanie czystej czerni i bieli
        img = img.convert('L')
        img = ImageEnhance.Contrast(img).enhance(3.0) 
        return img.convert('RGB')
    except Exception as e:
        st.error(f"Błąd: {e}")
        return None

# --- LOGIKA SESJI ---
if "basket" not in st.session_state: st.session_state["basket"] = []
if "auth" not in st.session_state: st.session_state["auth"] = False

if not st.session_state["auth"]:
    u = st.text_input("Nick:")
    p = st.text_input("Hasło:", type="password")
    if st.button("Zaloguj"):
        if u == "admin" and p == "KDP2026":
            st.session_state["auth"] = True
            st.rerun()
    st.stop()

# --- INTERFEJS ---
st.title("🚀 KDP ULTRA FACTORY")
opis = st.text_input("Co generujemy? (wpisz konkretnie, np. 'Lion head mandala' lub 'Sport car')")
ile = st.number_input("Ilość:", 1, 15, 1)

if st.button("GENERUJ SERIĘ"):
    eng = translator.translate(opis)
    cols = st.columns(3)
    for i in range(int(ile)):
        with st.spinner(f"Praca nad {i+1}..."):
            img = generate_ultra(eng, seed=random.randint(1, 999999))
            if img:
                cols[i % 3].image(img)
                buf = BytesIO()
                img.save(buf, format="PNG")
                st.session_state["basket"].append(buf.getvalue())

# --- PDF ---
if st.session_state["basket"]:
    st.divider()
    if st.button("📥 POBIERZ PDF KDP"):
        out = BytesIO()
        pdf = canvas.Canvas(out, pagesize=(8.5*inch, 11*inch))
        for img_data in st.session_state["basket"]:
            img_obj = ImageReader(BytesIO(img_data))
            pdf.drawImage(img_obj, 0.5*inch, 0.5*inch, width=7.5*inch, height=10*inch, preserveAspectRatio=True)
            pdf.showPage()
        pdf.save()
        st.download_button("💾 Zapisz plik", out.getvalue(), "kdp_final.pdf")
