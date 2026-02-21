import streamlit as st
import requests
import re
import time

# Configurazione Pagina
st.set_page_config(page_title="Absolute Budget v3.0", page_icon="💰")

# --- LOGICA DI RICERCA ---
def get_cheapest_version(card_name):
    url = f"https://api.scryfall.com/cards/search?q=!\"{card_name}\"&unique=prints"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200: return None
        data = response.json()
        valid_prints = []
        for p in data['data']:
            prices = p.get('prices', {})
            # Prende il prezzo più basso tra eur e eur_low
            pts = [float(prices[k]) for k in ['eur_low', 'eur'] if prices.get(k)]
            if pts:
                valid_prints.append({
                    'name': p['name'], 
                    'set': p['set'].upper(), 
                    'price': min(pts)
                })
        return min(valid_prints, key=lambda x: x['price']) if valid_prints else None
    except: return None

# --- INTERFACCIA STREAMLIT ---
st.title("💰 Absolute Budget v3.0")
st.markdown("### Ottimizzatore prezzi per Moxfield")

lista = st.text_area("Incolla qui la lista esportata da Moxfield:", height=250, placeholder="Commander\n1 Go-Shintai...\n\nDeck\n1 Island...")

if st.button("Avvia Analisi", type="primary"):
    if lista:
        linee = [l.strip() for l in lista.split("\n") if l.strip()]
        progress_bar = st.progress(0)
        status = st.empty()
        container_risultati = st.container()
        
        totale = 0.0
        carte_trovate = 0
        
        for i, linea in enumerate(linee):
            # Salta le intestazioni e cerca solo righe con nomi di carte
            if re.search(r'[a-zA-Z]', linea) and linea not in ["Deck", "Commander", "Sideboard", "Maybeboard"]:
                # Estrae il nome (rimuove quantità e codici set tra parentesi)
                nome = re.sub(r'^(\d+x?|x)\s+', '', linea).split(' (')[0].strip()
                
                status.text(f"🔍 Cerco su Scryfall: {nome}...")
                card = get_cheapest_version(nome)
                
                with container_risultati:
                    if card:
                        st.write(f"✅ **{card['name']}** ({card['set']}): **{card['price']:.2f}€**")
                        totale += card['price']
                        carte_trovate += 1
                    else:
                        st.write(f"❌ **{nome}**: Non trovata o prezzo non disponibile")
                
                # Rispetta i limiti delle API di Scryfall
                time.sleep(0.1)
            
            # Aggiorna barra progresso
            progress_bar.progress((i + 1) / len(linee))
        
        status.empty()
        st.success(f"Analisi completata! {carte_trovate} carte analizzate.")
        st.metric(label="Costo Totale Stimato (Prezzi più bassi)", value=f"{totale:.2f} €")
        
        st.balloons()
    else:
        st.error("Per favore, incolla una lista prima di cliccare!")

# Istruzioni extra
with st.expander("Come funziona?"):
    st.write("""
    1. Vai su Moxfield.
    2. Clicca su 'Export' e copia il testo.
    3. Incollalo qui sopra.
    4. L'app cercherà la stampa più economica in assoluto per ogni carta.
    """)
