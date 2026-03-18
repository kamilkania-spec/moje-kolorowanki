import streamlit as st 
import os 
import fal_client 
from deep_translator import GoogleTranslator 
from PIL import Image, ImageEnhance, ImageOps 
import requests 
from io import BytesIO 
from reportlab.pdfgen import canvas 
from reportlab.lib.units import inch 
from reportlab.lib.utils import ImageReader 
import random 

# --- KONFIGURACJA KDP EXPERT --- 
os.environ["FAL_KEY"] = "cf0a6c98-7933-45df-918d-5757b24e9a30:afc267a3e94340879464bbea2862b40b" 

st.set_page_config(page_title="SketchForge PRO - KDP Master", layout="centered") 

@st.cache_resource
def get_translator():
    return GoogleTranslator(source='pl', target='en')

translator = get_translator()

# --- DEFINICJA STYLÓW (GLOBALNA DLA SPÓJNOŚCI) ---
STYLES_DATA = [
    {"name": "Line Art", "icon": "🎨", "val": "clean line art"},
    {"name": "Zentangle", "icon": "🌸", "val": "zentangle patterns"},
    {"name": "Comic Book", "icon": "🗯️", "val": "american comic style outlines"},
    {"name": "Mandala", "icon": "☸️", "val": "geometric mandala"},
    {"name": "Storybook", "icon": "📖", "val": "classic storybook illustration"}
]

# --- SILNIK GENERUJĄCY (KDP OPTIMIZED) --- 
def master_generate(prompt, styl, mode="bw", seed=None, audience="Dzieci", consistency_context=None): 
    try: 
        base_quality = "ultra-high resolution, 300 DPI, sharp clean vector-like lines, crisp edges, professional print quality, no artifacts, no pixelation, no blur, high contrast, studio lighting"
        consistency_prompt = f"Consistent style with {consistency_context}," if consistency_context else ""
        
        if audience == "Dzieci":
            complexity = "very simple coloring page for toddlers, thick bold black outlines, large open spaces, minimal details, friendly look"
        else:
            complexity = "highly intricate adult coloring page, fine detailed lines, complex patterns, zentangle style, sophisticated composition"

        if mode == "color": 
            final_p = f"{consistency_prompt} Professional KDP book cover illustration, {prompt}, {styl}, vibrant CMYK colors, rich textures, smooth digital painting, {base_quality}" 
        elif mode == "cover":
            final_p = f"{consistency_prompt} Professional coloring book cover art, {prompt}, {styl}, eye-catching, vibrant CMYK profile, masterwork, {base_quality}"
        elif "mandala" in styl.lower(): 
            final_p = f"{consistency_prompt} Masterwork mandala, {prompt}, perfectly symmetrical geometric, bold black outlines on pure white background, NO shading, NO gray, {base_quality}, {complexity}" 
        else: 
            final_p = f"{consistency_prompt} Professional coloring page, {styl}, {prompt}, {complexity}, pure white background, solid black lines, NO gray, NO textures, {base_quality}" 

        actual_seed = seed if seed is not None else random.randint(1, 99999999) 
        
        result = fal_client.run("fal-ai/flux/dev", arguments={ 
            "prompt": final_p, 
            "seed": actual_seed, 
            "num_inference_steps": 35,
            "guidance_scale": 4.0,
            "width": 1024,
            "height": 1024
        }) 
        
        if not result or 'images' not in result: return None
        url = result['images'][0]['url'] 
        resp = requests.get(url) 
        img = Image.open(BytesIO(resp.content)) 
        
        if mode == "bw": 
            img = img.convert('L') 
            img = ImageOps.autocontrast(img, cutoff=2) 
            img = ImageEnhance.Contrast(img).enhance(4.0) 
            img = ImageEnhance.Sharpness(img).enhance(2.0) 
            img = img.convert('RGB') 
        
        return img 
    except Exception as e: 
        st.error(f"Błąd Silnika KDP: {e}") 
        return None 

# --- SESJA --- 
if "pdf_basket" not in st.session_state: st.session_state["pdf_basket"] = [] 
if "auth" not in st.session_state: st.session_state["auth"] = False 
# Zmiana domyślnego stylu na taki, który istnieje w STYLES_DATA
if "wybrany_styl" not in st.session_state: st.session_state["wybrany_styl"] = STYLES_DATA[0]["name"] 
if "ai_hint" not in st.session_state: st.session_state["ai_hint"] = "" 
if "audience" not in st.session_state: st.session_state["audience"] = "Dzieci"
if "story_context" not in st.session_state: st.session_state["story_context"] = ""

# --- LOGOWANIE --- 
if not st.session_state["auth"]: 
    st.title("🔐 SketchForge Master Login") 
    with st.form("login"):
        u = st.text_input("Nick") 
        p = st.text_input("Hasło", type="password") 
        if st.form_submit_button("Zaloguj"): 
            if u == "admin" and p == "KDP2026": 
                st.session_state["auth"] = True 
                st.rerun() 
            else:
                st.error("Błędne dane.")
    st.stop() 

# --- SIDEBAR ---
with st.sidebar:
    st.title("🛡️ KDP MASTER PANEL")
    tryb = st.radio("WYBIERZ NARZĘDZIE:", [
        "🎨 Generator SketchForge PRO", 
        "📚 Seria z Historią",
        "� Nisze & Trendy",
        "🌈 Bajka Personalizowana"
    ])
    st.divider()
    st.info("Zgodność: **300 DPI / KDP Ready**")
    if st.button("🗑️ WYCZYŚĆ PROJEKT"):
        st.session_state["pdf_basket"] = []
        st.rerun()

