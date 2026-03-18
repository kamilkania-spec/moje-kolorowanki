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
import json

# --- KONFIGURACJA ---
os.environ["FAL_KEY"] = "cf0a6c98-7933-45df-918d-5757b24e9a30:afc267a3e94340879464bbea2862b40b"

st.set_page_config(page_title="KDP Factory Pro 8K", layout="wide")
translator = GoogleTranslator(source='pl', target='en')

# --- BAZA DANYCH ---
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {
        "admin": {"pass": "KDP2026", "credits": 999999, "role": "admin"},
        "tester": {"pass": "KDP123", "credits": 50, "role": "user"}
    }
if "pdf_basket" not in st.session_state: st.session_state["pdf_basket"] = []
if "posts" not in st.session_state: st.session_state["posts"] = []
if "magic_p" not in st.session_state: st.session_state["magic_p"] = ""

# --- SILNIK (NAPRAWIONY BŁĄD ROZMIARU) ---
def master_generate(prompt, is_color=False, image_url=None, is_cover=False):
    nick = st.session_state.get("user_nick", "admin")
    try:
        size_val = "square_hd" if is_cover else "portrait_4_3" # FIX: portrait_4_3 zamiast 4_5
        arguments = {"prompt": prompt, "image_size": size_val, "seed": random.randint(1, 999999)}
        if image_url: arguments["image_url"] = image_url
            
        handler = fal_client.subscribe("fal-ai/flux/schnell", arguments=arguments)
        img = Image.open(BytesIO(requests.get(handler['images'][0]['url']).content))

        if not is_color:
            img = img.convert('L')
            img = ImageEnhance.Contrast(img).enhance(3.5)
            w, h = img.size
            img = img.resize((w*2, h*2), resample=Image.LANCZOS)
        
        if st.session_state.get("role") != "admin":
            st.session_state["user_db"][nick]["credits"] -= 1
        return img
    except Exception as e:
        st.error(f"⚠️ Błąd: {e}")
        return None

# --- LOGOWANIE ---
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
if not st.session_state["authenticated"]:
    st.title("🔐 Logowanie")
    u = st.text_input("Nick:")
    p = st.text_input("Hasło:", type="password")
    if st.button("Zaloguj się"):
        if u in st.session_state["user_db"] and st.session_state["user_db"][u]["pass"] == p:
            st.session_state["authenticated"] = True
            st.session_state["user_nick"] = u
            st.rerun()
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.title(f"🚀 KDP Factory Pro")
    st.write(f"Kredyty: {st.session_state['user_db'][st.session_state['user_nick']]['credits']}")
    
    st.write("---")
    st.write("📂 **W koszyku:**", len(st.session_state['pdf_basket']), "stron")
    
    # WYBÓR NARZĘDZIA (TWOJA LISTA)
    tryb = st.radio("WYBIERZ NARZĘDZIE:", [
        "🎨 Kolorowanki (Seria/Single)",
        "📖 Bajka z Dzieckiem",
        "🖍️ Opowieść Czarno-Biała",
        "🌅 Generator Okładek",
        "📸 Zdjęcie na Kontur",
        "🦊 Niche Finder & SEO",
        "💬 Forum",
        "📦 Eksport do PDF"
    ])
    
    st.write("---")
    if st.button("🗑️ Wyczyść cały projekt"):
        st.session_state['pdf_basket'] = []
        st.rerun()
    if st.button("🚪 Wyloguj"):
        st.session_state["authenticated"] = False
        st.rerun()

# --- GŁÓWNY INTERFEJS (Z TWOIM UKŁADEM) ---

