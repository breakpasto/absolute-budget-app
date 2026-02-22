import streamlit as st
import requests
import re
import time

st.set_page_config(page_title="Budget Checker 100€", page_icon="⚖️")

def get_market_price(card_name):
    url = f"https://api.scryfall.com/cards/search?q=!\"{card_name}\"&unique=prints"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200: return None
        data = response.json()
        valid_prices = []
        for p in data['data']:
            prices = p.get('prices', {})
            # Usiamo 'eur' che è il prezzo di mercato/tendenza, più realistico per il limite dei 100€
            val = prices.get('eur')
            if val:
                valid_prices.append(float(val))
        
        # Prendiamo la stampa più economica (ma basata su prezzo di mercato)
        return min(valid_prices) if valid_prices else None
    except: return None

st.title("⚖️ MTG Budget Checker")
st.subheader("Limite: 100.00 €")

lista = st.text_area("Incolla qui la lista da Moxfield:", height=200)

if st.button("Verifica Legalità Budget", type="primary"):
    if lista:
        linee = [l.strip() for l in lista.split("\n") if l.strip()]
        sections = {"Commander": [], "Deck": [], "Sideboard": []}
        curr_sec, first_found, skip = None, False, False
        
        for l in linee:
            if l.startswith("About"): skip = True; continue
            if l in ["Commander", "Sideboard", "Deck"]: skip = False; curr_sec = l; continue
            if not skip:
                if not first_found and re.search(r'[a-zA-Z]', l):
                    sections["Commander"].append(l); first_found = True; curr_sec = "Deck"; continue
                if curr_sec: sections[curr_sec].append(l)

        totali = {"Commander": 0.0, "Deck": 0.0, "Sideboard": 0.0}
        status = st.empty()
        
        for sec_name, cards in sections.items():
            if not cards: continue
            with st.expander(f"Dettaglio {sec_name}", expanded=True):
                for c_line in cards:
                    nome = re.sub(r'^(\d+x?|x)\s+', '', c_line).split(' (')[0].strip()
                    match_qty = re.match(r'^(\d+)', c_line)
                    qty = int(match_qty.group(1)) if match_qty else 1
                    
                    status.text(f"Valutando: {nome}...")
                    prezzo_unitario = get_market_price(nome)
                    if prezzo_unitario:
                        prezzo_riga = prezzo_unitario * qty
                        totali[sec_name] += prezzo_riga
                        st.write(f"{qty}x {nome} — {prezzo_riga:.2f}€")
                    else:
                        st.write(f"⚠️ {nome}: Prezzo non trovato")
                    time.sleep(0.1)

        status.empty()
        st.divider()
        
        totale_legale = totali["Commander"] + totali["Deck"]
        colore = "normal" if totale_legale <= 100 else "inverse"
        label_stato = "✅ LEGALE (Under 100€)" if totale_legale <= 100 else "❌ ILLEGALE (Over 100€)"
        
        st.header(label_stato)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Totale Mazzo", f"{totale_legale:.2f} €", delta=f"{100 - totale_legale:.2f} rimasti", delta_color=colore)
        c2.metric("Commander", f"{totali['Commander']:.2f} €")
        c3.metric("Sideboard", f"{totali['Sideboard']:.2f} €")

        if totale_legale > 100:
            st.warning(f"Sforamento rilevato: devi tagliare almeno {(totale_legale - 100):.2f}€!")
        else:
            st.balloons()
