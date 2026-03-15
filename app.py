import streamlit as st
import os, fal_client, requests, random, base64
from deep_translator import GoogleTranslator
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# --- KONFIGURACJA ---
os.environ["FAL_KEY"] = "cf0a6c98-7933-45df-918d-5757b24e9a30:afc267a3e94340879464bbea2862b40b"

st.set_page_config(page_title="KDP Design Studio Pro", layout="wide")
translator = GoogleTranslator(source='pl', target='en')

if "pdf_basket" not in st.session_state: st.session_state["pdf_basket"] = []
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False

# --- LOGOWANIE ---
if not st.session_state["authenticated"]:
    st.title("✨ KDP Design Studio Login")
    u, p = st.text_input("Użytkownik:"), st.text_input("Hasło:", type="password")
    if st.button("Zaloguj"):
        if u == "admin" and p == "KDP2026":
            st.session_state["authenticated"] = True
            st.rerun()
    st.stop()

# --- SILNIK GRAFICZNY (PREMIUM LINE ART) ---
def master_generate(prompt, is_color=False, image_url=None, seed=None):
    try:
        # Wymuszamy nowy seed, jeśli nie jest podany, dla pełnej unikalności
        current_seed = seed if seed is not None else random.randint(0, 10**9)
        
        # Profesjonalny prompt w stylu premium line-art
        clean_p = f"{prompt}, professional coloring book line art, vector style, clean black contours, pure white background, no gray areas, high resolution, 8k"
        
        args = {"prompt": clean_p, "image_size": "square_hd", "seed": current_seed}
        if image_url: args["image_url"] = image_url

        res = fal_client.subscribe("fal-ai/flux/schnell", arguments=args)
        img_data = requests.get(res['images'][0]['url']).content
        img = Image.open(BytesIO(img_data))
        
        if not is_color:
            img = img.convert('L')
            # Balans kontrastu dla gładkich linii (bez pikselozy)
            img = ImageEnhance.Contrast(img).enhance(3.0) 
            img = img.filter(ImageFilter.SMOOTH_MORE)
            img = img.filter(ImageFilter.SHARPEN)
        
        return img.resize((img.size[0]*2, img.size[1]*2), Image.LANCZOS)
    except Exception as e:
        st.error(f"Błąd generowania: {e}")
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.title("🖌️ Studio Menu")
    tryb = st.selectbox("Wybierz narzędzie:", [
        "🎨 Generator Kolekcji", 
        "🦁 Eksplorator Nisz (SEO)", 
        "📖 Studio Bajek AI", 
        "📸 Konwerter Zdjęć"
    ])
    st.divider()
    if st.button("🗑️ Wyczyść projekt"):
        st.session_state['pdf_basket'] = []; st.rerun()

# --- GENERATOR KOLEKCJI (DAWNIEJ HURT) ---
if tryb == "🎨 Generator Kolekcji":
    st.header("🎨 Generator Nowej Kolekcji")
    st.write("Stwórz spójną serię grafik gotowych do publikacji.")
    
    col1, col2, col3 = st.columns(3)
    with col1: kat = st.selectbox("Kategoria:", ["Natura i Przyroda", "Zwierzęta", "Mandale", "Architektura", "Fantastyka"])
    with col2: styl = st.selectbox("Stylistyka:", ["Szczegółowa (Fine)", "Bold & Easy (Grube linie)", "Zentangle"])
    with col3: ile = st.slider("Liczba stron w serii:", 1, 50, 20)
    
    temat_user = st.text_input("O czym ma być ta kolekcja? (np. 'Magiczne grzyby w lesie')")
    
    if st.button("🔥 Generuj Kolekcję"):
        if not temat_user:
            st.error("Podaj temat kolekcji!")
        else:
            bar = st.progress(0)
            status = st.empty()
            grid = st.columns(4)
            
            kat_map = {"Natura i Przyroda": "nature and forest", "Zwierzęta": "wildlife animals", "Mandale": "ornamental mandala", "Architektura": "historical buildings", "Fantastyka": "magic creatures"}
            styl_map = {"Szczegółowa (Fine)": "intricate detailed lines", "Bold & Easy (Grube linie)": "simple bold thick lines", "Zentangle": "patterned doodle style"}
            
            eng_temat = translator.translate(temat_user)
            
            for i in range(ile):
                status.info(f"Tworzenie strony {i+1} z {ile}...")
                # Dodajemy unikalny modyfikator do każdego promptu, by wymusić różnorodność
                p = f"Coloring page of {eng_temat}, {kat_map[kat]}, {styl_map[styl]}, unique composition version {i}"
                
                # Każde wywołanie bez podanego seeda w pętli = unikalny obrazek
                img = master_generate(p)
                
                if img:
                    buf = BytesIO(); img.save(buf, format="PNG")
                    st.session_state['pdf_basket'].append(buf.getvalue())
                    with grid[i % 4]:
                        st.image(img, use_container_width=True, caption=f"Strona {i+1}")
                bar.progress((i+1)/ile)
            status.success(f"Kolekcja '{temat_user}' została pomyślnie wygenerowana!")

# --- POZOSTAŁE MODUŁY ---
elif tryb == "🦁 Eksplorator Nisz (SEO)":
    st.header("🦁 Eksplorator Nisz i SEO")
    if st.button("🔍 Skanuj rynek"):
        st.success("Aktualne trendy: 1. Bold & Easy Hygge, 2. Easter Gnomes, 3. Celestial Cats")

elif tryb == "📖 Studio Bajek AI":
    st.header("📖 Studio Personalizowanych Bajek")
    f = st.file_uploader("Wgraj zdjęcie twarzy:", type=['jpg', 'png'])
    if f
