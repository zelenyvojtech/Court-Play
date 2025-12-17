import os
import urllib.request
import time

# Cílová složka
TARGET_DIR = "static/img"

# Použijeme službu Picsum, která povoluje stahování.
# Formát: (název_souboru, url_k_stažení)
IMAGES = {
    "hero.jpg": "https://picsum.photos/seed/tennis_hero/1200/800",
    "court_clay.jpg": "https://picsum.photos/seed/clay/600/400",
    "court_indoor.jpg": "https://picsum.photos/seed/indoor/600/400",
    "trainer.jpg": "https://picsum.photos/seed/trainer/600/400",
    "clubhouse.jpg": "https://picsum.photos/seed/house/800/600",
    "balls.jpg": "https://picsum.photos/seed/balls/600/400",
    "game.jpg": "https://picsum.photos/seed/game/600/400",
    "tournament.jpg": "https://picsum.photos/seed/tour/600/400",
    "map.jpg": "https://picsum.photos/seed/map/800/400",
    "racket.jpg": "https://picsum.photos/seed/racket/600/400"
}


def download_images():
    # 1. Vytvoření složky
    if not os.path.exists(TARGET_DIR):
        print(f"Vytvářím složku: {TARGET_DIR}")
        os.makedirs(TARGET_DIR)

    # 2. Stahování
    print("Začínám stahovat obrázky z Lorem Picsum...")

    # Přidáme hlavičku User-Agent, pro jistotu
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)')]
    urllib.request.install_opener(opener)

    for filename, url in IMAGES.items():
        file_path = os.path.join(TARGET_DIR, filename)

        print(f"Stahuji: {filename} ... ", end="")
        try:
            urllib.request.urlretrieve(url, file_path)
            print("OK")
        except Exception as e:
            print(f"CHYBA: {e}")

        # Malá pauza, abychom nezahltili server
        time.sleep(0.5)

    print("\n--- HOTOVO ---")
    print(f"Obrázky jsou uloženy v: {os.path.abspath(TARGET_DIR)}")


if __name__ == "__main__":
    download_images()