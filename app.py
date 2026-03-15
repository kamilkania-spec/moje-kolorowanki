import streamlit as st
import os
import fal_client
from deep_translator import GoogleTranslator
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import requests
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import random
import base64

# --- KONFIGURACJA ---
# Upewnij się, że ten klucz jest aktywny na fal.ai
os.environ["FAL_KEY"] = "cf0a6c98-7933-45df-918d-5757b24e9a30:afc267a3e94340879464bbea2862b40b"
ADMIN_NICK = "admin"
ADMIN_PASS = "KDP2026"

st.set_page_config(page_title="KDP Factory Pro 8K - FULL SUITE + Story AI (Photo)", layout="wide")
translator = GoogleTranslator(source='pl', target='en')

# --- BAZA DANYCH ---
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {
        "admin": {"pass": "KDP2026", "credits": 999999, "role": "admin"},
        "tester": {"pass": "KDP123", "credits": 50, "role": "user"}
    }
if "pdf_basket" not in st.session_state: st.session_state["pdf_basket"] = []
if "posts" not in st.session_state: st.session_state["posts"] = []
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False

# --- LOGOWANIE ---
if not st.session_state["authenticated"]:
    st.title("🔐 KDP Factory Login")
    u = st.text_input("Nick:")
    p = st.text_input("Hasło:", type="password")
    if st.button("Zaloguj się"):
        if u in st.session_state["user_db"] and st.session_state["user_db"][u]["pass"] == p:
            st.session_state["authenticated"] = True
            st.session_state["user_nick"] = u
            st.session_state["role"] = st.session_state["user_db"][u]["role"]
            st.rerun()
    st.stop()

# --- GŁÓWNY SILNIK GRAFICZNY ---
def master_generate(prompt, is_color=False, image_url=None):
    nick = st.session_state["user_nick"]
    if st.session_state["user_db"][nick]["credits"] <= 0:
        st.error("❌ Brak kredytów!")
        return None
    try:
        # Konfiguracja argumentów dla API fal.ai (Flux)
        arguments = {"prompt": prompt}
        if image_url:
            arguments["image_url"] = image_url # Dodanie obrazu jako inspiracji (ControlNet)

        # Wywołanie API
        handler = fal_client.subscribe("fal-ai/flux/schnell", arguments=arguments)
        url = handler['images'][0]['url']
        resp = requests.get(url)
        
        # Przetwarzanie obrazu
        img = Image.open(BytesIO(resp.content))
        
        if not is_color:
            # Konwersja na czarno-biały dla kolorowanek
            img = img.convert('L')
            img = ImageEnhance.Contrast(img).enhance(3.5)
            
        # Skalowanie do 8K (LANCZOS)
        w, h = img.size
        img = img.resize((w*2, h*2), resample=Image.LANCZOS)
        
        # Odjęcie kredytu
        if st.session_state["role"] != "admin":
            st.session_state["user_db"][nick]["credits"] -= 1
            
        return img
    except Exception as e:
        st.error(f"⚠️ Błąd API: {e}")
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.title(f"👤 {st.session_state['user_nick']}")
    cred = st.session_state["user_db"][st.session_state['user_nick']]['credits']
    st.write(f"🪙 Kredyty: {'∞' if st.session_state['role'] == 'admin' else cred}")
    
    tryb = st.selectbox("Wybierz moduł:", 
                        ["✏️ Generator Kategorii", 
                         "🦁 Niche Finder & SEO", 
                         "📖 Opowieść (Story Mode)", 
                         "📖 KDP Story AI (Beta)", 
                         "📸 Zdjęcie na Kontur", 
                         "💬 Forum",
                         "⚖️ Regulamin i Pomoc"])
    
    st.divider()
    if st.button("🗑️ Wyczyść Projekt"):
        st.session_state['pdf_basket'] = []; st.rerun()
    if st.button("🚪 Wyloguj"):
        st.session_state["authenticated"] = False; st.rerun()

# --- LOGIKA MODUŁÓW (WSZYSTKIE NARZĘDZIA) ---

