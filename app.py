import streamlit as st
import os
import fal_client
from deep_translator import GoogleTranslator
from PIL import Image, ImageEnhance
import requests
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import random

# --- KONFIGURACJA KLUCZY I ŚRODOWISKA ---
# Pamiętaj, aby trzymać klucz bezpiecznie!
os.environ["FAL_KEY"] = "cf0a6c98-7933-45df-918d-5757b24e9a30:afc267a3e94340879464bbea2862b40b"

st.set_page_config(page_title="KDP Factory Pro 8K", layout="wide", page_icon="🎨")
translator = GoogleTranslator(source='pl', target='en')

# --- INICJALIZACJA SESJI (PAMIĘĆ APLIKACJI) ---
if "pdf_basket" not in st.session_state: 
    st.session_state["pdf_basket"] = []
if "authenticated" not in st.session_state: 
    st.session_state["authenticated"] = False
if "p_magic" not in st.session_state:
    st.session_state["p_magic"] = ""

# --- RDZEŃ GENERUJĄCY (SILNIK) ---
def master_generate(prompt, is_color=False, image_url=None, is_cover=False):
    """Główna funkcja generująca grafiki - dba o brak tandety i wysoką jakość."""
    try:
        # Budowanie potężnego promptu technicznego
        if is_cover:
            quality_suffix = ", professional book cover, vivid cinematic colors, award winning illustration, 8k, masterpiece, centered composition"
        elif not is_color:
            quality_suffix = ", coloring book page, clean bold black outlines, pure white background, no shading, no background noise, high contrast, vector style, 8k"
        else:
            quality_suffix = ", children's storybook style, soft dreamy lighting, vibrant colors, highly detailed, 8k, whimsical"
        
        full_prompt = prompt + quality_suffix
        
        # Ustawienie rozmiaru (Okładka kwadratowa, wnętrze portretowe pod KDP)
        size = "square" if is_cover else "portrait_4_5"
        
        arguments = {
            "prompt": full_prompt,
            "image_size": size,
            "seed": random.randint(1, 99999999) # To zapewnia UNIKALNOŚĆ każdej grafiki w serii
        }
        
        if image_url:
            arguments["image_url"] = image_url # Przekazanie zdjęcia dziecka do AI
            
        handler = fal_client.subscribe("fal-ai/flux/schnell", arguments=arguments)
        url = handler['images'][0]['url']
        resp = requests.get(url)
        img = Image.open(BytesIO(resp.content))

        # Post-processing dla kolorowanek (żeby były idealnie czarno-białe)
        if not is_color and not is_cover:
            img = img.convert('L') # Skala szarości
            img = ImageEnhance.Contrast(img).enhance(4.5) # Agresywne podbicie czerni linii
        
        return img
    except Exception as e:
        st.error(f"⚠️ Błąd silnika AI: {e}")
        return None

# --- LOGOWANIE ---
if not st.session_state["authenticated"]:
    st.title("🔐 System Produkcji KDP - Logowanie")
    col_l, col_r = st.columns(2)
    with col_l:
        u = st.text_input("Użytkownik:")
        p = st.text_input("Hasło:", type="password")
        if st.button("Zaloguj do systemu"):
            if u == "admin" and p == "KDP2026":
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Błędne dane!")
    st.stop()

# --- PANEL BOCZNY (NAWIGACJA) ---
with st.sidebar:
    st.title("🚀 KDP Factory Pro")
    st.info(f"W koszyku: {len(st.session_state['pdf_basket'])} stron")
    
    tryb = st.radio("WYBIERZ NARZĘDZIE:", [
        "🎨 Kolorowanki (Seria/Single)", 
        "📖 Bajka z Dzieckiem (Personalizacja)", 
        "🖼️ Generator Okładek",
        "📦 Export do PDF (KDP Ready)"
    ])
    
    st.divider()
    if st.button("🗑️ Wyczyść cały projekt"):
        st.session_state['pdf_basket'] = []
        st.success("Projekt wyczyszczony!")
    
    if st.button("🚪 Wyloguj"):
        st.session_state["authenticated"] = False
        st.rerun()

# --- MODUŁ 1: KOLOROWANKI ---
if tryb == "🎨 Kolorowanki (Seria/Single)":
    st.header("🎨 Kreator Kolorowanek Premium")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        styl = st.selectbox("Wybierz styl:", ["Mandala dla dorosłych", "Architektura", "Zwierzęta", "Przyroda", "Własny pomysł"])
        user_input = st.text_area("O czym ma być grafika? (wpisz po polsku):", placeholder="np. smok w jaskini, stare miasto w nocy...")
        
        if st.button("🪄 Użyj Magicznej Pałeczki"):
            if user_input:
                # Tłumaczenie i wzbogacanie promptu
                translated = translator.translate(user_input)
                templates = {
                    "Mandala dla dorosłych": f"complex sacred geometry mandala of {translated}, intricate patterns, symmetrical, fine ink lines",
                    "Architektura": f"highly detailed architectural sketch of {translated}, sharp clean lines, victorian style, professional perspective",
                    "Zwierzęta": f"ornate zentangle portrait of {translated}, majestic animal with patterns, bold black outlines",
                    "Przyroda": f"botanical nature scene with {translated}, woodcut style, organic intricate lines",
                    "Własny pomysł": translated
                }
                st.session_state["p_magic"] = templates.get(styl, translated)
                st.success("✨ Magiczna pałeczka przygotowała prompt!")
            else:
                st.warning("Wpisz najpierw swój pomysł!")

    with col2:
        ile = st.number_input("Ile różnych sztuk wygenerować?", 1, 50, 1)
        final_prompt = st.text_area("Podgląd promptu AI (możesz edytować):", value=st.session_state.get("p_magic", ""), height=150)

    if st.button("🚀 GENERUJ PROJEKT"):
        if not final_prompt and user_input:
            final_prompt = translator.translate(user_input)
            
        bar = st.progress(0)
        for i in range(ile):
            with st.spinner(f"Tworzenie unikalnej strony {i+1} z {ile}..."):
                img = master_generate(final_prompt, is_color=False)
                if img:
                    buf = BytesIO()
                    img.save(buf, format="PNG")
                    st.session_state['pdf_basket'].append(buf.getvalue())
                    st.image(img, width=350, caption=f"Strona dodana do koszyka")
            bar.progress((i + 1) / ile)
        st.balloons()

