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

os.environ["FAL_KEY"] = "cf0a6c98-7933-45df-918d-5757b24e9a30:afc267a3e94340879464bbea2862b40b"

st.set_page_config(page_title="SketchForge Master", layout="centered")

STYLES_DATA = [
    {"name": "Line Art", "icon": "🎨", "val": "clean line art"},
    {"name": "Zentangle", "icon": "🌸", "val": "zentangle patterns"},
    {"name": "Comic", "icon": "🗯️", "val": "comic book outlines"},
    {"name": "Mandala", "icon": "☸️", "val": "geometric mandala"},
    {"name": "Storybook", "icon": "📖", "val": "storybook illustration"},
]

KDP_TRENDS = {
    "Mandala dla dorosłych": [
        "ocean mandala patterns",
        "botanical mandala symmetry",
        "sacred geometry patterns",
    ],
    "Kawaii dla dzieci": [
        "cute animals with balloons",
        "kawaii food friends",
        "happy farm animals coloring page",
    ],
    "Fantasy i smoki": [
        "friendly dragon in castle",
        "wizard forest adventure",
        "magical creatures line art",
    ],
}


@st.cache_resource
def get_translator():
    return GoogleTranslator(source="pl", target="en")


translator = get_translator()


def master_generate(prompt, styl, mode="bw", seed=None, audience="Dzieci", consistency_context=None):
    try:
        quality = "ultra clean outlines, no shading, no gradients, no fill color, white background, black contour lines, print quality"
        consistency = f"consistent character and composition with {consistency_context}," if consistency_context else ""
        complexity = (
            "very simple large shapes thick outlines for kids"
            if audience == "Dzieci"
            else "intricate detailed contour drawing for adults"
        )

        if mode == "cover":
            final_p = f"{consistency} coloring book cover, {prompt}, {styl}, {quality}, {complexity}"
        else:
            final_p = f"{consistency} coloring page, {prompt}, {styl}, {quality}, {complexity}"

        result = fal_client.run(
            "fal-ai/flux/dev",
            arguments={
                "prompt": final_p,
                "seed": seed if seed is not None else random.randint(1, 99999999),
                "num_inference_steps": 35,
                "guidance_scale": 4.0,
                "width": 1024,
                "height": 1024,
            },
        )

        if not result or "images" not in result:
            return None

        url = result["images"][0]["url"]
        img = Image.open(BytesIO(requests.get(url, timeout=60).content)).convert("RGB")

        if mode == "bw":
            return to_contour_bw(img)
        return img
    except Exception as e:
        st.error(f"Błąd Silnika: {e}")
        return None


def to_contour_bw(image: Image.Image) -> Image.Image:
    gray = image.convert("L")
    edges = gray.filter(ImageFilter.FIND_EDGES)
    edges = ImageOps.autocontrast(edges, cutoff=2)
    line = edges.point(lambda p: 0 if p > 24 else 255).convert("L")
    line = line.filter(ImageFilter.MinFilter(3))
    line = line.point(lambda p: 0 if p < 128 else 255).convert("L")
    return line.convert("RGB")


def strict_bw_validation(image: Image.Image) -> bool:
    bw = image.convert("L").point(lambda p: 0 if p < 128 else 255)
    hist = bw.histogram()
    return sum(hist[1:255]) == 0


def png_300dpi_bytes(image: Image.Image) -> bytes:
    out = BytesIO()
    image.save(out, format="PNG", dpi=(300, 300), optimize=True)
    return out.getvalue()


def bitmap_to_svg_bytes(image: Image.Image) -> bytes:
    bw = image.convert("1")
    width, height = bw.size
    pix = bw.load()
    rects = []

    for y in range(height):
        x = 0
        while x < width:
            while x < width and pix[x, y] != 0:
                x += 1
            start = x
            while x < width and pix[x, y] == 0:
                x += 1
            if start < x:
                rects.append((start, y, x - start))

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#FFFFFF"/>',
    ]
    for x, y, w in rects:
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="1" fill="#000000"/>')
    parts.append("</svg>")
    return "".join(parts).encode("utf-8")


def convert_all_in_basket_to_contours():
    transformed = []
    for i, data in enumerate(st.session_state["pdf_basket"], start=1):
        src = Image.open(BytesIO(data)).convert("RGB")
        contour = to_contour_bw(src)
        png_bytes = png_300dpi_bytes(contour)
        svg_bytes = bitmap_to_svg_bytes(contour)
        valid = strict_bw_validation(contour)
        transformed.append(
            {
                "name": f"kolorowanka_{i:03d}",
                "image": contour,
                "png": png_bytes,
                "svg": svg_bytes,
                "valid": valid,
            }
        )
    st.session_state["transformed_assets"] = transformed


