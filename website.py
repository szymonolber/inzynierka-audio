import streamlit as st
import os
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(
    page_title="Szymon Olber - 2027",
    layout="wide", # Używamy wide, żeby mieć kontrolę nad marginesami
    page_icon="▪️"
)

# --- 2. CSS - ESTETYKA "PAYSAGES" (ARTISTIC MINIMALISM) ---
st.markdown("""
<style>
    /* IMPORT CZCIONKI - Space Mono (Techniczna, ale elegancka) */
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400&display=swap');

    /* KOLORYSTYKA - Szałwia / Beż (Zgodnie ze zdjęciem 'paysages') */
    :root {
        --bg-color: #E6E8E3; /* Złamana szałwiowa biel */
        --text-color: #2F332E; /* Ciemna oliwka / Prawie czarny */
        --accent-color: #2F332E; 
    }

    /* GLOBALNY RESET */
    .stApp {
        background-color: var(--bg-color);
        color: var(--text-color);
        font-family: 'Space Mono', monospace;
    }

    /* UKRYCIE ELEMENTÓW SYSTEMOWYCH */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {
        padding-top: 3rem;
        padding-bottom: 5rem;
        max-width: 1200px;
    }
            
    /* UPLOADER - STYLIZACJA KONTENERA */
    [data-testid='stFileUploader'] {
        background-color: transparent;
        border: 1px dashed var(--text-color);
        padding: 40px;
        opacity: 0.9;
    }

    /* NAPRAWA KOLORU TEKSTU WEWNĄTRZ (BIAŁY) */
    [data-testid='stFileUploaderDropzone'] div,
    [data-testid='stFileUploaderDropzone'] span,
    [data-testid='stFileUploaderDropzone'] small,
    [data-testid='stFileUploaderDropzone'] p {
        color: white !important; /* Wymuszony biały dla napisów */
        -webkit-text-fill-color: white !important; /* Dla przeglądarek Webkit */
    }

    /* Ukrycie przycisku "Browse files" */
    [data-testid='stFileUploader'] button {
        display: none;
    }

    /* TYPOGRAFIA */
    h1, h2, h3, p, span, div, button, input, label {
        font-family: 'Space Mono', monospace !important;
        color: var(--text-color) !important;
        letter-spacing: -0.5px;
    }

    h1 {
        font-size: 6rem !important; /* Ogromny tytuł */
        font-weight: 400;
        line-height: 1;
        margin-bottom: 2rem;
        opacity: 0; /* Do animacji */
        animation: fadeIn 1.5s ease-out forwards;
    }

    .subtitle {
        font-size: 1.2rem;
        line-height: 1.6;
        max-width: 600px;
        margin-bottom: 4rem;
        opacity: 0;
        animation: fadeIn 1.5s ease-out 0.5s forwards; /* Opóźnienie */
    }

    /* NAWIGACJA (ROGI EKRANU) */
    .nav-corner {
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        opacity: 0.7;
    }

    /* STYLIZACJA INPUTÓW (LINIE ZAMIAST PUDEŁEK) */
    .stTextInput > div > div > input {
        background-color: transparent !important;
        border: none !important;
        border-bottom: 1px solid var(--text-color) !important;
        border-radius: 0px !important;
        padding: 10px 0px;
        font-size: 1.2rem;
        color: white !important;
        text-align: center !important;
    }
    .stTextInput > div > div > input:focus {
        box-shadow: none !important;
        border-bottom: 2px solid var(--text-color) !important;
            
    }
    /* Ukrycie labeli nad inputami (zrobimy własne) */
    .stTextInput label {
        display: none;
    }

    /* UPLOADER - TOTALNY MINIMALIZM */
    [data-testid='stFileUploader'] {
        background-color: transparent;
        border: 1px dashed var(--text-color);
        border-radius: 0px;
        padding: 40px;
        transition: all 0.3s ease;
        opacity: 0.8;
    }
    [data-testid='stFileUploader']:hover {
        background-color: rgba(47, 51, 46, 0.05); /* Lekkie przyciemnienie */
        opacity: 1;
    }
    [data-testid='stFileUploader'] button {
        display: none; /* Ukrywamy przycisk "Browse", zostawiamy tylko drag&drop area look */
    }
    /* Tekst wewnątrz uploadera - ZMIANA NA BIAŁY */
    [data-testid='stFileUploader'] section > div,
    [data-testid='stFileUploader'] section > div > span,
    [data-testid='stFileUploader'] section > div > small {
        color: white !important;
    }

    /* PRZYCISK - Outline Style */
    .stButton > button {
        background-color: transparent !important;
        border: 1px solid var(--text-color) !important;
        border-radius: 0px !important; /* Ostry kant */
        color: var(--text-color) !important;
        padding: 15px 40px !important;
        font-size: 1rem !important;
        text-transform: uppercase;
        transition: all 0.3s ease;
        margin-top: 20px;
        width: 100%;
    }
    .stButton > button:hover {
        background-color: var(--text-color) !important;
        color: var(--bg-color) !important; /* Odwrócenie kolorów */
        cursor: pointer;
    }

    /* LISTA PLIKÓW */
    .file-row {
        border-bottom: 1px solid rgba(47, 51, 46, 0.2);
        padding: 20px 0;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    /* ANIMACJE */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Drobny detal - kropka w rogu */
    .dot {
        height: 10px;
        width: 10px;
        background-color: var(--text-color);
        border-radius: 50%;
        display: inline-block;
    }

</style>
""", unsafe_allow_html=True)

