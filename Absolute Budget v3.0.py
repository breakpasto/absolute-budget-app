import streamlit as st
import requests
import re
import time

st.set_page_config(page_title="Absolute Budget v3.0", page_icon="💰")

def get_cheapest_version(card_name):
    url = f"https://api.scryfall.com/cards/search?q=!\"{card_name}\"&unique=prints"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200: return None
        data = response.json()
        valid_prints = []
        for p in data['data']:
            prices = p.get('prices', {})
            pts = [float(prices[k]) for k in ['eur_low', 'eur'] if prices.get(k)]
            if pts:
                valid_prints.append({'name': p['name'], 'price': min(pts)})
        return min(valid_prints, key=lambda x: x['price']) if valid_prints else None
    except: return None

st.title("💰 Absolute Budget v3.0")
lista = st.text_area("Incolla la lista da Moxfield:", height=200)

if st.button("Avvia Analisi Completa", type="primary"):
    if lista:
        linee = [l.strip() for l in lista.split("\n") if l.strip()]
        
        # Divisione in sezioni
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
            st.subheader(f"--- {sec_name} ---")
            for c_line in cards:
                nome = re.sub(r'^(\d+x?|x)\s+', '', c_line).split(' (')[0].strip()
                match_qty = re.match(r'^(\d+)', c_line)
                qty = int(match_qty.group(1)) if match_qty else 1
                
                status.text(f"🔍 Analisi: {nome}...")
                card = get_cheapest_version(nome)
                if card:
                    prezzo_riga = card['price'] * qty
                    totali[sec_name] += prezzo_riga
                    st.write(f"✅ {qty}x {card['name']}: {prezzo_riga:.2f}€")
                time.sleep(0.1)

        status.empty()
        st.divider()
        
        # --- RIEPILOGO FINALE ---
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Solo Comandante", f"{totali['Commander']:.2f} €")
            st.metric("Mazzo (Senza Cmd)", f"{totali['Deck']:.2f} €")
        with col2:
            st.metric("Mazzo Completo", f"{(totali['Commander'] + totali['Deck']):.2f} €", delta_color="inverse")
            st.metric("Sideboard", f"{totali['Sideboard']:.2f} €")
            
        st.balloons()
