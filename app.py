import streamlit as st
import os, fal_client, requests, random, base64
from deep_translator import GoogleTranslator
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

os.environ["FAL_KEY"] = "cf0a6c98-7933-45df-918d-5757b24e9a30:afc267a3e94340879464bbea2862b40b"
st.set_page_config(page_title="KDP Design Studio Pro", layout="wide")
translator = GoogleTranslator(source='pl', target='en')

if "pdf_basket" not in st.session_state: st.session_state["pdf_basket"] = []
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("✨ KDP Studio Login")
    u, p = st.text_input("Login:"), st.text_input("Hasło:", type="password")
    if st.button("Zaloguj"):
        if u == "admin" and p == "KDP2026":
            st.session_state["authenticated"] = True
            st.rerun()
    st.stop()

def master_generate(prompt, is_color=False, image_url=None, seed=None):
    try:
        current_seed = seed if seed is not None else random.randint(0, 10**9)
        clean_p = f"{prompt}, professional coloring book line art, clean black contours, white background, no gray, 8k"
        args = {"prompt": clean_p, "image_size": "square_hd", "seed": current_seed}
        if image_url: args["image_url"] = image_url
        res = fal_client.subscribe("fal-ai/flux/schnell", arguments=args)
        img = Image.open(BytesIO(requests.get(res['images'][0]['url']).content))
        if not is_color:
            img = img.convert('L')
            img = ImageEnhance.Contrast(img).enhance(3.0) 
            img = img.filter(ImageFilter.SHARPEN)
        return img.resize((img.size[0]*2, img.size[1]*2), Image.LANCZOS)
    except Exception as e:
        st.error(f"Błąd: {e}"); return None

with st.sidebar:
    st.title("🖌️ Menu")
    tryb = st.selectbox("Narzędzie:", ["🎨 Generator Kolekcji", "🦁 Niche Finder", "📖 Foto-Bajka AI", "📸 Kontur"])
    if st.button("🗑️ Wyczyść projekt"): st.session_state['pdf_basket'] = []; st.rerun()

if tryb == "🎨 Generator Kolekcji":
    st.header("🎨 Generator Kolekcji (Siatka iColoring)")
    c1, c2, c3 = st.columns(3)
    kat = c1.selectbox("Kategoria:", ["Natura", "Zwierzęta", "Mandale", "Architektura"])
    styl = c2.selectbox("Styl:", ["Fine", "Bold & Easy", "Zentangle"])
    ile = c3.slider("Liczba stron:", 1, 40, 20)
    temat = st.text_input("Temat (np. wilki w lesie):")
    if st.button("🔥 Generuj serię"):
        bar, status, grid = st.progress(0), st.empty(), st.columns(4)
        k_m = {"Natura": "nature", "Zwierzęta": "wildlife", "Mandale": "mandala", "Architektura": "architecture"}
        s_m = {"Fine": "detailed lines", "Bold & Easy": "bold thick lines", "Zentangle": "ornamental"}
        for i in range(ile):
            status.info(f"Strona {i+1}/{ile}...")
            p = f"{k_m[kat]}, {s_m[styl]}, {translator.translate(temat)}, variation {random.random()}"
            img = master_generate(p)
            if img:
                buf = BytesIO(); img.save(buf, format="PNG"); st.session_state['pdf_basket'].append(buf.getvalue())
                with grid[i % 4]: st.image(img, use_container_width=True)
            bar.progress((i+1)/ile)
        status.success("Kolekcja gotowa!")

elif tryb == "🦁 Niche Finder":
    if st.button("🔍 Skanuj rynek"): st.success("Trendy: Bold & Easy Hygge, Easter Gnomes")

elif tryb == "📖 Foto-Bajka AI":
    f = st.file_uploader("Zdjęcie:", type=['jpg', 'png'])
    if f and st.button("Generuj"):
        url = f"data:{f.type};base64,{base64.b64encode(f.read()).decode()}"
        img = master_generate("Consistent character coloring page", image_url=url)
        st.image(img)

if st.session_state['pdf_basket']:
    st.divider()
    if st.button("📥 POBIERZ PDF (8.5x11)"):
        out = BytesIO(); pdf = canvas.Canvas(out, pagesize=(8.5*inch, 11*inch))
        for d in st.session_state['pdf_basket']:
            pdf.drawImage(BytesIO(d), 0.75*inch, 1*inch, width=7*inch, height=9*inch)
            pdf.showPage(); pdf.showPage()
        pdf.save()
        st.download_button("💾 Zapisz PDF", out.getvalue(), "kdp_final.pdf")