if tryb == "🎨 Kolorowanki (Seria/Single)":
    st.header("🎨 Generator Kolorowanek")
    
    temat = st.text_input("O czym ma być grafika? (wpisz po polsku):", value="")
    
    # MAGICZNA PAŁECZKA OD RAZY POD SPODEM - TAK JAK CHCIAŁEŚ
    if st.button("🪄 Użyj Magicznej Pałeczki"):
        eng = translator.translate(temat)
        st.session_state["magic_p"] = f"Intricate coloring book page of {eng}, clean bold lines, white background, professional, 8k"
        st.success("Wygenerowano ulepszony prompt!")

    final_prompt = st.text_area("Podgląd promptu AI (możesz edytować):", value=st.session_state["magic_p"])
    
    ile = st.number_input("Ile grafik wygenerować w serii?", 1, 50, 1)
    
    if st.button("🚀 GENERUJ PROJEKT"):
        bar = st.progress(0)
        for i in range(ile):
            img = master_generate(final_prompt, is_color=False)
            if img:
                st.image(img, caption=f"Grafika {i+1}")
                buf = BytesIO(); img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())
            bar.progress((i+1)/ile)

elif tryb == "📖 Bajka z Dzieckiem":
    st.header("📖 Personalizowana Bajka (Kolor)")
    f = st.file_uploader("Wgraj zdjęcie dziecka:")
    imie = st.text_input("Imię dziecka:")
    fabula = st.text_area("O czym jest bajka?")
    if f and st.button("✨ Generuj Bajkę"):
        url = fal_client.upload_image(f.getvalue())
        for i in range(5):
            img = master_generate(f"Storybook page {i+1}, {imie}, {fabula}", is_color=True, image_url=url)
            if img:
                st.image(img, width=300)
                buf = BytesIO(); img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())

elif tryb == "🖍️ Opowieść Czarno-Biała":
    st.header("🖍️ Książka z opowieścią (Do kolorowania)")
    fab = st.text_area("Opisz fabułę całej książki:")
    if st.button("🚀 Generuj całą książkę"):
        for i in range(10):
            img = master_generate(f"Coloring page, scene {i+1}, {translator.translate(fab)}", is_color=False)
            if img:
                st.image(img, width=300)
                buf = BytesIO(); img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())

elif tryb == "🌅 Generator Okładek":
    st.header("🌅 Profesjonalna Okładka")
    o = st.text_input("Co ma być na okładce?")
    if st.button("🎨 Generuj Okładkę"):
        img = master_generate(translator.translate(o), is_color=True, is_cover=True)
        if img:
            st.image(img)
            buf = BytesIO(); img.save(buf, format="PNG")
            st.session_state['pdf_basket'].insert(0, buf.getvalue())

elif tryb == "📦 Eksport do PDF":
    st.header("📦 Pobieranie Projektu")
    if st.session_state['pdf_basket']:
        if st.button("📥 POBIERZ PDF (8.5x11 inch)"):
            out = BytesIO()
            pdf = canvas.Canvas(out, pagesize=(8.5*inch, 11*inch))
            for d in st.session_state['pdf_basket']:
                pdf.drawImage(BytesIO(d), 0.5*inch, 1*inch, width=7.5*inch, height=9*inch)
                pdf.showPage()
                pdf.showPage()
            pdf.save()
            st.download_button("Zapisz plik PDF", out.getvalue(), "kdp_final.pdf")
    else:
        st.warning("Twój koszyk jest pusty!")

elif tryb == "📸 Zdjęcie na Kontur":
    st.header("📸 Twoje zdjęcie -> Szkic")
    f_k = st.file_uploader("Wgraj zdjęcie:")
    if f_k and st.button("Konwertuj"):
        img = Image.open(f_k).convert('L').filter(ImageFilter.CONTOUR)
        img = ImageOps.invert(img)
        st.image(img)
        buf = BytesIO(); img.save(buf, format="PNG")
        st.session_state['pdf_basket'].append(buf.getvalue())

elif tryb == "💬 Forum":
    st.header("💬 Forum")
    w = st.text_input("Napisz coś:")
    if st.button("Wyślij"):
        st.session_state["posts"].insert(0, {"u": st.session_state["user_nick"], "m": w})
    for p in st.session_state["posts"]: st.info(f"**{p['u']}**: {p['m']}")

elif tryb == "🦊 Niche Finder & SEO":
    st.header("🦊 Trendy")
    st.write("`Celestial`, `Boho`, `Steampunk`")
