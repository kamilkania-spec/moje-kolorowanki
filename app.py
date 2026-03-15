import streamlit as st
import os
import requests
from PIL import Image
from io import BytesIO
import fal_client

# 1. DESIGN I KOLORY (Szarozielony Premium)
st.set_page_config(page_title="iColoring AI Studio", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #F5F5F0; }
    .stButton>button { background-color: #556B2F; color: white; border-radius: 12px; height: 3em; font-weight: bold; width: 100%; }
    .stSidebar { background-color: #E0E0D1; }
    .plan-card { background: white; padding: 15px; border-radius: 10px; border: 1px solid #556B2F; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# 2. SIDEBAR - SUBSKRYPCJE I NAWIGACJA
st.sidebar.title("💎 iColoring Premium")
st.sidebar.markdown("""
<div class="plan-card"><strong>Plan: Free Trial</strong><br><small>Pozostało: 3 kredyty</small></div>
""", unsafe_allow_html=True)

st.sidebar.subheader("Subskrypcje:")
if st.sidebar.button("7 Dni - $9.99"): st.sidebar.info("Link do Stripe...")
if st.sidebar.button("1 Miesiąc - $29.99"): st.sidebar.info("Link do Stripe...")
if st.sidebar.button("1 Rok - $199.99"): st.sidebar.info("Link do Stripe...")

st.sidebar.markdown("---")
tryb = st.sidebar.selectbox("Wybierz Tryb", ["Tekst na Kolorowankę", "Zdjęcie na Kolorowankę"])

# 3. OBSŁUGA API (Klucz pobierzemy z Secrets)

os.environ["FAL_KEY"] = "cf0a6c98-7933-45df-918d-5757b24e9a30:afc267a3e94340879464bbea2862b40b"

# 4. LOGIKA GŁÓWNA
st.title("🎨 iColoring Studio")

if tryb == "Tekst na Kolorowankę":
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Ustawienia")
        rozmiar = st.radio("Rozmiar", ["1:1", "3:4", "4:3", "9:16"], horizontal=True)
        styl = st.selectbox("Styl", ["Domyślny", "Anime", "Lego", "Zawiły", "Kawaii", "Chibi"])
        prompt = st.text_area("Opisz swoją kolorowankę (np. 'Cute cat on the moon')")
        generuj = st.button("GENERUJ KOLOROWANKĘ")

    with col2:
        if generuj and prompt:
            with st.spinner("AI tworzy i ulepsza jakość..."):
                try:
                    res = fal_client.subscribe("fal-ai/fast-lightning-sdxl", arguments={
                        "prompt": f"bold outlines, white background, coloring page, {prompt}, {styl} style, high contrast",
                        "image_size": "square_hd" if rozmiar == "1:1" else "portrait_4_3"
                    })
                    img_url = res['images'][0]['url']
                    resp = requests.get(img_url)
                    img = Image.open(BytesIO(resp.content))
                    st.image(img, use_column_width=True)
                    buf = BytesIO()
                    img.save(buf, format="PNG")
                    st.download_button("📥 Pobierz do druku KDP", buf.getvalue(), "kolorowanka.png")
                except Exception as e:
                    st.error(f"Błąd: {e}")
else:
    st.subheader("Zamień zdjęcie na szkic")
    file = st.file_uploader("Wgraj zdjęcie", type=["jpg", "png"])
    if file:
        st.image(file, width=300)
        if st.button("Konwertuj na kolorowankę"):
            st.info("Przetwarzanie zdjęcia przez AI...")
