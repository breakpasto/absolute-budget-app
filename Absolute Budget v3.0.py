import requests
import time
import re
from collections import Counter
from datetime import datetime

def get_cheapest_version(card_name):
    """Interroga Scryfall per la stampa con il prezzo EUR minimo assoluto."""
    url = f"https://api.scryfall.com/cards/search?q=!\"{card_name}\"&unique=prints"
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return None
        
        data = response.json()
        prints = data['data']
        
        valid_prints = []
        for p in prints:
            prices = p.get('prices', {})
            price_points = [float(prices[k]) for k in ['eur_low', 'eur'] if prices.get(k)]
            
            if price_points:
                valid_prints.append({
                    'name': p['name'],
                    'set': p['set'].upper(),
                    'collector_number': p['collector_number'],
                    'price': min(price_points)
                })
        
        return min(valid_prints, key=lambda x: x['price']) if valid_prints else None
    except Exception:
        return None

def main():
    input_filename = "decklist.txt"
    now_str = datetime.now().strftime("%d_%m_%Y_%H%M")
    manabox_file = f"manabox_import_{now_str}.txt"
    report_file = f"deck_report_prezzi_{now_str}.txt"

    basic_lands = {
        "Island", "Swamp", "Mountain", "Forest", "Plains", 
        "Snow-Covered Island", "Snow-Covered Swamp", "Snow-Covered Mountain", 
        "Snow-Covered Forest", "Snow-Covered Plains", "Wastes"
    }

    try:
        with open(input_filename, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
    except FileNotFoundError:
        print(f"ERRORE: Assicurati che il file '{input_filename}' esista.")
        return

    # --- PARSING AVANZATO ---
    sections = {"Commander": [], "Deck": [], "Sideboard": []}
    current_section = None
    first_card_found = False
    skip_mode = False

    for l in lines:
        if l.startswith("About"):
            skip_mode = True
            continue
        
        if l == "Commander":
            skip_mode = False
            current_section = "Commander"
            continue
        elif l == "Sideboard":
            skip_mode = False
            current_section = "Sideboard"
            continue
        elif l in ["Deck", "Creatures", "Planeswalkers", "Spells", "Artifacts", "Enchantments", "Lands"]:
            skip_mode = False
            if current_section != "Sideboard":
                current_section = "Deck"
            continue

        if not skip_mode:
            if not first_card_found:
                if re.search(r'[a-zA-Z]', l):
                    sections["Commander"].append(l)
                    first_card_found = True
                    current_section = "Deck"
                    continue
            
            if current_section:
                sections[current_section].append(l)

    # --- ELABORAZIONE ---
    out_manabox = []
    out_report = []
    # Dizionario prezzi per categoria
    prices = {"Commander": 0.0, "Deck": 0.0, "Sideboard": 0.0}
    seen_cards = set()

    print(f"--- MTG Optimizer: Commander Budget Detail ---")

    for section_name, card_list in sections.items():
        if not card_list: continue

        out_manabox.append(f"\n{section_name}")
        out_report.append(f"\n[{section_name.upper()}]" + "-" * 35)

        card_counts = Counter()
        for card_line in card_list:
            name = re.sub(r'^(\d+x?|x)\s+', '', card_line)
            name = re.sub(r'\s\[.*?\]\s.*$', '', name) 
            name = name.split(' (')[0].strip()

            match_qty = re.match(r'^(\d+)', card_line)
            line_qty = int(match_qty.group(1)) if match_qty else 1

            if name not in basic_lands:
                if name in seen_cards and section_name != "Sideboard": 
                    continue
                seen_cards.add(name)
                card_counts[name] = line_qty
            else:
                card_counts[name] += line_qty

        for name, qty in card_counts.items():
            print(f"Ricerca [{section_name}]: {name}...", end="", flush=True)
            cheapest = get_cheapest_version(name)
            
            if cheapest:
                out_manabox.append(f"{qty} {cheapest['name']} ({cheapest['set']}) {cheapest['collector_number']}")
                sub = cheapest['price'] * qty
                
                # Assegna il prezzo alla sezione specifica
                prices[section_name] += sub
                
                out_report.append(f"{qty}x {cheapest['name']:<25} | {cheapest['price']:>6.2f}€ (Tot: {sub:>7.2f}€)")
                print(f" OK! ({cheapest['price']}€)")
            else:
                print(" NON TROVATA")
                out_report.append(f"ERR: {name}")
            time.sleep(0.08)

    # --- CALCOLI FINALI ---
    total_main_only = prices["Deck"]
    total_with_commander = prices["Commander"] + prices["Deck"]
    total_with_side = total_with_commander + prices["Sideboard"]

    # --- SCRITTURA REPORT ---
    with open(manabox_file, "w", encoding="utf-8") as f:
        f.write("\n".join(out_manabox).strip())

    with open(report_file, "w", encoding="utf-8") as f:
        f.write(f"REPORT PREZZI DETTAGLIATO - {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
        f.write("=" * 65 + "\n" + "\n".join(out_report) + "\n" + "=" * 65)
        f.write(f"\nCOSTO SOLO COMMANDER:          {prices['Commander']:>8.2f} EUR")
        f.write(f"\nCOSTO MAZZO (Senza Commander): {total_main_only:>8.2f} EUR")
        f.write(f"\nCOSTO MAZZO (Con Commander):   {total_with_commander:>8.2f} EUR")
        f.write(f"\nCOSTO SIDEBOARD:               {prices['Sideboard']:>8.2f} EUR")
        f.write(f"\n" + "-" * 65)
        f.write(f"\nTOTALE COMPLESSIVO (Tutto):    {total_with_side:>8.2f} EUR\n")

    print("\n" + "="*50)
    print(f"COMPLETATO!")
    print(f"File ManaBox: {manabox_file}")
    print(f"File Report: {report_file}")
    print(f"Mazzo (senza Cmd): {total_main_only:.2f}€ | Con Cmd: {total_with_commander:.2f}€")
    print("="*50)

if __name__ == "__main__":
    main()
