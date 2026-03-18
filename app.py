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

# --- TRENDY KDP 2026 ---
TRENDY_KDP = {
    "Easter 2026 (Wielkanoc)": ["Easter Bunny with flowers", "Spring animals coloring book", "Christian Easter symbols"],
    "Kawaii Food & Animals": ["Cute sushi with faces", "Bubble tea animals", "Kawaii dessert patterns"],
    "Self-Care Mandala": ["Geometric stress relief", "Nature-themed relaxation", "Floral patterns for adults"],
    "Toddler Learning": ["Alphabet coloring with animals", "Simple shapes and numbers", "Vehicles for toddlers"]
}

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { border-radius: 12px; transition: all 0.3s; }
    </style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_translator():
    return GoogleTranslator(source='pl', target='en')

translator = get_translator()

# --- SILNIK GENERUJĄCY --- 
def master_generate(prompt, styl, mode="bw", seed=None, audience="Dzieci"): 
    try: 
        if audience == "Dzieci":
            complexity = "very simple, large coloring areas, thick bold outlines, minimalist detail, child-friendly"
        else:
            complexity = "highly intricate, fine lines, very detailed patterns, complex shading-free texture, sophisticated for adults"

        quality_suffix = f"8k, high resolution, sharp focus, vector style, clean lines, crisp edges, {complexity}"
        
        if mode == "color": 
            final_p = f"Professional book illustration, {prompt}, {styl}, vibrant colors, smooth digital art, {quality_suffix}" 
        elif mode == "cover":
            final_p = f"Professional coloring book cover art, {prompt}, {styl}, vibrant, eye-catching, KDP style, {quality_suffix}"
        elif "mandala" in styl.lower(): 
            final_p = f"Intricate mandala coloring page, {prompt}, perfectly symmetrical, bold black outlines, pure white background, NO shading, NO gray, {quality_suffix}" 
        else: 
            final_p = f"Coloring book page, {styl}, {prompt}, thick bold black outlines, smooth curves, pure white background, NO shading, NO gray, NO textures, {quality_suffix}" 

        actual_seed = seed if seed is not None else random.randint(1, 99999999) 
        
        handler = fal_client.subscribe("fal-ai/flux/dev", arguments={ 
            "prompt": final_p, 
            "seed": actual_seed, 
            "num_inference_steps": 30,
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

# --- SIDEBAR (MENU) ---
with st.sidebar:
    st.title("🛠️ NARZĘDZIA KDP")
    tryb = st.radio("WYBIERZ MODUŁ:", [
        "🎨 Generator SketchForge", 
        "🔍 Nisze & Trendy KDP",
        "👶 Bajka Personalizowana",
        "🚀 Masowy Generator + Okładka"
    ])
    st.divider()
    if st.button("🗑️ WYCZYŚĆ PROJEKT"):
        st.session_state["pdf_basket"] = []
        st.rerun()

# --- NAGŁÓWEK ---
st.markdown(f"""
    <div style='display: flex; align-items: center; justify-content: space-between; padding-bottom: 20px;'>
        <div style='display: flex; align-items: center; gap: 10px;'>
            <span style='font-size: 24px; font-weight: bold; color: #4A90E2;'>🖋️ SketchForge Pro</span>
        </div>
        <div style='display: flex; gap: 10px; align-items: center;'>
            <span style='background: #f0f2f6; padding: 5px 15px; border-radius: 20px; font-size: 14px;'>💎 50</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- MODUŁ: NISZE & TRENDY ---
if tryb == "🔍 Nisze & Trendy KDP":
    st.header("🔍 Najlepsze Nisze & Sugestie AI")
    st.write("Wybierz trend, aby automatycznie przygotować opis dla generatora.")
    for nisza, sugestie in TRENDY_KDP.items():
        with st.expander(f"🔥 {nisza}"):
            for sug in sugestie:
                if st.button(f"Sugeruj: {sug}", key=f"sug_{sug}"):
                    st.session_state["ai_hint"] = sug
                    st.toast(f"Wybrano: {sug}")
                    st.info("Przejdź teraz do '🎨 Generator SketchForge'!")

# --- MODUŁ: GENERATOR SKETCHFORGE ---
elif tryb == "🎨 Generator SketchForge":
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.write("**Model AI**")
        st.selectbox("Model", ["SketchEngine 2.0 🪄", "Flux Dev"], label_visibility="collapsed")
    with col_m2:
        st.write("**Dla kogo?**")
        st.session_state["audience"] = st.segmented_control("Audience", ["Dzieci", "Dorośli"], default=st.session_state["audience"], label_visibility="collapsed")

    st.divider()
    st.write("**Twoja wizja**")
    prompt_input = st.text_area("Opis", placeholder="Np. Kotek w czapce...", value=st.session_state["ai_hint"], height=80, label_visibility="collapsed")
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        if st.button("🔄 Tłumacz na ENG", use_container_width=True):
            if prompt_input: st.session_state["ai_hint"] = translator.translate(prompt_input); st.rerun()
    with col_t2:
        if st.button("✨ Zainspiruj mnie", use_container_width=True):
            st.session_state["ai_hint"] = random.choice(["Kot w kosmosie", "Zaczarowany zamek", "Kawaii sushi", "Mandala kwiatowa"]); st.rerun()

    st.write("**Wybierz Styl**")
    styles_data = [
        {"name": "Domyślny", "icon": "🎨", "val": "line art"},
        {"name": "Rysunek", "icon": "👶", "val": "kids drawing"},
        {"name": "Anime", "icon": "👧", "val": "anime style outlines"},
        {"name": "Lego", "icon": "🧱", "val": "lego style"},
        {"name": "Zawiły", "icon": "🌸", "val": "intricate detailed"},
        {"name": "Mandala", "icon": "☸️", "val": "mandala geometric"},
        {"name": "Fantastyka", "icon": "🧙", "val": "fantasy"},
        {"name": "Komiks", "icon": "🗯️", "val": "comic style"},
        {"name": "Architektura", "icon": "🏠", "val": "architecture"},
        {"name": "Przestrzeń", "icon": "🚀", "val": "space"}
    ]
    s_cols = st.columns(5)
    for i, s in enumerate(styles_data):
        with s_cols[i % 5]:
            is_sel = st.session_state["wybrany_styl"] == s["name"]
            if st.button(f"{s['icon']}\n{s['name']}", key=f"s_{s['name']}", use_container_width=True, type="primary" if is_sel else "secondary"):
                st.session_state["wybrany_styl"] = s["name"]
                st.rerun()

    st.divider()
    col_g1, col_g2 = st.columns([2, 1])
    with col_g1: ile = st.number_input("Ilość stron", 1, 15, 1)
    with col_g2: mode = st.radio("Format", ["BW", "Kolor"], horizontal=True)

    if st.button("🚀 GENERUJ PROJEKT", type="primary", use_container_width=True):
        if not prompt_input: st.warning("Wpisz opis!")
        else:
            eng_p = translator.translate(prompt_input)
            r_cols = st.columns(2)
            for i in range(ile):
                with st.spinner(f"Tworzę {i+1}/{ile}..."):
                    s_val = next(s["val"] for s in styles_data if s["name"] == st.session_state["wybrany_styl"])
                    img = master_generate(eng_p, s_val, mode="bw" if mode == "BW" else "color", audience=st.session_state["audience"])
                    if img:
                        r_cols[i % 2].image(img, use_container_width=True)
                        buf = BytesIO(); img.save(buf, format="PNG")
                        st.session_state["pdf_basket"].append(buf.getvalue())
            st.success("Dodano do PDF!")

# --- MODUŁ: BAJKA PERSONALIZOWANA ---
elif tryb == "👶 Bajka Personalizowana":
    st.header("👶 Moja Własna Bajka")
    imie = st.text_input("Imię dziecka:")
    opis_p = st.text_area("O czym ma być bajka?")
    if st.button("STWÓRZ ILUSTRACJĘ", type="primary"):
        if imie and opis_p:
            with st.spinner("Tworzę..."):
                img = master_generate(translator.translate(f"Kid {imie}, {opis_p}"), "storybook", mode="color")
                if img:
                    st.image(img)
                    buf = BytesIO(); img.save(buf, format="PNG")
                    st.session_state["pdf_basket"].append(buf.getvalue())

# --- MODUŁ: MASOWY GENERATOR ---
elif tryb == "🚀 Masowy Generator + Okładka":
    st.header("🚀 Generator Serii KDP")
    m_temat = st.text_input("Temat serii:")
    m_ile = st.select_slider("Ilość:", [10, 20, 30])
    if st.button("START", type="primary"):
        if m_temat:
            # Okładka
            with st.spinner("Okładka..."):
                img_c = master_generate(translator.translate(m_temat), "cover art", mode="cover")
                if img_c:
                    buf = BytesIO(); img_c.save(buf, format="PNG")
                    st.session_state["pdf_basket"].insert(0, buf.getvalue())
            # Strony
            p_bar = st.progress(0)
            for i in range(m_ile):
                img = master_generate(translator.translate(m_temat), "line art", mode="bw", audience=st.session_state["audience"])
                if img:
                    buf = BytesIO(); img.save(buf, format="PNG")
                    st.session_state["pdf_basket"].append(buf.getvalue())
                p_bar.progress((i+1)/m_ile)
            st.success("Seria gotowa!")

# --- PDF EXPORT (SIDEBAR) ---
if st.session_state["pdf_basket"]:
    with st.sidebar:
        st.divider()
        st.write(f"📄 **Projekt: {len(st.session_state['pdf_basket'])} stron**")
        pdf_w, pdf_h = 8.5*inch, 11*inch
        out = BytesIO()
        c = canvas.Canvas(out, pagesize=(pdf_w, pdf_h))
        for d in st.session_state["pdf_basket"]:
            ir = ImageReader(BytesIO(d))
            c.drawImage(ir, 0.25*inch, 0.25*inch, width=pdf_w-0.5*inch, height=pdf_h-0.5*inch, preserveAspectRatio=True)
            c.showPage()
        c.save()
        st.download_button("📥 POBIERZ PDF (8.5x11)", out.getvalue(), "sketchforge_kdp.pdf", "application/pdf", use_container_width=True)