# --- NAGŁÓWEK ---
st.markdown(f"""
    <div style='display: flex; align-items: center; justify-content: space-between; padding-bottom: 20px;'>
        <div style='display: flex; align-items: center; gap: 10px;'>
            <span style='font-size: 24px; font-weight: bold; color: #2E7D32;'>🖋️ SketchForge Master</span>
        </div>
        <div style='display: flex; gap: 10px; align-items: center;'>
            <span style='background: #E8F5E9; padding: 5px 15px; border-radius: 20px; font-size: 14px; color: #2E7D32;'>PRO QUALITY</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- MODUŁY ---
if tryb == "🎨 Generator SketchForge PRO":
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.write("**Odbiorca**")
        st.session_state["audience"] = st.segmented_control("Audience", ["Dzieci", "Dorośli"], default=st.session_state["audience"], label_visibility="collapsed")
    with col_m2:
        st.write("**Format**")
        mode = st.radio("Format", ["BW (Druk)", "KOLOR"], horizontal=True, label_visibility="collapsed")

    st.divider()
    prompt_input = st.text_area("Opis ilustracji:", placeholder="Np. Kotek w kapeluszu...", value=st.session_state["ai_hint"], height=100)
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        if st.button("🔄 Tłumacz na ENG", use_container_width=True):
            if prompt_input: st.session_state["ai_hint"] = translator.translate(prompt_input); st.rerun()
    with col_t2:
        if st.button("✨ Zainspiruj mnie", use_container_width=True):
            st.session_state["ai_hint"] = random.choice(["Magiczny las", "Futurystyczny pojazd", "Zawiła mandala", "Urocze zwierzęta"]); st.rerun()

    st.write("**Wybierz Styl Artystyczny**")
    s_cols = st.columns(len(STYLES_DATA))
    for i, s in enumerate(STYLES_DATA):
        with s_cols[i]:
            is_sel = st.session_state["wybrany_styl"] == s["name"]
            if st.button(f"{s['icon']}\n{s['name']}", key=f"s_{s['name']}", use_container_width=True, type="primary" if is_sel else "secondary"):
                st.session_state["wybrany_styl"] = s["name"]
                st.rerun()

    if st.button("🚀 GENERUJ 300 DPI", type="primary", use_container_width=True):
        if not prompt_input: st.warning("Wpisz opis!")
        else:
            eng_p = translator.translate(prompt_input)
            with st.spinner("Pracuję nad jakością Expert..."):
                # Bezpieczne pobieranie stylu z wartością domyślną
                s_val = next((s["val"] for s in STYLES_DATA if s["name"] == st.session_state["wybrany_styl"]), "line art")
                img = master_generate(eng_p, s_val, mode="bw" if "BW" in mode else "color", audience=st.session_state["audience"])
                if img:
                    st.image(img, use_container_width=True)
                    buf = BytesIO(); img.save(buf, format="PNG")
                    st.session_state["pdf_basket"].append(buf.getvalue())
                    st.success("Gotowe!")

elif tryb == "📚 Seria z Historią":
    st.header("📚 Spójna Seria KDP")
    m_temat = st.text_input("Bohater/Temat:")
    m_opis = st.text_area("Fabuła:")
    m_ile = st.select_slider("Stron:", [5, 10, 15, 20])
    
    if st.button("🚀 GENERUJ SERIĘ", type="primary", use_container_width=True):
        if m_temat and m_opis:
            eng_topic = translator.translate(m_temat)
            eng_story = translator.translate(m_opis)
            
            with st.spinner("Okładka..."):
                cover = master_generate(f"Book cover: {eng_topic}", "Professional Art", mode="cover", audience=st.session_state["audience"])
                if cover:
                    buf = BytesIO(); cover.save(buf, format="PNG"); st.session_state["pdf_basket"].append(buf.getvalue())
            
            p_bar = st.progress(0)
            for i in range(m_ile):
                with st.spinner(f"Strona {i+1}..."):
                    img = master_generate(f"Adventure of {eng_topic}: {eng_story}", "line art", mode="bw", audience=st.session_state["audience"], consistency_context=eng_topic)
                    if img:
                        buf = BytesIO(); img.save(buf, format="PNG"); st.session_state["pdf_basket"].append(buf.getvalue())
                p_bar.progress((i+1)/m_ile)
            st.success("Seria gotowa!")

# --- PDF EXPORT ---
if st.session_state["pdf_basket"]:
    with st.sidebar:
        st.divider()
        st.subheader("📄 EKSPORT PDF")
        st.write(f"Stron: {len(st.session_state['pdf_basket'])}")
        
        bleed = 0.125 * inch
        pdf_w, pdf_h = 8.5 * inch + bleed, 11 * inch + bleed
        out = BytesIO()
        c = canvas.Canvas(out, pagesize=(pdf_w, pdf_h))
        
        for d in st.session_state["pdf_basket"]:
            ir = ImageReader(BytesIO(d))
            c.drawImage(ir, 0, 0, width=pdf_w, height=pdf_h, preserveAspectRatio=True)
            c.showPage()
        c.save()
        
        st.download_button("📥 POBIERZ PDF (KDP READY)", out.getvalue(), "kdp_master_project.pdf", "application/pdf", use_container_width=True)