def save_to_drive(file_obj, filename):
    # Pobieramy dane logowania z "Sekretów" Streamlit Cloud
    gcp_info = st.secrets["gcp_service_account"]
    folder_id = st.secrets["folder_id"] # ID folderu też w sekretach
    
    creds = service_account.Credentials.from_service_account_info(
        gcp_info, scopes=['https://www.googleapis.com/auth/drive']
    )
    service = build('drive', 'v3', credentials=creds)

    file_metadata = {
        'name': filename,
        'parents': [folder_id]
    }
    
    # Konwersja na format binarny dla Drive API
    media = MediaIoBaseUpload(file_obj, mimetype='audio/wav', resumable=True)
    
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return file.get('id')



# --- 4. UKŁAD STRONY (HEADER - ROGI) ---
# Używamy kolumn, żeby rozrzucić tekst po rogach jak na stronie 'paysages'
header_col1, header_col2 = st.columns([1, 1])

with header_col1:
    st.markdown('<div class="nav-corner">SZYMON OLBER</div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-corner" style="margin-top: 5px;">PRACA INŻYNIERSKA</div>', unsafe_allow_html=True)

with header_col2:
    st.markdown('<div class="nav-corner" style="text-align: right;">UNIWERSYTET PRZYRODNICZY</div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-corner" style="text-align: right; margin-top: 5px;">ROK 2027</div>', unsafe_allow_html=True)

st.markdown("<br><br><br>", unsafe_allow_html=True) # Odstęp (Negative Space)

# --- 5. GŁÓWNA TREŚĆ (HERO) ---
col_main, col_space = st.columns([2, 1]) # Podział asymetryczny dla artyzmu

with col_main:
    st.markdown('<h1>badanie<br>akustyki<br>kaszlu.</h1>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle"><br>Zbieram dane audio w celu trenowania algorytmów monitorowania anomalii.<br>Proces jest anonimowy i służy wyłącznie celom badawczym.</div>', unsafe_allow_html=True)

# --- 6. SEKCJA INTERAKCJI ---
st.markdown("<br>", unsafe_allow_html=True)

if not st.session_state.wyslano:
    # Kontener Uploadu
    c1, c2, c3 = st.columns([1, 8, 1]) # Centrowanie z marginesami
    with c2:
        st.markdown('<div style="font-size: 0.9rem; margin-bottom: 10px; opacity: 0.6;">01. PRZESYŁANIE</div>', unsafe_allow_html=True)
        
        # UPLOADER
        uploaded_files = st.file_uploader("PRZEŚLIJ PLIKI", type=['wav', 'mp3', 'm4a'], accept_multiple_files=True)
        
        if uploaded_files:
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown('<div style="font-size: 0.9rem; margin-bottom: 20px; opacity: 0.6;">02. PLIKI</div>', unsafe_allow_html=True)
            
            dane_plikow = {}
            
            # Pętla generująca surową listę plików
            for plik in uploaded_files:
                # Customowy layout wiersza
                r1, r2 = st.columns([2, 1])
                with r1:
                    st.markdown(f"<div style='padding-top: 15px;'>Plik: {plik.name}</div>", unsafe_allow_html=True)
                with r2:
                    # Minimalistyczny input bez ramki (dzięki CSS)
                    wiek = st.text_input(f"wiek_{plik.name}", placeholder="WIEK PACJENTA", key=plik.name, label_visibility="collapsed")
                    dane_plikow[plik.name] = wiek
                
                # Linia oddzielająca (Separator)
                st.markdown("<hr style='border: 0; border-bottom: 1px solid rgba(47,51,46,0.2); margin: 0;'>", unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Przycisk
            b1, b2, b3 = st.columns([1, 2, 1])
            with b2:
               if st.button("PRZEŚLIJ DANE"):
                
                status = st.empty()
                p_bar = st.progress(0)
                
                for i, plik in enumerate(uploaded_files):
                    # Generowanie nazwy
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    wiek_input = dane_plikow[plik.name]
                    wiek_safe = wiek_input.replace(" ", "").replace(".", "") if wiek_input else "null"
                    nazwa_nowa = f"{timestamp}_{wiek_safe}_{i}.wav"
                    
                    # --- ZMIANA: ZAPIS DO CHMURY ZAMIAST LOKALNIE ---
                    try:
                        save_to_drive(plik, nazwa_nowa)
                        status.text(f"WYSYŁANIE DO CHMURY: {plik.name}...")
                    except Exception as e:
                        st.error(f"Błąd wysyłania: {e}")
                    
                    p_bar.progress((i + 1) / len(uploaded_files))
                
                st.session_state.wyslano = True
                st.rerun()

else:
    # EKRAN KOŃCOWY (Minimalistyczny)
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown(
            """
            <div style="text-align: center; border: 1px solid #2F332E; padding: 60px;">
                <div style="font-size: 3rem; margin-bottom: 20px;">●</div>
                <div style="font-size: 1.5rem; margin-bottom: 10px;">Przesyłanie zakończone.</div>
                <div style="opacity: 0.7; font-size: 0.9rem;">Dziękuje!</div>
            </div>
            """, 
            unsafe_allow_html=True
        )
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("PRZEŚLIJ PONOWNIE"):
            st.session_state.wyslano = False
            st.rerun()

# --- 7. STOPKA (FIXED BOTTOM) ---
# Używamy CSS, żeby przykleić to na dół, ale subtelnie
st.markdown("""
<div style="position: fixed; bottom: 20px; left: 40px; font-size: 10px; opacity: 0.5;">
    INDEX: KOLEKCJA AUDIO
</div>
<div style="position: fixed; bottom: 20px; right: 40px; font-size: 10px; opacity: 0.5;">
    COPYRIGHT © 2027 SZYMON OLBER
</div>
""", unsafe_allow_html=True)