import os
import time
import requests
from bs4 import BeautifulSoup

# --- Configuration via variables d'environnement ---
URL = os.getenv("WATCH_URL")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Paramètres de contrôle ---
MAX_RETRIES = 3           # nombre max de tentatives en cas de 429
BACKOFF_FACTOR = 15       # temps d'attente en secondes entre retries
SLEEP_BETWEEN_REQUESTS = 5  # pour éviter de spammer le serveur

def send_telegram(msg):
    """Envoie un message sur Telegram"""
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": msg},
            timeout=10
        )
    except Exception as e:
        print(f"[WARN] Impossible d'envoyer le message Telegram : {e}")

def fetch_car_list():
    """Récupère la liste des voitures avec gestion du 429 et retries"""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        )
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.get(URL, headers=headers, timeout=10)

            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                options = soup.find_all("option")
                return [o.get_text(strip=True) for o in options if o.get_text(strip=True)]

            elif r.status_code == 429:
                wait = attempt * BACKOFF_FACTOR
                print(f"[WARN] 429 Too Many Requests – retry in {wait}s (attempt {attempt}/{MAX_RETRIES})")
                time.sleep(wait)
                continue

            else:
                print(f"[ERROR] HTTP {r.status_code}")
                return None

        except Exception as e:
            print(f"[ERROR] fetch_car_list exception: {e}")
            time.sleep(2)

    print("[ERROR] Max retry limit reached.")
    return None

def main():
    # --- Récupération de la liste précédente ---
    last_list_file = "last_list.txt"
    if os.path.exists(last_list_file):
        with open(last_list_file, "r", encoding="utf-8") as f:
            last_list = [line.strip() for line in f.readlines()]
    else:
        last_list = []

    current_list = fetch_car_list()
    if current_list is None:
        print("[WARN] Impossible de récupérer la liste actuelle. Fin du script.")
        return

    # --- Comparaison pour détecter changements ---
    added = [c for c in current_list if c not in last_list]
    removed = [c for c in last_list if c not in current_list]

    if added or removed:
        msg = "🔔 Changement détecté !\n"
        if added:
            msg += "🟢 Ajoutés :\n" + "\n".join("• " + a for a in added) + "\n"
        if removed:
            msg += "🔴 Retirés :\n" + "\n".join("• " + r for r in removed) + "\n"
        msg += "📋 Liste actuelle :\n" + "\n".join("• " + c for c in current_list)

        send_telegram(msg)
    else:
        print("Aucun changement détecté.")

    # --- Sauvegarde de la liste actuelle pour la prochaine exécution ---
    with open(last_list_file, "w", encoding="utf-8") as f:
        f.write("\n".join(current_list))

if __name__ == "__main__":
    main()
