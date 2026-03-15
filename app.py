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
# Twój klucz API i Hasło - Upewnij się, że są poprawne
os.environ["FAL_KEY"] = "cf0a6c98-7933-45df-918d-5757b24e9a30:afc267a3e94340879464bbea2862b40b"
HASLO_DO_FABRYKI = "KDP2026"

st.set_page_config(page_title="KDP Ultimate Production Studio", layout="wide")
translator = GoogleTranslator(source='pl', target='en')

# --- LOGOWANIE ---
if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    st.title("🔐 Autoryzacja Fabryki")
    h = st.text_input("Podaj hasło dostępowe:", type="password")
    if st.button("Uruchom System"):
        if h == HASLO_DO_FABRYKI:
            st.session_state["auth"] = True
            st.rerun()
        else:
            st.error("Błędne hasło!")
    st.stop()

# --- INICJALIZACJA ---
if 'pdf_basket' not in st.session_state:
    st.session_state['pdf_basket'] = []
if 'last_topic' not in st.session_state:
    st.session_state['last_topic'] = ""

# --- FUNKCJE POMOCNICZE ---
def process_8k(img_source, is_url=True):
    """Pobiera obraz i podbija go do jakości 8K (upscaling cyfrowy)"""
    if is_url:
        resp = requests.get(img_source)
        img = Image.open(BytesIO(resp.content)).convert('L')
    else:
        img = Image.open(img_source).convert('L')
    w, h = img.size
    # Upscaling cyfrowy (2x) dla gładkości
    img = img.resize((w*2, h*2), resample=Image.LANCZOS)
    return ImageEnhance.Contrast(img).enhance(3.5)

def photo_to_outline(uploaded_file):
    """Zmienia wgrane zdjęcie w czysty kontur kolorowanki"""
    img = Image.open(uploaded_file).convert('L')
    # Algorytm wykrywania krawędzi i czyszczenia
    img = ImageEnhance.Contrast(img).enhance(2.5)
    img = img.point(lambda p: 0 if p < 140 else 255) # Threshold - najprostsze czyszczenie
    return img

def generate_seo(topic):
    """Generuje dane SEO dla Amazon KDP"""
    top = topic.capitalize()
    seo = {
        "title": f"{top} Coloring Book for Adults",
        "subtitle": f"Stress Relief Designs with {top} Themes - 8.5 x 11 Large Print Edition",
        "keywords": f"{topic}, adult coloring book, stress relief, gift idea, mindfulness, artistic designs, {topic} art, activity book",
        "description": f"Embark on a creative journey with our '{top} Coloring Book'. This book features unique, high-quality illustrations designed to provide hours of relaxation and creative expression. Perfect for artists of all levels!"
    }
    return seo

# --- SIDEBAR (NAWIGACJA) ---
with st.sidebar:
    st.title("🚀 KDP Command Center")
    # TWORZYMY CZWARTĄ OPCJĘ W MENU
    tryb = st.selectbox("Wybierz moduł pracy:", 
                        ["✏️ Tekst na Kolorowankę", 
                         "📸 Zdjęcie na Kolorowankę", 
                         "📖 Opowieść (Story Mode)",
                         "🦁 Generuj Serię Niszy (Zwierzęta/Tematy)"])
    st.divider()
    st.subheader("📦 Twój Projekt")
    st.write(f"Ilość stron w PDF: {len(st.session_state['pdf_basket'])}")
    if st.button("🗑️ Wyczyść Projekt"):
        st.session_state['pdf_basket'] = []
        st.session_state['last_topic'] = ""
        st.rerun()

# --- MODUŁY GŁÓWNE ---

# 1. TEKST NA KOLOROWANKĘ
if tryb == "✏️ Tekst na Kolorowankę":
    st.header("🎨 Zamień opis w grafikę 8K")
    prompt_pl = st.text_input("Opisz obrazek:", placeholder="np. Mała panda jedząca bambus")
    if st.button("Generuj i Dodaj do Książki"):
        if prompt_pl:
            st.session_state['last_topic'] = prompt_pl
            with st.spinner("Rysuję..."):
                eng = translator.translate(prompt_pl)
                res = fal_client.submit("fal-ai/flux/schnell", arguments={
                    "prompt": f"Coloring page, {eng}, 8k, black and white, bold lines, white background, no shading"
                })
                img_final = process_8k(res.get()['images'][0]['url'])
                buf = BytesIO()
                img_final.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())
                st.image(img_final, caption="Strona dodana!")

# 2. ZDJĘCIE NA KOLOROWANKĘ
elif tryb == "📸 Zdjęcie na Kolorowankę":
    st.header("📸 Twoje zdjęcie jako kolorowanka")
    foto = st.file_uploader("Wgraj zdjęcie:", type=['jpg', 'jpeg', 'png'])
    if foto and st.button("Przerób na kontur i Dodaj"):
        with st.spinner("Przetwarzam..."):
            img_outline = photo_to_outline(foto)
            buf = BytesIO()
            img_outline.save(buf, format="PNG")
            st.session_state['pdf_basket'].append(buf.getvalue())
            st.image(img_outline, caption="Zdjęcie przerobione!")