# --- MODUŁ 2: BAJKA Z DZIECKIEM ---
elif tryb == "📖 Bajka z Dzieckiem (Personalizacja)":
    st.header("📖 Bajka: Moje Dziecko jako Bohater")
    st.write("Wgraj zdjęcie dziecka, a AI stworzy spójną bajkę z jego cechami!")
    
    f_photo = st.file_uploader("Zdjęcie twarzy dziecka:", type=['png', 'jpg', 'jpeg'])
    c1, c2 = st.columns(2)
    with c1:
        imie_dziecka = st.text_input("Imię dziecka:")
        postać = st.selectbox("Bohater bajki:", ["Mały Miś", "Dzielny Rycerz", "Kosmiczny Odkrywca", "Leśna Wróżka"])
    with c2:
        liczba_stron = st.slider("Długość bajki (strony):", 3, 10, 5)

    if f_photo and imie_dziecka and st.button("✨ STWÓRZ TĘ BAJKĘ"):
        # Upload zdjęcia do serwera fal
        photo_url = fal_client.upload_image(f_photo.getvalue())
        
        bar_b = st.progress(0)
        for i in range(liczba_stron):
            # Tworzenie sceny bajki
            scene_p = f"Children's book illustration, {imie_dziecka} as a {postać} having an adventure, page {i+1}, face consistent with uploaded photo, whimsical, vibrant"
            img = master_generate(scene_p, is_color=True, image_url=photo_url)
            if img:
                buf = BytesIO()
                img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())
                st.image(img, width=400, caption=f"Strona {i+1}")
            bar_b.progress((i + 1) / liczba_stron)
        st.success("Bajka została dopisana do Twojego aktualnego projektu!")

# --- MODUŁ 3: OKŁADKA ---
elif tryb == "🖼️ Generator Okładek":
    st.header("🖼️ Profesjonalna Okładka do Książki")
    p_okl = st.text_input("Opisz wizję okładki (np. Magiczny las pełen mandal):")
    
    if st.button("🎨 Generuj Okładkę"):
        p_eng = translator.translate(p_okl)
        with st.spinner("Projektowanie okładki..."):
            img = master_generate(p_eng, is_color=True, is_cover=True)
            if img:
                st.image(img, width=500, caption="PROJEKT OKŁADKI")
                buf = BytesIO()
                img.save(buf, format="PNG")
                # Okładka ZAWSZE na początek pliku!
                st.session_state['pdf_basket'].insert(0, buf.getvalue())
                st.success("Okładka została wygenerowana i ustawiona jako 1. strona projektu!")

# --- MODUŁ 4: EKSPORT ---
elif tryb == "📦 Export do PDF (KDP Ready)":
    st.header("📦 Twój Gotowy Produkt Amazon KDP")
    st.write(f"Twój projekt ma obecnie: **{len(st.session_state['pdf_basket'])}** stron.")
    
    if st.session_state['pdf_basket']:
        if st.button("📥 GENERUJ I POBIERZ PLIK PDF (8.5x11 cala)"):
            out = BytesIO()
            # Standardowy rozmiar Amazon KDP (Letter)
            pdf = canvas.Canvas(out, pagesize=(8.5 * inch, 11 * inch))
            
            for i, data in enumerate(st.session_state['pdf_basket']):
                # Rysowanie grafiki z bezpiecznym marginesem (Safe Zone)
                pdf.drawImage(BytesIO(data), 0.75*inch, 1.5*inch, width=7*inch, height=8*inch, preserveAspectRatio=True)
                pdf.showPage() # Kończymy stronę z grafiką
                
                # Jeśli to nie jest okładka, dodajemy pustą stronę (żeby kredki nie przebijały)
                # Zakładamy, że okładka to strona 0
                if i > 0 or len(st.session_state['pdf_basket']) == 1:
                    pdf.showPage() 
            
            pdf.save()
            st.download_button(
                label="Kliknij tutaj, aby zapisać PDF na dysku",
                data=out.getvalue(),
                file_name="projekt_kdp_master.pdf",
                mime="application/pdf"
            )
    else:
        st.warning("Twój koszyk jest pusty. Wygeneruj najpierw jakieś grafiki!")
