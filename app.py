# --- STYLE CSS (Dodaj na początku, aby upiększyć przyciski) ---
st.markdown("""
    <style>
    .style-card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 10px;
        text-align: center;
        background-color: #f9f9f9;
    }
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        background-color: #e91e63;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# --- GŁÓWNY PANEL GENERATORA ---
st.header("🎨 iColoring 2.0 Pro")

# 1. Pole tekstowe z tłumaczem
prompt_pl = st.text_area("Wpisz swój pomysł (np. Kotek w kosmosie):", placeholder="Opisz swój pomysł...")
if st.button("🌐 Tłumacz na angielski"):
    eng_prompt = translator.translate(prompt_pl)
    st.info(f"Przetłumaczono: {eng_prompt}")

# 2. Wybór Stylu (Kafelki)
st.write("### Wybierz Styl")
kolumny_stylu = st.columns(4)

style_opcje = {
    "Domyślny": "detailed coloring book page, clean lines",
    "Rysunek": "simple child drawing style, thick outlines",
    "Anime": "manga style coloring page, sharp lines",
    "Mandala": "intricate mandala patterns, symmetrical",
    "Kawaii": "cute chibi style, simple shapes",
    "Geometria": "geometric abstract patterns, 8k",
    "Science-fiction": "futuristic coloring page, tech details",
    "Przyroda": "nature and forest landscapes, realistic lines"
}

wybrany_styl_klucz = "Domyślny"
# Tworzymy siatkę kafelków (na razie jako radio, ale w ładnym układzie)
wybrany_styl_klucz = st.radio("Style:", list(style_opcje.keys()), horizontal=True)

# 3. Rozmiar i Ilość
st.write("### Ustawienia")
col_res, col_num = st.columns([2, 1])

with col_res:
    rozmiar = st.select_slider("Rozmiar (Proporcje):", options=["1:1", "3:4", "4:3", "9:16"])

with col_num:
    ilosc = st.number_input("Utwórz ilość:", min_value=1, max_value=50, value=1)

# --- PRZYCISK GŁÓWNY (Spowodować / Generuj) ---
if st.button("✨ SPOWODOWAĆ (Generuj)", use_container_width=True):
    with st.spinner("Pracuję nad Twoją kolorowanką..."):
        # Logika pętli z poprzedniego kodu
        for i in range(ilosc):
            final_prompt = f"{style_opcje[wybrany_styl_klucz]}, {prompt_pl}, white background, black and white"
            img = master_generate(final_prompt)
            
            if img:
                # Wyświetlanie w ładnym gridzie
                st.image(img, caption=f"Wynik {i+1}")
                # Zapis do koszyka PDF (jak w poprzednim kodzie)
                buf = BytesIO()
                img.save(buf, format="PNG")
                st.session_state['pdf_basket'].append(buf.getvalue())

# --- DÓŁ STRONY (Stopka PDF) ---
if st.session_state['pdf_basket']:
    st.divider()
    st.write(f"📦 Masz {len(st.session_state['pdf_basket'])} grafik w projekcie.")
    if st.button("📥 POBIERZ GOTOWY PDF DO AMAZON KDP"):
        # Tutaj wywołaj Twoją funkcję generowania PDF z IMG_2100.jpg
        st.write("Generuję plik...")
