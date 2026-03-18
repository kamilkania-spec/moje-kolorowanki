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

st.set_page_config(page_title="SketchForge Pro - KDP Master", layout="centered") 

# --- CUSTOM CSS DLA STYLU SketchForge ---
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        border-radius: 12px;
        transition: all 0.3s;
    }
    .header-box {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px;
        background: white;
        border-bottom: 1px solid #eee;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_translator():
    return GoogleTranslator(source='pl', target='en')

translator = get_translator()

# --- SILNIK GENERUJĄCY --- 
def master_generate(prompt, styl, mode="bw", seed=None, audience="Dzieci"): 
    try: 
        # Instrukcje złożoności zależne od odbiorcy
        if audience == "Dzieci":
            complexity = "very simple, large coloring areas, thick bold outlines, minimalist detail, child-friendly"
        else:
            complexity = "highly intricate, fine lines, very detailed patterns, complex shading-free texture, sophisticated for adults"

        quality_suffix = f"8k, high resolution, sharp focus, vector style, clean lines, crisp edges, {complexity}"
        
        if mode == "color": 
            final_p = f"Professional book illustration, {prompt}, {styl}, vibrant colors, smooth digital art, {quality_suffix}" 
        elif "mandala" in styl.lower(): 
            final_p = f"Intricate mandala coloring page, {prompt}, perfectly symmetrical, bold black outlines, pure white background, NO shading, NO gray, {quality_suffix}" 
        else: 
            final_p = f"Coloring book page, {styl}, {prompt}, thick bold black outlines, smooth curves, pure white background, NO shading, NO gray, NO textures, {quality_suffix}" 

        actual_seed = seed if seed is not None else random.randint(1, 99999999) 
        
        handler = fal_client.subscribe("fal-ai/flux/dev", arguments={ 
            "prompt": final_p, 
            "seed": actual_seed, 
            "num_inference_steps": 30, # Zwiększone dla detali
            "guidance_scale": 3.5 
        }) 
        
        result = handler.get() 
        if not result or 'images' not in result: return None

        url = result['images'][0]['url'] 
        resp = requests.get(url) 
        img = Image.open(BytesIO(resp.content)) 
        
        if mode == "bw": 
            img = img.convert('L') 
            img = ImageEnhance.Contrast(img).enhance(3.0) 
            img = img.convert('RGB') 
        
        return img 
    except Exception as e: 
        st.error(f"Błąd API: {e}") 
        return None 

# --- SESJA --- 
if "pdf_basket" not in st.session_state: st.session_state["pdf_basket"] = [] 
if "auth" not in st.session_state: st.session_state["auth"] = False 
if "wybrany_styl" not in st.session_state: st.session_state["wybrany_styl"] = "Domyślny" 
if "ai_hint" not in st.session_state: st.session_state["ai_hint"] = "" 
if "audience" not in st.session_state: st.session_state["audience"] = "Dzieci"

# --- LOGOWANIE --- 
if not st.session_state["auth"]: 
    st.title("🔐 SketchForge Login") 
    with st.form("login"):
        u = st.text_input("Nick") 
        p = st.text_input("Hasło", type="password") 
        if st.form_submit_button("Zaloguj"): 
            if u == "admin" and p == "KDP2026": 
                st.session_state["auth"] = True 
                st.rerun() 
    st.stop() 

# --- NAGŁÓWEK (STYL SketchForge) ---
st.markdown("""
    <div style='display: flex; align-items: center; justify-content: space-between; padding-bottom: 20px;'>
        <div style='display: flex; align-items: center; gap: 10px;'>
            <span style='font-size: 24px;'>☰</span>
            <span style='font-size: 24px; font-weight: bold; color: #4A90E2;'>🖋️ SketchForge</span>
        </div>
        <div style='display: flex; gap: 10px; align-items: center;'>
            <span style='background: #f0f2f6; padding: 5px 15px; border-radius: 20px; font-size: 14px;'>💎 50</span>
            <span style='font-size: 20px; color: #ccc;'>+</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- WYBÓR MODELU I ODBIORCY ---
col_m1, col_m2 = st.columns(2)
with col_m1:
    st.write("**Model AI**")
    model_opt = st.selectbox("Wybierz model AI", ["SketchEngine 2.0 🪄", "Flux Dev (Premium)"], label_visibility="collapsed")
with col_m2:
    st.write("**Dla kogo?**")
    audience = st.segmented_control("Grupa docelowa", ["Dzieci", "Dorośli"], default="Dzieci", key="audience_ctrl", label_visibility="collapsed")
    st.session_state["audience"] = audience

st.caption(f"Aktualnie optymalizuję pod: **{st.session_state['audience']}** (złożoność: {'niska' if st.session_state['audience'] == 'Dzieci' else 'wysoka'})")

# --- EDYTOR PROMPTU ---
st.divider()
st.write("**Twoja wizja**")
prompt_input = st.text_area("Opis", placeholder="Wpisz swój tekst (np. Piesek w czapce)...", value=st.session_state["ai_hint"], height=80, label_visibility="collapsed")

col_tools1, col_tools2 = st.columns(2)
with col_tools1:
    if st.button("🔄 Tłumacz na ENG", use_container_width=True):
        if prompt_input:
            translated = translator.translate(prompt_input)
            st.session_state["ai_hint"] = translated
            st.rerun()
with col_tools2:
    if st.button("✨ Zainspiruj mnie", use_container_width=True):
        pomysly = ["Kot w kosmosie", "Zaczarowany zamek", "Słodki piesek kawaii", "Mandala z kwiatami", "Futurystyczne miasto"]
        st.session_state["ai_hint"] = random.choice(pomysly)
        st.rerun()

# --- WYBÓR STYLU ---
st.write("**Wybierz Styl**")
styles_data = [
    {"name": "Domyślny", "icon": "🎨", "val": "line art"},
    {"name": "Rysunek", "icon": "👶", "val": "kids drawing"},
    {"name": "Anime", "icon": "👧", "val": "anime style outlines"},
    {"name": "Lego", "icon": "🧱", "val": "lego blocks style"},
    {"name": "Zawiły", "icon": "🌸", "val": "intricate detailed"},
    {"name": "Mandala", "icon": "☸️", "val": "mandala geometric"},
    {"name": "Fantastyka", "icon": "🧙", "val": "fantasy world"},
    {"name": "Komiks", "icon": "🗯️", "val": "comic book style"},
    {"name": "Architektura", "icon": "🏠", "val": "architecture blueprint"},
    {"name": "Przestrzeń", "icon": "🚀", "val": "outer space galaxy"}
]

cols = st.columns(5)
for i, s in enumerate(styles_data):
    with cols[i % 5]:
        is_selected = st.session_state["wybrany_styl"] == s["name"]
        btn_type = "primary" if is_selected else "secondary"
        if st.button(f"{s['icon']}\n{s['name']}", key=f"style_{s['name']}", use_container_width=True, type=btn_type):
            st.session_state["wybrany_styl"] = s["name"]
            st.rerun()

# --- GENEROWANIE ---
st.divider()
col_gen1, col_gen2 = st.columns([2, 1])
with col_gen1:
    ile = st.number_input("Ilość stron (1-15)", 1, 15, 1)
with col_gen2:
    mode = st.radio("Format", ["BW (KDP)", "Kolor"], horizontal=True)

if st.button("🚀 GENERUJ DLA: " + st.session_state["audience"].upper(), type="primary", use_container_width=True):
    if not prompt_input:
        st.warning("Wpisz opis!")
    else:
        eng_prompt = translator.translate(prompt_input)
        st.write("---")
        res_cols = st.columns(2)
        for i in range(ile):
            with st.spinner(f"Tworzę stronę {i+1}/{ile}..."):
                style_val = next(s["val"] for s in styles_data if s["name"] == st.session_state["wybrany_styl"])
                m = "bw" if mode == "BW (KDP)" else "color"
                img = master_generate(eng_prompt, style_val, mode=m, audience=st.session_state["audience"])
                if img:
                    res_cols[i % 2].image(img, use_container_width=True)
                    buf = BytesIO()
                    img.save(buf, format="PNG")
                    st.session_state["pdf_basket"].append(buf.getvalue())
        st.success(f"Gotowe! Dodano {ile} grafik do projektu PDF.")

# --- KOSZYK PDF ---
if st.session_state["pdf_basket"]:
    with st.sidebar:
        st.header("📄 Twój Projekt KDP")
        st.write(f"Ilość stron: {len(st.session_state['pdf_basket'])}")
        
        pdf_width, pdf_height = 8.5 * inch, 11 * inch
        pdf_buffer = BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=(pdf_width, pdf_height))
        for data in st.session_state["pdf_basket"]:
            img_reader = ImageReader(BytesIO(data))
            margin = 0.25 * inch
            c.drawImage(img_reader, margin, margin, width=pdf_width-2*margin, height=pdf_height-2*margin, preserveAspectRatio=True)
            c.showPage()
        c.save()
        
        st.download_button("📥 POBIERZ PDF (8.5x11)", pdf_buffer.getvalue(), "sketchforge_project.pdf", "application/pdf", use_container_width=True)
        if st.button("🗑️ Wyczyść wszystko", use_container_width=True):
            st.session_state["pdf_basket"] = []
            st.rerun()
