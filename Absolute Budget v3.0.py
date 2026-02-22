import streamlit as st
import requests
import re
import time

# Configurazione della pagina Streamlit per Mobile
st.set_page_config(
    page_title="Budget Checker 100€", 
    page_icon="⚖️", 
    layout="wide"
)

# --- FUNZIONE DI RICERCA PREZZI ---
def get_market_price(card_name):
    # API Scryfall: cerca la stampa più economica basata sul prezzo 'eur' (Trend di mercato)
    url = f"https://api.scryfall.com/cards/search?q=!\"{card_name}\"&unique=prints"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200: 
            return None
        data = response.json()
        valid_prices = []
        for p in data['data']:
            prices = p.get('prices', {})
            val = prices.get('eur')
            if val:
                valid_prices.append(float(val))
        
        # Restituisce il prezzo della versione più economica tra tutte le stampe esistenti
        return min(valid_prices) if valid_prices else None
    except:
        return None

# --- INTERFACCIA UTENTE ---
st.title("⚖️ MTG Absolute Budget Checker")
st.markdown("### Soglia massima consentita: **100.00 €**")

# Area di testo per la lista
lista_raw = st.text_area(
    "Incolla qui la lista esportata da Moxfield:", 
    height=250, 
    placeholder="Commander\n1 Mendicant Core, Guidelight\n\nDeck\n1 Academy Ruins\n..."
)

if st.button("Verifica Legalità Budget", type="primary"):
    if lista_raw:
        linee = [l.strip() for l in lista_raw.split("\n") if l.strip()]
        
        # Struttura per dividere le carte
        sections = {"Commander": [], "Deck": [], "Sideboard": []}
        curr_sec, first_found, skip = None, False, False
        
        # Logica di Parsing per Moxfield
        for l in linee:
            if l.startswith("About"): skip = True; continue
            if l in ["Commander", "Sideboard", "Deck"]: skip = False; curr_sec = l; continue
            if not skip:
                # Se non è ancora stata trovata una sezione, la prima carta è il Commander
                if not first_found and re.search(r'[a-zA-Z]', l):
                    sections["Commander"].append(l); first_found = True; curr_sec = "Deck"; continue
                if curr_sec: 
                    sections[curr_sec].append(l)

        totali = {"Commander": 0.0, "Deck": 0.0, "Sideboard": 0.0}
        status = st.empty()
        
        # Visualizzazione Dettagliata
        for sec_name, cards in sections.items():
            if not cards: continue
            with st.expander(f"Dettaglio {sec_name}", expanded=(sec_name == "Commander")):
                for c_line in cards:
                    # Estrazione Quantità e Nome
                    nome = re.sub(r'^(\d+x?|x)\s+', '', c_line).split(' (')[0].strip()
                    match_qty = re.match(r'^(\d+)', c_line)
                    qty = int(match_qty.group(1)) if match_qty else 1
                    
                    status.text(f"🔍 Recupero prezzo: {nome}...")
                    prezzo_unitario = get_market_price(nome)
                    
                    if prezzo_unitario:
                        prezzo_riga = prezzo_unitario * qty
                        totali[sec_name] += prezzo_riga
                        st.write(f"**{qty}x** {nome} — `{prezzo_riga:.2f}€`")
                    else:
                        st.write(f"⚠️ **{nome}**: Prezzo non trovato")
                    
                    # Delay per non sovraccaricare le API di Scryfall
                    time.sleep(0.1)

        status.empty()
        st.divider()
        
        # --- CALCOLI FINALI ---
        mainboard_senza_cmd = totali["Deck"]
        totale_completo = totali["Commander"] + totali["Deck"]
        is_legale = totale_completo <= 100
        
        # Intestazione Risultato
        if is_legale:
            st.success(f"### ✅ MAZZO LEGALE")
        else:
            st.error(f"### ❌ MAZZO ILLEGALE")

        # Layout a 4 Colonne (Richiesto)
        c1, c2, c3, c4 = st.columns(4)
        
        # Colonna 1: Totale (Cmd + Deck)
        c1.metric(
            label="TOTALE MAZZO", 
            value=f"{totale_completo:.2f} €", 
            delta=f"{100 - totale_completo:.2f} €" if is_legale else f"Sforato di {totale_completo - 100:.2f} €",
            delta_color="normal" if is_legale else "inverse"
        )
        
        # Colonna 2: Solo Comandante
        c2.metric(label="SOLO COMMANDER", value=f"{totali['Commander']:.2f} €")
        
        # Colonna 3: Mazzo senza Comandante
        c3.metric(label="DECK (Senza Cmd)", value=f"{mainboard_senza_cmd:.2f} €")
        
        # Colonna 4: Sideboard
        c4.metric(label="SIDEBOARD", value=f"{totali['Sideboard']:.2f} €")

        # Feedback extra
        if not is_legale:
            st.warning(f"Attenzione: Devi ridurre il costo totale di almeno **{(totale_completo - 100):.2f} €** per rientrare nel budget.")
        else:
            st.balloons()
    else:
        st.warning("Per favore, incolla la tua lista prima di procedere.")