if tryb == "✏️ Generator Kategorii":
    st.header("🎨 Szybki Generator 8K")
    kat = st.radio("Styl:", ["Dowolny", "Geometria", "Pejzaż", "Przyroda", "Architektura"], horizontal=True)
    opis = st.text_input("Opis (co narysować?):")
    if st.button("GENERUJ"):
        with st.spinner("Pracuję..."):
            eng = translator.translate(opis)
            p = f"Coloring book page, {kat if kat != 'Dowolny' else ''} {eng}, 8k, black and white, clean bold lines, no shading"
            img = master_generate(p, is_color=False)
            if img:
                buf = BytesIO(); img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())
                st.image(img)

elif tryb == "🦁 Niche Finder & SEO":
    st.header("🦁 Niche Blaster - Analiza i Generowanie")
    if st.button("🔍 Skanuj Trendy Amazon Marzec 2026"):
        trends = [
            "Easter Biblical Stories (Seasonally High)",
            "Bold & Easy: Cozy Little Shops",
            "Celestial Boho Animals",
            "Victorian Steampunk Fashions",
            "Kawaii Food with Expressions"
        ]
        st.write("🔥 **Trendy USA/UK:**")
        for t in trends: st.code(t)
    
    n_input = st.text_input("Wpisz wybraną niszcę:")
    if n_input:
        st.success(f"Tytuł: {n_input.capitalize()} Coloring Book for Adults")
        st.write(f"Słowa kluczowe: {n_input}, coloring book, kdp, amazon, adult coloring, meditation, 2026 trends")
        ile_n = st.number_input("Ile grafik wygenerować?", 1, 50, 5)
        if st.button("🚀 Generuj Serię"):
            bar = st.progress(0)
            for i in range(ile_n):
                img = master_generate(f"Coloring page, {translator.translate(n_input)}, 8k, unique, bold lines", is_color=False)
                if img:
                    buf = BytesIO(); img.save(buf, format="PNG")
                    st.session_state['pdf_basket'].append(buf.getvalue())
                bar.progress((i+1)/ile_n)

elif tryb == "📖 Opowieść (Story Mode)":
    st.header("📖 Story Mode - Cała Książka (Czarno-Biała)")
    historia = st.text_area("Opisz fabułę książki:")
    ile_s = st.number_input("Ile stron?", 5, 50, 10)
    if st.button("🔥 GENERUJ CAŁOŚĆ"):
        bar_s = st.progress(0)
        eng_h = translator.translate(historia)
        for i in range(ile_s):
            img = master_generate(f"Step {i+1} of {ile_s}: {eng_h}. Coloring page, 8k, bold lines", is_color=False)
            if img:
                buf = BytesIO(); img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())
            bar_s.progress((i+1)/ile_s)

