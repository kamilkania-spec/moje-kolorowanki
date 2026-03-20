import os
import random
import zipfile
from io import BytesIO

import fal_client
import requests
import streamlit as st
from deep_translator import GoogleTranslator
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from openai import OpenAI

# --- Studio Configuration ---
# iColoring Pro Engine Configuration
os.environ["FAL_KEY"] = "cf0a6c98-7933-45df-918d-5757b24e9a30:afc267a3e94340879464bbea2862b40b"

st.set_page_config(
    page_title="iColoring Pro - Recraft Edition",
    page_icon="🖍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS: iColoring Premium Theme ---
st.markdown("""
    <style>
    :root {
        --primary-color: #FF4B4B;
        --bg-color: #F8F9FA;
    }
    .main { background-color: var(--bg-color); }
    .stButton>button {
        border-radius: 20px;
        font-weight: 600;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .style-card {
        background: white;
        padding: 15px;
        border-radius: 16px;
        border: 1px solid #E0E0E0;
        text-align: center;
        transition: all 0.3s;
    }
    .selected-style {
        border: 2px solid var(--primary-color) !important;
        background: #FFF5F5;
    }
    .tool-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 0;
        border-bottom: 2px solid #EEE;
        margin-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_translator():
    return GoogleTranslator(source="pl", target="en")

translator = get_translator()

# --- iColoring Master Engine (Recraft V3 Integration) ---
def icoloring_generate(prompt, style_config, mode="bw", audience="Dorośli", engine="Recraft V3"):
    try:
        # iColoring Secret Sauce: Multi-layer prompt engineering
        quality_prompt = (
            "Professional high-end line art illustration, masterwork, clean ink, "
            "ultra-sharp vector contours, white background, no grayscale, no shading, "
            "perfectly closed lines, cinematic composition, 8k resolution, 600 DPI quality"
        )
        
        audience_modifier = (
            "complex intricate patterns, fine lines, sophisticated for adults" 
            if audience == "Dorośli" else 
            "bold simple shapes, thick outlines, whimsical for kids"
        )

        final_prompt = f"{style_config['val']}, {prompt}, {quality_prompt}, {audience_modifier}"

        if engine == "Recraft V3":
            # Using Recraft V3 via OpenAI-compatible API
            # Initialize client with current token from session state
            current_recraft_client = OpenAI(
                base_url='https://external.api.recraft.ai/v1',
                api_key=st.session_state["recraft_token"],
            )
            response = current_recraft_client.images.generate(
                model="recraft-v3",
                prompt=final_prompt,
                size="1024x1024",
                n=1,
            )
            url = response.data[0].url
        else:
            # Fallback to FLUX PRO
            result = fal_client.run(
                "fal-ai/flux-pro/v1.1",
                arguments={
                    "prompt": final_prompt,
                    "width": 1024,
                    "height": 1024,
                    "prompt_upsampling": True,
                    "safety_tolerance": "5"
                },
            )
            if not result or "images" not in result: return None
            url = result["images"][0]["url"]

        img = Image.open(BytesIO(requests.get(url, timeout=60).content)).convert("RGB")

        if mode == "bw":
            return process_to_icoloring_standard(img)
        return img
    except Exception as e:
        st.error(f"iColoring Engine Error: {e}")
        return None

def process_to_icoloring_standard(image):
    # iColoring Advanced Post-Processing Pipeline
    gray = image.convert("L")
    # Adaptive thresholding for perfect lines
    clean = gray.point(lambda p: 255 if p > 220 else p)
    bw = clean.point(lambda p: 0 if p < 180 else 255).convert("1")
    # Smoothing & Denoising
    smooth = bw.convert("L").filter(ImageFilter.SMOOTH_MORE)
    final = smooth.point(lambda p: 0 if p < 128 else 255).convert("RGB")
    return final

# --- STYLES DATA: iColoring Premium Selection ---
STYLES_DATA = [
    {"name": "Master Line", "icon": "🖋️", "val": "professional clean line art, sharp ink"},
    {"name": "Anime Pro", "icon": "👧", "val": "high-end anime manga lineart, professional inking"},
    {"name": "Zen Mandala", "icon": "☸️", "val": "intricate symmetrical mandala, sacred geometry"},
    {"name": "Botanical", "icon": "🌿", "val": "elegant floral patterns, realistic leaf line art"},
    {"name": "Storybook", "icon": "📖", "val": "classic whimsical storybook illustration style"},
    {"name": "Comic Pop", "icon": "🗯️", "val": "modern comic book outlines, bold action style"}
]

# --- SESSION INITIALIZATION ---
if "basket" not in st.session_state: st.session_state["basket"] = []
if "auth" not in st.session_state: st.session_state["auth"] = False
if "selected_style" not in st.session_state: st.session_state["selected_style"] = STYLES_DATA[0]["name"]
if "recraft_token" not in st.session_state: st.session_state["recraft_token"] = ""

# --- LOGIN ---
if not st.session_state["auth"]:
    st.title("🔐 iColoring Pro Login")
    with st.form("login"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Access Studio"):
            if u == "admin" and p == "KDP2026":
                st.session_state["auth"] = True
                st.rerun()
    st.stop()

# --- SIDEBAR: iColoring Pro Tools ---
with st.sidebar:
    st.title("🖍️ iColoring Pro")
    menu = st.radio("STUDIO MODULES", [
        "🎨 Creative Generator",
        "📚 Series & Story Engine",
        "🔍 Market Niche Finder",
        "⚙️ Advanced Settings"
    ])
    st.divider()
    
    # API Key Management in Sidebar for easy access
    st.subheader("🔑 API Keys")
    st.info("Wpisz swój token poniżej, aby używać modelu Recraft V3.")
    st.session_state["recraft_token"] = st.text_input(
        "Recraft API Token", 
        value=st.session_state["recraft_token"], 
        type="password",
        placeholder="Tu wklej token..."
    )
    
    st.divider()
    st.write(f"📥 **Project Basket:** {len(st.session_state['basket'])} assets")
    if st.button("🗑️ Clear Workspace"):
        st.session_state["basket"] = []
        st.rerun()

# --- MAIN INTERFACE ---
st.markdown("""
    <div class='tool-header'>
        <span style='font-size: 32px; font-weight: 800; color: #FF4B4B;'>iColoring Pro Studio</span>
        <span style='background: #E8F5E9; padding: 8px 20px; border-radius: 30px; color: #2E7D32; font-weight: 700;'>ULTRA 600 DPI</span>
    </div>
""", unsafe_allow_html=True)

if menu == "🎨 Creative Generator":
    col1, col2 = st.columns([2, 1])
    with col1:
        st.write("**Vision Description**")
        user_prompt = st.text_area("Describe your masterpiece...", placeholder="e.g. A majestic lion with a crown of flowers...", height=120)
    with col2:
        st.write("**Generation Engine**")
        ai_engine = st.selectbox("Model", ["Flux Pro v1.1", "Recraft V3"], help="Recraft V3 wymaga własnego tokenu API.")
        st.write("**Target Audience**")
        audience = st.segmented_control("Audience", ["Dzieci", "Dorośli"], default="Dorośli")
        mode = st.radio("Output Format", ["BW Contours", "Full Color Cover"], horizontal=True)

    st.write("**Choose Professional Style**")
    s_cols = st.columns(len(STYLES_DATA))
    for i, s in enumerate(STYLES_DATA):
        with s_cols[i]:
            is_selected = st.session_state["selected_style"] == s["name"]
            if st.button(f"{s['icon']}\n{s['name']}", key=f"style_{s['name']}", 
                         use_container_width=True, 
                         type="primary" if is_selected else "secondary"):
                st.session_state["selected_style"] = s["name"]
                st.rerun()

    amount = st.slider("Number of Variations", 1, 10, 1)
    
    if st.button("🚀 GENERATE MASTERPIECE", type="primary", use_container_width=True):
        if not user_prompt:
            st.warning("Please enter a description.")
        elif not st.session_state["recraft_token"] and ai_engine == "Recraft V3":
            st.error("Please enter your Recraft API Token in the sidebar to use this engine.")
        else:
            eng_prompt = translator.translate(user_prompt)
            style_cfg = next(s for s in STYLES_DATA if s["name"] == st.session_state["selected_style"])
            
            res_cols = st.columns(2)
            for i in range(amount):
                with st.spinner(f"Rendering Asset {i+1} via {ai_engine}..."):
                    img = icoloring_generate(eng_prompt, style_cfg, 
                                           mode="bw" if "BW" in mode else "color", 
                                           audience=audience,
                                           engine=ai_engine)
                    if img:
                        res_cols[i % 2].image(img, use_container_width=True)
                        buf = BytesIO()
                        img.save(buf, format="PNG", dpi=(600,600))
                        st.session_state["basket"].append(buf.getvalue())
            st.success("Successfully added to project basket!")

# --- PDF EXPORT (KDP PREMIUM STANDARD) ---
if st.session_state["basket"]:
    with st.sidebar:
        st.divider()
        st.subheader("📦 Final Export")
        
        # Amazon KDP Premium Standard: 8.5x11 with 0.125 bleed
        pdf_w, pdf_h = 8.625 * inch, 11.25 * inch
        out = BytesIO()
        c = canvas.Canvas(out, pagesize=(pdf_w, pdf_h))
        
        for data in st.session_state["basket"]:
            ir = ImageReader(BytesIO(data))
            c.drawImage(ir, 0, 0, width=pdf_w, height=pdf_h, preserveAspectRatio=True)
            c.showPage()
        c.save()
        
        st.download_button("📥 DOWNLOAD KDP READY PDF", out.getvalue(), 
                         "icoloring_pro_project.pdf", "application/pdf", 
                         use_container_width=True)
