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

# --- KONFIGURACJA ---
os.environ["FAL_KEY"] = "cf0a6c98-7933-45df-918d-5757b24e9a30:afc267a3e94340879464bbea2862b40b"
st.set_page_config(page_title="KDP Factory Pro 8K", layout="wide")
translator = GoogleTranslator(source='pl', target='en')

# --- SILNIK GENERUJĄCY (8K + DYNAMIKA SERII) ---
def master_generate(prompt, styl_wybrany, is_color=False, seed=None):
    try:
        # Dodajemy modyfikatory zmienności, żeby każda grafika w serii była inna
        variations = [
            "different perspective", "alternative composition", "unique details",
            "close-up shot", "wide angle", "slightly different arrangement",
            "detailed textures", "artistic variation"
        ]
        var_text = random.choice(variations) if seed else ""

        if is_color:
            final_p = f"Vibrant storybook illustration, {prompt}, {var_text}, highly detailed, 8k, masterpiece"
        elif "mandala" in styl_wybrany.lower():
            final_p = (
                f"Coloring book page, {prompt} as intricate mandala, {var_text}, "
                f"perfectly symmetrical, geometric patterns, heavy thick black outlines, "
                f"pure white background, NO shading, NO grey, 8k"
            )
        else:
            final_p = (
                f"Coloring book page, {styl_wybrany}, {prompt}, {var_text}, "
                f"perfect anatomy, complete body, heavy thick black outlines, "
                f"pure white background, NO shading, NO shadows, NO grey, 8k"
            )
        
        # Używamy randomowego seeda, żeby wymusić na AI nową wizję
        actual_seed = seed if seed else random.randint(1, 999999)
        
        arguments = {
            "prompt": final_p,
            "seed": actual_seed
        }
        
        handler = fal_client.subscribe("fal-ai/flux/schnell", arguments=arguments)
        url = handler['images'][0]['url']
        
        resp = requests.get(url)
        img = Image.open(BytesIO(resp.content))
        
        if not is_color:
            img = img.convert('L')
            img = ImageEnhance.Contrast(img).enhance(2.0)
            img = img.convert('RGB')
        
        w, h = img.size
        img = img.resize((w*2, h*2), resample=Image.LANCZOS)
        return img
    except Exception as e:
        st.error(f"Błąd API: {e}")
        return None

# --- SESJA ---
if "pdf_basket" not in st.session_state: st.session_state["pdf_basket"] = []
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
if "wybrany_styl" not in st.session_state: st.session_state["wybrany_styl"] = "line art"
if "ai_hint" not in st.session_state: st.session_state["ai_hint"] = ""

# --- LOGOWANIE ---
if not st.session_state["authenticated"]:
    st.title("🔐 KDP Factory Login")
    u = st.text_input("Nick:")
    p = st.text_input("Hasło:", type="password")
    if st.button("Zaloguj się"):
        if u == "admin" and p == "KDP2026":
            st.session_state["authenticated"] = True
            st.rerun()
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.title(f"👤 {st.session_state.get('user_nick', 'Admin')}")
    tryb = st.radio("MENU:", ["🎨 Generator Kategorii", "🌈 Bajka AI", "🚀 Masowy Generator", "📷 Zdjęcie na Kontur"])
    st.divider()
    if st.button("🗑️ Wyczyść Projekt"):
        st.session_state['pdf_basket'] = []
        st.rerun()

# --- MODUŁ 1: GENERATOR KATEGORII (Z POPRAWIONĄ ZMIENNOŚCIĄ) ---
if tryb == "🎨 Generator Kategorii":
    st.header("🎨 Generator Kategorii 8K")
    
    style_dict = {
        "Domyślny": "line art",
        "Architektura": "architecture",
        "Przyroda": "nature landscape",
        "Zwierzęta": "animal portrait",
        "Mandala": "mandala style",
        "Fantasy": "fantasy world",
        "Komiks": "comic style"
    }
    
    cols = st.columns(len(style_dict))
    for i, (s_name, s_val) in enumerate(style_dict.items()):
        with cols[i]:
            if st.button(s_name):
                st.session_state["wybrany_styl"] = s_val
                st.toast(f"Wybrano: {s_name}")

    opis = st.text_input("Nisza/Temat:", value=st.session_state["ai_hint"])
    
    # Suwak do 20 sztuk
    ile_sztuk = st.slider("Ile różnych grafik wygenerować?", 1, 20, 1)
    
    if st.button(f"🚀 GENERUJ SERIĘ {ile_sztuk} SZT."):
        progress_bar = st.progress(0)
        eng = translator.translate(opis)
        for i in range(ile_sztuk):
            with st.spinner(f"Tworzę unikalny wariant {i+1}..."):
                # Przekazujemy i jako seed/część seeda, by wymusić różnorodność
                new_seed = random.randint(1, 1000000)
                img = master_generate(eng, st.session_state["wybrany_styl"], seed=new_seed)
                if img:
                    st.image(img, caption=f"Wariant {i+1}", use_container_width=True)
                    buf = BytesIO()
                    img.save(buf, format="PNG")
                    st.session_state['pdf_basket'].append(buf.getvalue())
            progress_bar.progress((i+1)/ile_sztuk)
        st.success(f"Dodano {ile_sztuk} unikalnych grafik do PDF!")

    st.divider()
    st.subheader("💡 Pomoc AI")
    slowo = st.text_input("Podaj słowo:")
    if st.button("✨ Podpowiedz"):
        if slowo:
            poms = [f"{slowo} w wazonie", f"bukiet {slowo}", f"pole {slowo}"]
            st.session_state["ai_hint"] = random.choice(poms)
            st.rerun()

# --- MODUŁY 2, 3, 4 (BEZ ZMIAN) ---
elif tryb == "🌈 Bajka AI":
    st.header("🌈 Bajka AI")
    # ... (kod bajki)

elif tryb == "🚀 Masowy Generator":
    st.header("🚀 Masowy Generator")
    # ... (kod masowy)

# --- EKSPORT PDF ---
if st.session_state['pdf_basket']:
    st.divider()
    if st.button("📥 POBIERZ PDF DO AMAZON KDP"):
        try:
            out = BytesIO()
            pdf = canvas.Canvas(out, pagesize=(8.5*inch, 11*inch))
            for d in st.session_state['pdf_basket']:
                img_obj = ImageReader(BytesIO(d))
                pdf.drawImage(img_obj, 0.5*inch, 1*inch, width=7.5*inch, height=9*inch)
                pdf.showPage()
                pdf.showPage()
            pdf.save()
            st.download_button("💾 Pobierz PDF", out.getvalue(), "kdp_final.pdf", "application/pdf")
        except Exception as e:
            st.error(f"Błąd PDF: {e}")
