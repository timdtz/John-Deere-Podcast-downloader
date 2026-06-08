import os
import requests
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

# Konfiguration
rss_url = "https://feeds.megaphone.fm/KBBF4939684019"
download_folder = "JohnDeere_Podcast"

def clean_filename(title):
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        title = title.replace(char, '')
    return title.strip()

def select_episodes(episodes):
    """Zeigt alle Episoden an und lässt den Nutzer eine Auswahl treffen."""
    print("\nVerfügbare Episoden:")
    print("-" * 60)
    for i, (title, _, exists) in enumerate(episodes, 1):
        status = " [bereits vorhanden]" if exists else ""
        print(f"  {i:>3}. {title}{status}")
    print("-" * 60)
    print("\nAuswahl (Beispiele):")
    print("  'all'       → alle Episoden")
    print("  'new'       → nur noch nicht vorhandene")
    print("  '1 3 5'     → Episoden 1, 3 und 5")
    print("  '1-5'       → Episoden 1 bis 5")
    print("  '1-3 7 9'   → Kombination\n")

    while True:
        auswahl = input("Deine Auswahl: ").strip().lower()

        if auswahl == "all":
            return list(range(len(episodes)))
        elif auswahl == "new":
            return [i for i, (_, _, exists) in enumerate(episodes) if not exists]
        else:
            indices = set()
            try:
                for part in auswahl.split():
                    if '-' in part:
                        start, end = part.split('-')
                        indices.update(range(int(start) - 1, int(end)))
                    else:
                        indices.add(int(part) - 1)
                # Ungültige Indizes herausfiltern
                valid = [i for i in sorted(indices) if 0 <= i < len(episodes)]
                if valid:
                    return valid
                else:
                    print("Keine gültigen Nummern – bitte erneut versuchen.")
            except ValueError:
                print("Ungültige Eingabe – bitte erneut versuchen.")

def download_episodes():
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)

    print(f"Lade Feed: {rss_url} ...")
    try:
        response = requests.get(rss_url)
        root = ET.fromstring(response.content)
    except Exception as e:
        print(f"Fehler beim Laden des Feeds: {e}")
        return

    # Alle Episoden einlesen
    episodes = []
    for item in root.findall('./channel/item'):
        title_el = item.find('title')
        enclosure = item.find('enclosure')
        if title_el is None or enclosure is None:
            continue
        title = title_el.text
        url = enclosure.get('url')
        filename = clean_filename(title) + ".mp3"
        filepath = os.path.join(download_folder, filename)
        exists = os.path.exists(filepath)
        episodes.append((title, url, exists))

    if not episodes:
        print("Keine Episoden im Feed gefunden.")
        return

    # Auswahl treffen
    selected_indices = select_episodes(episodes)

    if not selected_indices:
        print("Keine Episoden ausgewählt.")
        return

    print(f"\nStarte Download von {len(selected_indices)} Episode(n)...\n")

    for i in selected_indices:
        title, url, exists = episodes[i]
        filename = clean_filename(title) + ".mp3"
        filepath = os.path.join(download_folder, filename)

        if exists:
            print(f"[Übersprungen] Existiert bereits: {filename}")
            continue

        print(f"Lade herunter: {filename}")
        try:
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(filepath, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            print(f"  ✓ Fertig")
        except Exception as e:
            print(f"  ✗ Fehler: {e}")

    print("\nFertig! Alle gewählten Folgen liegen im Ordner:", download_folder)

if __name__ == "__main__":
    download_episodes()