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

# --- SILNIK GENERUJĄCY (JAKOŚĆ 8K + ANATOMIA) ---
def master_generate(prompt, styl_wybrany, is_color=False):
    try:
        if is_color:
            final_p = f"Vibrant storybook illustration, {prompt}, highly detailed, perfect anatomy, 8k resolution, masterpiece"
        else:
            # Wymuszenie rąk, nóg i czystej czarno-białej linii
            final_p = (
                f"Coloring book page, {styl_wybrany}, {prompt}, "
                f"perfect anatomy, complete body with all 4 limbs visible, well-proportioned, "
                f"heavy thick black outlines, pure white background, "
                f"NO shading, NO shadows, NO grey, pure black and white, "
                f"smooth clean lines, 8k resolution, high contrast"
            )
        
        arguments = {"prompt": final_p}
        handler = fal_client.subscribe("fal-ai/flux/schnell", arguments=arguments)
        url = handler['images'][0]['url']
        
        resp = requests.get(url)
        img = Image.open(BytesIO(resp.content))
        
        if not is_color:
            # Podbicie kontrastu dla czystej linii bez niszczenia obrazu (pikselozy)
            img = img.convert('L')
            img = ImageEnhance.Contrast(img).enhance(2.0)
            img = img.convert('RGB') # Zabezpieczenie dla PDF
        
        # Powiększanie 8K
        w, h = img.size
        img = img.resize((w*2, h*2), resample=Image.LANCZOS)
        
        return img
    except Exception as e:
        st.error(f"Błąd API: {e}")
        return None

# --- INICJALIZACJA SESJI ---
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
            st.session_state["user_nick"] = u
            st.rerun()
    st.stop()

# --- SIDEBAR (PEŁNE MENU) ---
with st.sidebar:
    st.title(f"👤 {st.session_state.get('user_nick', 'Admin')}")
    tryb = st.radio("WYBIERZ NARZĘDZIE:", [
        "🎨 Generator Kategorii", 
        "🌈 Kolorowa Bajka AI", 
        "🚀 Masowy Generator (10-30)",
        "📷 Zdjęcie na Kontur"
    ])
    st.divider()
    if st.button("🗑️ Wyczyść Projekt (PDF)"):
        st.session_state['pdf_basket'] = []
        st.rerun()

# --- MODUŁ 1: GENERATOR KATEGORII (KAFELKI) ---
if tryb == "🎨 Generator Kategorii":
    st.header("🎨 Szybki Generator 8K")
    
    style_dict = {
        "Domyślny": "line art",
        "Architektura": "architecture, detailed buildings, perspective",
        "Przyroda": "nature, forest, flowers landscape",
        "Zwierzęta": "animal character, clear limbs and paws",
        "Mandala": "complex mandala, geometric patterns",
        "Fantasy": "mythical creatures, magic world",
        "Komiks": "comic style, bold outlines"
    }
    
    cols = st.columns(len(style_dict))
    for i, (s_name, s_val) in enumerate(style_dict.items()):
        with cols[i]:
            if st.button(s_name):
                st.session_state["wybrany_styl"] = s_val
                st.toast(f"Wybrano: {s_name}")

    st.info(f"Wybrany styl techniczny: **{st.session_state['wybrany_styl']}**")
    
    opis = st.text_input("Twoja wizja (np. Kot na wakacjach):", value=st.session_state["ai_hint"])
    
    if st.button("🚀 GENERUJ 8K"):
        with st.spinner("Pracuję nad jakością i anatomią..."):
            eng = translator.translate(opis)
            img = master_generate(eng, st.session_state["wybrany_styl"], is_color=False)
            if img:
                st.image(img, use_container_width=True)
                buf = BytesIO()
                img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())

    st.divider()
    st.subheader("💡 Nie masz pomysłu? Napisz słowo, AI Ci pomoże")
    slowo = st.text_input("Wpisz słowo (np. smok, las):")
    if st.button("✨ Podpowiedz mi"):
        if slowo:
            poms = [f"{slowo} w magicznym świecie", f"potężny {slowo} w stylu fantasy", f"uroczy uśmiechnięty {slowo}"]
            st.session_state["ai_hint"] = random.choice(poms)
            st.rerun()

# --- MODUŁ 2: KOLOROWA BAJKA ---
elif tryb == "🌈 Kolorowa Bajka AI":
    st.header("📖 Stwórz Kolorową Bajkę")
    f_zdjecie = st.file_uploader("Wgraj zdjęcie (opcjonalnie):", type=['png', 'jpg'])
    imię = st.text_input("Imię bohatera:")
    opowieść = st.text_area("O czym ma być ta scena?")
    
    if st.button("GENERUJ KOLOROWĄ ILUSTRACJĘ"):
        with st.spinner("Tworzę kolorową magię..."):
            prompt_bajka = f"Fairytale scene about {imię}, {opowieść}"
            img = master_generate(prompt_bajka, "storybook", is_color=True)
            if img:
                st.image(img, use_container_width=True)
                buf = BytesIO()
                img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())

# --- MODUŁ 3: MASOWY GENERATOR ---
elif tryb == "🚀 Masowy Generator (10-30)":
    st.header("🚀 Hurtowe Generowanie (Seria)")
    temat = st.text_input("Temat całej serii (np. Dinozaury w kosmosie):")
    ile = st.select_slider("Ilość:", options=[10, 20, 30])
    
    if st.button(f"GENERUJ {ile} SZTUK"):
        bar = st.progress(0)
        eng_t = translator.translate(temat)
        for i in range(ile):
            # Wymuszamy unikalność każdej sztuki + pełny kontur
            img = master_generate(f"{eng_t}, unique scene {i+1}", "line art", is_color=False)
            if img:
                buf = BytesIO()
                img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())
            bar.progress((i+1)/ile)
        st.success(f"Seria {ile} obrazków gotowa w koszyku!")

# --- MODUŁ 4: ZDJĘCIE NA KONTUR (PLACEHOLDER, JAK BYŁO) ---
elif tryb == "📷 Zdjęcie na Kontur":
    st.header("📷 Przerób Zdjęcie na Kolorowankę")
    st.info("Ta funkcja wymaga podpięcia modelu Image-to-Image. Zrobię to, gdy skończymy dopieszczać tekst na obraz!")

# --- EKSPORT PDF ---
if st.session_state['pdf_basket']:
    st.divider()
    st.subheader(f"📥 Twój Projekt KDP ({len(st.session_state['pdf_basket'])} stron)")
    if st.button("📥 POBIERZ PDF DO AMAZON KDP"):
        try:
            out = BytesIO()
            pdf = canvas.Canvas(out, pagesize=(8.5*inch, 11*inch))
            for d in st.session_state['pdf_basket']:
                img_obj = ImageReader(BytesIO(d))
                pdf.drawImage(img_obj, 0.5*inch, 1*inch, width=7.5*inch, height=9*inch)
                pdf.showPage()
                pdf.showPage() # Pusta strona na tył
            pdf.save()
            st.download_button("💾 Zapisz plik PDF", out.getvalue(), "kdp_final_8k.pdf", "application/pdf")
        except Exception as e:
            st.error(f"Błąd tworzenia PDF: {e}")
