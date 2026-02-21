import flet as ft
from flet import colors, icons  # <--- Importiamo esplicitamente colori e icone
import requests
import time
import re
from datetime import datetime

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
            pts = [float(prices[k]) for k in ['eur_low', 'eur'] if prices.get(k)]
            if pts:
                valid_prints.append({
                    'name': p['name'], 
                    'set': p['set'].upper(), 
                    'num': p['collector_number'], 
                    'price': min(pts)
                })
        return min(valid_prints, key=lambda x: x['price']) if valid_prints else None
    except: return None

# --- INTERFACCIA GRAFICA ---
def main(page: ft.Page):
    page.title = "Absolute Budget v3.0"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = "adaptive"
    page.padding = 20

    # Componenti UI
    input_list = ft.TextField(
        label="Incolla qui la lista da Moxfield",
        multiline=True,
        min_lines=10,
        hint_text="Esempio:\nCommander\n1 Go-Shintai...\n\nDeck\n1 Island..."
    )
    
    status_text = ft.Text("Pronto per l'analisi", color=colors.BLUE_400)
    progress_bar = ft.ProgressBar(width=400, color=colors.BLUE_400, visible=False)
    
    results_column = ft.Column()
    summary_card = ft.Card(visible=False)

    def analyze_click(e):
        if not input_list.value:
            status_text.value = "Errore: Incolla prima una lista!"
            status_text.color = colors.RED_400
            page.update()
            return

        results_column.controls.clear()
        summary_card.visible = False
        progress_bar.visible = True
        status_text.value = "Ricerca in corso su Scryfall..."
        status_text.color = colors.BLUE_400
        analyze_btn.disabled = True
        page.update()

        lines = [l.strip() for l in input_list.value.split("\n") if l.strip()]
        sections = {"Commander": [], "Deck": [], "Sideboard": []}
        curr_sec, first_found, skip = None, False, False
        
        # Parsing
        for l in lines:
            if l.startswith("About"): skip = True; continue
            if l in ["Commander", "Sideboard", "Deck"]: skip = False; curr_sec = l; continue
            if not skip:
                if not first_found and re.search(r'[a-zA-Z]', l):
                    sections["Commander"].append(l); first_found = True; curr_sec = "Deck"; continue
                if curr_sec: sections[curr_sec].append(l)

        prices = {"Commander": 0.0, "Deck": 0.0, "Sideboard": 0.0}
        
        for sec_name, cards in sections.items():
            if not cards: continue
            results_column.controls.append(
                ft.Container(
                    content=ft.Text(f"{sec_name.upper()}", weight="bold", size=18, color=colors.AMBER_400),
                    margin=ft.margin.only(top=20)
                )
            )
            
            for c_line in cards:
                name = re.sub(r'^(\d+x?|x)\s+', '', c_line).split(' (')[0].strip()
                match_qty = re.match(r'^(\d+)', c_line)
                qty = int(match_qty.group(1)) if match_qty else 1
                
                cheapest = get_cheapest_version(name)
                if cheapest:
                    sub = cheapest['price'] * qty
                    prices[sec_name] += sub
                    results_column.controls.append(
                        ft.ListTile(
                            leading=ft.Icon(icons.STYLE),
                            title=ft.Text(f"{qty}x {cheapest['name']}"),
                            subtitle=ft.Text(f"{cheapest['set']} #{cheapest['num']}"),
                            trailing=ft.Text(f"{sub:.2f} €", weight="bold")
                        )
                    )
                else:
                    results_column.controls.append(ft.Text(f"❌ {name} non trovata", color=colors.RED_300))
                
                time.sleep(0.08)
                page.update()

        # Calcoli finali
        total_main = prices["Commander"] + prices["Deck"]
        summary_card.content = ft.Container(
            padding=20,
            content=ft.Column([
                ft.Text("RIEPILOGO COSTI", size=20, weight="bold", color=colors.BLUE_200),
                ft.Divider(),
                ft.Text(f"Solo Commander: {prices['Commander']:.2f} €"),
                ft.Text(f"Mazzo (Senza Cmd): {prices['Deck']:.2f} €"),
                ft.Text(f"Mazzo Completo: {total_main:.2f} €", color=colors.GREEN_400, size=18, weight="bold"),
                ft.Text(f"Sideboard: {prices['Sideboard']:.2f} €"),
            ], spacing=5)
        )
        summary_card.visible = True
        progress_bar.visible = False
        status_text.value = "Analisi completata!"
        analyze_btn.disabled = False
        page.update()

    analyze_btn = ft.ElevatedButton(
        "Avvia Analisi Absolute Budget", 
        on_click=analyze_click, 
        icon=icons.PLAY_ARROW_ROUNDED,
        style=ft.ButtonStyle(color=colors.WHITE, bgcolor=colors.BLUE_700)
    )

    page.add(
        ft.Row([ft.Icon(icons.WALLET, size=40), ft.Text("Absolute Budget v3.0", size=30, weight="bold")]),
        ft.Text("Ottimizzatore di mazzi Magic: The Gathering", italic=True, color=colors.GREY_400),
        input_list,
        ft.Row([analyze_btn, status_text], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        progress_bar,
        summary_card,
        results_column
    )

# Questo abilita l'accesso da altri dispositivi nella tua rete (casa)
ft.app(target=main, view=None, port=8550, host="0.0.0.0")