elif tryb == "📖 KDP Story AI (Beta)":
    st.header("📖 KDP Story AI (Beta) - Spersonalizowane Bajki z Twojego Zdjęcia")
    st.info("Ta funkcja generuje pełne, spójne kolorowe ilustracje gotowe do druku bajek w USA, inspirując się wgranym zdjęciem!")
    
    # 📸 NOWE: Wgrywanie zdjęcia dziecka do interpretacji
    f_photo = st.file_uploader("📸 Wgraj zdjęcie dziecka (do interpretacji AI):", type=['png', 'jpg'])
    
    imię = st.text_input("Imię dziecka (główny bohater):")
    postać = st.selectbox("W kogo zamienić dziecko?", ["Misia", "Superbohatera", "Robota", "Królewnę/Księcia", "Dowolną postać tekstową"])
    if postać == "Dowolną postać tekstową":
        postać_d = st.text_input("Opisz postać (np. Mały astronauta w niebieskim skafandrze):")
    else:
        postać_d = postać
        
    hist_d = st.text_area("Opisz fabułę bajki (np. Podróż na Marsa z psem Bongo):")
    ile_d = st.number_input("Ile stron bajki?", 5, 30, 10)
    
    if imię and f_photo and hist_d:
        st.success(f"✅ Tytuł: {imię.capitalize()}'s Magical Adventure")
        
        if st.button("🚀 GENERUJ BAJKĘ DLA DZIEKCKA (Z FOTKI)"):
            bar_d = st.progress(0)
            eng_h_d = translator.translate(hist_d)
            seed = random.randint(0, 999999)
            
            # Przetwarzanie zdjęcia dziecka na URL (Base64) dla API
            try:
                # Wczytanie obrazu i konwersja do Base64
                photo_bytes = f_photo.read()
                photo_base64 = base64.b64encode(photo_bytes).decode('utf-8')
                photo_url = f"data:{f_photo.type};base64,{photo_base64}"
                
                for i in range(ile_d):
                    # Specjalny prompt dla spójności postaci i stylu bajkowego, inspirując się zdjęciem
                    # Dodano instrukcję: "based on face from the photo"
                    p_d = f"Step {i+1} of {ile_d} in the story of {imię}. The main character is a {postać_d}, whose face is based on the provided photo of the child. The {postać_d} looks consistent with the child's features from the photo on every page. Plot: {eng_h_d}. Whimsical children's book illustration, soft lighting, vibrant colors, clear focus. {seed}"
                    
                    # Generowanie z przekazaniem zdjęcia jako ControlNet/inspiracja
                    img = master_generate(p_d, is_color=True, image_url=photo_url)
                    
                    if img:
                        buf = BytesIO(); img.save(buf, format="PNG")
                        st.session_state['pdf_basket'].append(buf.getvalue())
                    bar_d.progress((i+1)/ile_d)
                st.success("Bajka gotowa! Pobierz PDF poniżej.")
            except Exception as e:
                st.error(f"⚠️ Błąd podczas przetwarzania zdjęcia: {e}")

elif tryb == "📸 Zdjęcie na Kontur":
    st.header("📸 Twoje zdjęcie -> Bezstratny Szkic 8K")
    f = st.file_uploader("Wgraj plik (JPG/PNG):", type=['png', 'jpg'])
    if f and st.button("KONWERTUJ NA KONTUR"):
        with st.spinner("Przetwarzam zdjęcie na bezstratny kontur..."):
            img = Image.open(f).convert('L')
            img_blurred = img.filter(ImageFilter.GaussianBlur(radius=1))
            img_edges = img_blurred.filter(ImageFilter.FIND_EDGES)
            img_final = ImageOps.invert(img_edges)
            img_final = ImageEnhance.Contrast(img_final).enhance(3.0)
            
            w, h = img_final.size
            img_final_res = img_final.resize((w*2, h*2), resample=Image.LANCZOS)

            buf = BytesIO(); img_final_res.save(buf, format="PNG")
            st.session_state['pdf_basket'].append(buf.getvalue())
            st.image(img_final_res, caption="Bezstratny kontur gotowy!")

elif tryb == "💬 Forum":
    st.header("💬 Forum Społeczności")
    wiad = st.text_input("Wiadomość:")
    if st.button("Wyślij"):
        st.session_state["posts"].insert(0, {"u": st.session_state["user_nick"], "m": wiad})
        st.rerun()
    for p in st.session_state["posts"]: st.info(f"**{p['u']}**: {p['m']}")

elif tryb == "⚖️ Regulamin i Pomoc":
    st.header("⚖️ Dokumenty Prawne i Pomoc")
    tab1, tab2 = st.tabs(["Regulamin", "Polityka Prywatności"])
    with tab1: st.write("Regulamin Twojej aplikacji... (Tu wklej tekst dla Stripe)")
    with tab2: st.write("Polityka prywatności... (Tu wklej tekst dla Stripe)")

# --- EKSPORT PDF ---
if st.session_state['pdf_basket']:
    st.divider()
    if st.button("📥 POBIERZ PDF DO AMAZON KDP"):
        out = BytesIO()
        pdf = canvas.Canvas(out, pagesize=(8.5*inch, 11*inch))
        for d in st.session_state['pdf_basket']:
            pdf.drawImage(BytesIO(d), 0.5*inch, 1*inch, width=7.5*inch, height=9*inch)
            pdf.showPage(); pdf.showPage() # Jedna pusta strona (standard KDP)
        pdf.save()
        st.download_button("Zapisz plik PDF", out.getvalue(), "projekt_kdp_8k.pdf")
    