def transformed_zip_bytes():
    out = BytesIO()
    with zipfile.ZipFile(out, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for item in st.session_state.get("transformed_assets", []):
            zf.writestr(f"{item['name']}.png", item["png"])
            zf.writestr(f"{item['name']}.svg", item["svg"])
    return out.getvalue()


def export_pdf_from_pngs(items):
    bleed = 0.125 * inch
    pdf_w, pdf_h = 8.5 * inch + bleed, 11 * inch + bleed
    out = BytesIO()
    c = canvas.Canvas(out, pagesize=(pdf_w, pdf_h))
    for item in items:
        ir = ImageReader(BytesIO(item["png"]))
        c.drawImage(ir, 0, 0, width=pdf_w, height=pdf_h, preserveAspectRatio=True)
        c.showPage()
    c.save()
    return out.getvalue()


if "pdf_basket" not in st.session_state:
    st.session_state["pdf_basket"] = []
if "auth" not in st.session_state:
    st.session_state["auth"] = False
if "wybrany_styl" not in st.session_state:
    st.session_state["wybrany_styl"] = STYLES_DATA[0]["name"]
if "ai_hint" not in st.session_state:
    st.session_state["ai_hint"] = ""
if "audience" not in st.session_state:
    st.session_state["audience"] = "Dzieci"
if "transformed_assets" not in st.session_state:
    st.session_state["transformed_assets"] = []


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
                st.error("Błędne dane")
    st.stop()

with st.sidebar:
    st.title("🛡️ KDP MASTER PANEL")
    tryb = st.radio(
        "WYBIERZ NARZĘDZIE:",
        [
            "🎨 Generator",
            "📚 Seria z Historią",
            "🔍 Nisze & Trendy",
            "🌈 Bajka Personalizowana",
            "🧪 Konwersja BW Kontur",
        ],
    )
    st.divider()
    st.info("Zgodność: 300 DPI / KDP Ready")
    if st.button("🗑️ WYCZYŚĆ PROJEKT"):
        st.session_state["pdf_basket"] = []
        st.session_state["transformed_assets"] = []
        st.rerun()

st.markdown(
    """
    <div style='display:flex;justify-content:space-between;align-items:center;padding-bottom:16px;'>
      <span style='font-size:24px;font-weight:700;color:#2E7D32;'>🖋️ SketchForge Master</span>
      <span style='background:#E8F5E9;padding:4px 12px;border-radius:16px;color:#2E7D32;'>PRO QUALITY</span>
    </div>
    """,
    unsafe_allow_html=True,
)

if tryb == "🎨 Generator":
    c1, c2 = st.columns(2)
    with c1:
        st.session_state["audience"] = st.segmented_control(
            "Dla kogo", ["Dzieci", "Dorośli"], default=st.session_state["audience"]
        )
    with c2:
        mode = st.radio("Tryb", ["BW", "KOLOR"], horizontal=True)

    prompt_input = st.text_area("Opis ilustracji", value=st.session_state["ai_hint"], height=90)

    t1, t2 = st.columns(2)
    with t1:
        if st.button("🔄 Tłumacz na ENG", use_container_width=True) and prompt_input:
            st.session_state["ai_hint"] = translator.translate(prompt_input)
            st.rerun()
    with t2:
        if st.button("✨ Podpowiedz", use_container_width=True):
            st.session_state["ai_hint"] = random.choice(
                ["friendly dragon", "forest mandala", "space cat", "castle adventure"]
            )
            st.rerun()

    st.write("**Styl**")
    cols = st.columns(len(STYLES_DATA))
    for i, s in enumerate(STYLES_DATA):
        with cols[i]:
            selected = st.session_state["wybrany_styl"] == s["name"]
            if st.button(
                f"{s['icon']}\n{s['name']}",
                key=f"style_{s['name']}",
                use_container_width=True,
                type="primary" if selected else "secondary",
            ):
                st.session_state["wybrany_styl"] = s["name"]
                st.rerun()

    amount = st.number_input("Ilość grafik", 1, 30, 1)
    if st.button("🚀 Generuj", type="primary", use_container_width=True):
        if not prompt_input:
            st.warning("Wpisz opis")
        else:
            style_val = next(
                (s["val"] for s in STYLES_DATA if s["name"] == st.session_state["wybrany_styl"]),
                "clean line art",
            )
            out_cols = st.columns(2)
            eng = translator.translate(prompt_input)
            for i in range(amount):
                img = master_generate(
                    eng,
                    style_val,
                    mode="bw" if mode == "BW" else "color",
                    audience=st.session_state["audience"],
                )
                if img:
                    out_cols[i % 2].image(img, use_container_width=True)
                    buf = BytesIO()
                    img.save(buf, format="PNG")
                    st.session_state["pdf_basket"].append(buf.getvalue())
            st.success("Dodano do projektu")

elif tryb == "📚 Seria z Historią":
    temat = st.text_input("Temat serii")
    fabula = st.text_area("Fabuła")
    ile = st.select_slider("Liczba stron", [5, 10, 15, 20])
    if st.button("🚀 Generuj serię", type="primary", use_container_width=True):
        if temat and fabula:
            eng_topic = translator.translate(temat)
            eng_story = translator.translate(fabula)
            cover = master_generate(
                f"book cover for {eng_topic}",
                "storybook illustration",
                mode="cover",
                audience=st.session_state["audience"],
            )
            if cover:
                b = BytesIO()
                cover.save(b, format="PNG")
                st.session_state["pdf_basket"].append(b.getvalue())
            prog = st.progress(0)
            for i in range(ile):
                img = master_generate(
                    f"scene {i+1} of {eng_topic}: {eng_story}",
                    "clean line art",
                    mode="bw",
                    audience=st.session_state["audience"],
                    consistency_context=eng_topic,
                )
                if img:
                    b = BytesIO()
                    img.save(b, format="PNG")
                    st.session_state["pdf_basket"].append(b.getvalue())
                prog.progress((i + 1) / ile)
            st.success("Seria gotowa")

elif tryb == "🔍 Nisze & Trendy":
    st.subheader("Trendy KDP")
    for niche, prompts in KDP_TRENDS.items():
        with st.expander(f"🔥 {niche}"):
            for p in prompts:
                if st.button(f"Użyj: {p}", key=f"niche_{niche}_{p}"):
                    st.session_state["ai_hint"] = p
                    st.success("Podpowiedź ustawiona")

elif tryb == "🌈 Bajka Personalizowana":
    imie = st.text_input("Imię dziecka")
    opis = st.text_area("Opis przygody")
    if st.button("✨ Generuj ilustrację", type="primary") and imie and opis:
        prompt = translator.translate(f"storybook about {imie}: {opis}")
        img = master_generate(prompt, "storybook illustration", mode="color", audience="Dzieci")
        if img:
            st.image(img, use_container_width=True)
            b = BytesIO()
            img.save(b, format="PNG")
            st.session_state["pdf_basket"].append(b.getvalue())

elif tryb == "🧪 Konwersja BW Kontur":
    st.subheader("Konwersja wszystkich kolorowanek do konturów BW")
    st.write(f"W koszyku: {len(st.session_state['pdf_basket'])} grafik")
    if st.button("🧪 Konwertuj wszystko", type="primary", use_container_width=True):
        if not st.session_state["pdf_basket"]:
            st.warning("Koszyk jest pusty")
        else:
            convert_all_in_basket_to_contours()
            valid_count = sum(1 for x in st.session_state["transformed_assets"] if x["valid"])
            total = len(st.session_state["transformed_assets"])
            st.success(f"Gotowe: {total} plików. Walidacja BW: {valid_count}/{total}")

    if st.session_state["transformed_assets"]:
        preview_cols = st.columns(2)
        for i, item in enumerate(st.session_state["transformed_assets"][:6]):
            preview_cols[i % 2].image(item["image"], caption=f"{item['name']} | BW OK: {item['valid']}")

        zip_bytes = transformed_zip_bytes()
        st.download_button(
            "📦 Pobierz ZIP (SVG + PNG 300 DPI)",
            zip_bytes,
            file_name="kontury_bw_svg_png.zip",
            mime="application/zip",
            use_container_width=True,
        )

        pdf_bytes = export_pdf_from_pngs(st.session_state["transformed_assets"])
        st.download_button(
            "📥 Pobierz PDF KDP z konturów",
            pdf_bytes,
            file_name="kontury_bw_kdp.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

if st.session_state["pdf_basket"]:
    with st.sidebar:
        st.divider()
        st.write(f"📄 Stron w projekcie: {len(st.session_state['pdf_basket'])}")
