import streamlit as st
import os
import fal_client
from deep_translator import GoogleTranslator
from PIL import Image, ImageEnhance, ImageDraw
import requests
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# --- CONFIG ---
os.environ["FAL_KEY"] = "cf0a6c98-7933-45df-918d-5757b24e9a30:afc267a3e94340879464bbea2862b40b"
HASLO = "KDP2026"

st.set_page_config(page_title="KDP AI Architect 8K", layout="wide")
translator = GoogleTranslator(source='pl', target='en')

if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    h = st.text_input("Hasło dostępu do Fabryki:", type="password")
    if st.button("Uruchom System"):
        if h == HASLO: st.session_state["auth"] = True; st.rerun()
    st.stop()

# --- ENGINE ---
def generate_storyboard(short_prompt, num_pages):
    """Tu dzieje się magia planowania historii"""
    st.write(f"🧠 AI planuje Twoją historię na {num_pages} stron...")
    # W wersji docelowej tu można podpiąć model tekstowy (np. GPT-4), 
    # tutaj robimy inteligentny podział promptów dla Fluxa.
    base_en = translator.translate(short_prompt)
    storyboard = []
    for i in range(num_pages):
        progress_desc = f"Part {i+1} of {num_pages}: "
        # Tworzymy progresję akcji
        if i == 0: context = "Introduction, setting the scene"
        elif i == num_pages - 1: context = "Finale, emotional ending"
        else: context = f"Development of adventure, scene {i+1}"
        
        full_scene = f"{progress_desc} {base_en}. {context}. Coloring page style, 8k, ultra-clean lines, white background, consistent characters."
        storyboard.append(full_scene)
    return storyboard

def get_8k_image(url):
    resp = requests.get(url)
    img = Image.open(BytesIO(resp.content)).convert('L')
    w, h = img.size
    img = img.resize((w*2, h*2), resample=Image.LANCZOS)
    return ImageEnhance.Contrast(img).enhance(3.0)

# --- UI ---
st.title("📖 KDP AI Architect: Od jednego zdania do 50 stron")

with st.sidebar:
    st.header("Parametry Wydawnicze")
    liczba_stron = st.number_input("Ilość stron:", 5, 100, 30)
    format_ksiazki = st.selectbox("Format:", ["8.5 x 11 in", "8.5 x 8.5 in"])
    dodaj_tekst = st.checkbox("Dodaj podpisy scen na dole", value=True)

historia_baza = st.text_area("Wpisz krótki zarys historii (AI zajmie się resztą):", 
                            placeholder="np. Trzy pieski jadą na wakacje, ale wracają osobno.")

if st.button("🚀 GENERUJCIE PEŁNĄ OPOWIEŚĆ 8K"):
    if historia_baza:
        story_plan = generate_storyboard(historia_baza, liczba_stron)
        st.session_state['book_pages'] = []
        
        prog_bar = st.progress(0)
        status = st.empty()
        
        for idx, scene_prompt in enumerate(story_plan):
            status.text(f"🎨 Rysuję stronę {idx+1} z {liczba_stron}...")
            
            # Generowanie obrazu
            handler = fal_client.submit("fal-ai/flux/schnell", arguments={"prompt": scene_prompt})
            result = handler.get()
            
            # Przetwarzanie do 8K
            img_processed = get_8k_image(result['images'][0]['url'])
            
            # Dodawanie napisu (opcjonalnie)
            if dodaj_tekst:
                draw = ImageDraw.Draw(img_processed)
                draw.text((100, img_processed.size[1]-100), f"Scene {idx+1}", fill=0)

            # Zapis do pamięci
            buf = BytesIO()
            img_processed.save(buf, format="PNG")
            st.session_state['book_pages'].append(buf.getvalue())
            
            prog_bar.progress((idx+1)/liczba_stron)
        
        st.success("✅ Twoja książka została w pełni zaprojektowana i narysowana!")

# --- EXPORT ---
if 'book_pages' in st.session_state and st.session_state['book_pages']:
    st.divider()
    if st.button("📥 POBIERZ KOMPLETNĄ KSIĄŻKĘ (PDF)"):
        out = BytesIO()
        p = canvas.Canvas(out, pagesize=(8.5*inch, 11*inch))
        for img_data in st.session_state['book_pages']:
            # Rysunek
            p.drawImage(BytesIO(img_data), 0.5*inch, 1*inch, width=7.5*inch, height=9*inch)
            p.showPage()
            # Pusta strona
            p.showPage()
        p.save()
        st.download_button("Pobierz gotowy plik PDF", out.getvalue(), "kdp_story_book.pdf")