# 3. OPOWIEŚĆ (STORY MODE - DŁUGIE HISTORIE Z JEDNYM BOHATEREM)
elif tryb == "📖 Opowieść (Story Mode)":
    st.header("📖 AI Architect: Buduj całą historię")
    zarys = st.text_area("O czym ma być ta opowieść? (AI rozwinie historię i narysuje serię stron)")
    ile_stron_story = st.number_input("Ile stron?", 5, 100, 20)
    
    if st.button("🚀 GENERUJ PEŁNĄ OPOWIEŚĆ (MASOWO)"):
        if zarys:
            st.session_state['last_topic'] = zarys
            eng_base = translator.translate(zarys)
            bar = st.progress(0)
            for i in range(ile_stron_story):
                # Prompt dba o spójność historii ("Step X of Y")
                p = f"Step {i+1} of {ile_stron_story}: {eng_base}. Coloring page, 8k, consistent characters, bold black outlines, white background"
                res = fal_client.submit("fal-ai/flux/schnell", arguments={"prompt": p})
                img_story = process_8k(res.get()['images'][0]['url'])
                buf = BytesIO()
                img_story.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())
                bar.progress((i+1)/ile_stron_story)
            st.success("Opowieść gotowa!")

# 4. NOWY MODUŁ: GENEROWANIE SERII NISZY (ZWIERZĘTA/TEMATY)
elif tryb == "🦁 Generuj Serię Niszy (Zwierzęta/Tematy)":
    st.header("🦁 Generuj serię grafik w tym samym stylu")
    nisza_pl = st.text_input("Opisz ogólną niszę (np. Zwierzęta polarne, Podwodny świat, Dinozaury):")
    styl_pl = st.text_input("Wybierz styl (np. Witraż, Mandala, Realistyczny kontur, Prosty dla dzieci):")
    ile_stron_niche = st.number_input("Ilość grafik w serii?", 10, 50, 25)
    
    if st.button("🔥 GENERUJ SERIĘ 8K"):
        if nisza_pl and styl_pl:
            st.session_state['last_topic'] = f"{nisza_pl} in {styl_pl}"
            eng_nisza = translator.translate(nisza_pl)
            eng_styl = translator.translate(styl_pl)
            
            bar_n = st.progress(0)
            for i in range(ile_stron_niche):
                # Prompt dba o spójność STYLU
                prompt_n = f"Coloring page, {eng_nisza}, {eng_styl} style, unique {eng_nisza} character, 8k, black and white, bold clean outlines, white background, no shading"
                res = fal_client.submit("fal-ai/flux/schnell", arguments={"prompt": prompt_n})
                img_n = process_8k(res.get()['images'][0]['url'])
                
                buf = BytesIO()
                img_n.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())
                bar_n.progress((i+1)/ile_stron_niche)
            st.success(f"Seria {ile_stron_niche} grafik została wygenerowana i dodana do projektu!")

# --- FINALIZACJA I SEO ---
if st.session_state['pdf_basket']:
    st.divider()
    col_pdf, col_seo = st.columns(2)
    
    with col_pdf:
        st.subheader("📑 Plik PDF (Wnętrze)")
        st.write(f"Twój projekt ma obecnie **{len(st.session_state['pdf_basket'])}** stron.")
        if st.button("📥 POBIERZ PEŁNĄ KSIĄŻKĘ (PDF)"):
            output = BytesIO()
            p = canvas.Canvas(output, pagesize=(8.5*inch, 11*inch))
            for data in st.session_state['pdf_basket']:
                # Rysunek z marginesem
                p.drawImage(BytesIO(data), 0.5*inch, 1*inch, width=7.5*inch, height=9*inch)
                p.showPage()
                p.showPage() # Pusta strona po każdym rysunku (Standard Premium)
            p.save()
            st.download_button("Kliknij, aby zapisać plik", output.getvalue(), "kdp_multi_studio.pdf", "application/pdf")

    with col_seo:
        st.subheader("📈 KDP SEO Assistant")
        if st.session_state['last_topic']:
            # Generujemy dane SEO na podstawie ostatniego tematu
            data_seo = generate_seo(st.session_state['last_topic'])
            st.info(f"**Title (zoptymalizowany):** {data_seo['title']}")
            st.info(f"**Subtitle (zoptymalizowany):** {data_seo['subtitle']}")
            st.code(f"Keywords (do skopiowania): {data_seo['keywords']}")
            st.write(f"**Description:** {data_seo['description']}")
        else:
            st.write("Wygeneruj coś, aby zobaczyć SEO.")
