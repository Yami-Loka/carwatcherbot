import os
import time
import requests
from bs4 import BeautifulSoup

# --- Configuration via variables d'environnement ---
URL = os.getenv("WATCH_URL")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


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


def fetch_car_list(max_retries=5):
    """Récupère la liste des voitures depuis la page Odoo avec gestion du 429"""

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        )
    }

    for attempt in range(max_retries):
        try:
            r = requests.get(URL, headers=headers, timeout=10)

            # --- Succès ---
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                options = soup.find_all("option")
                return [o.get_text(strip=True) for o in options if o.get_text(strip=True)]

            # --- Blocage anti-bot ---
            if r.status_code == 429:
                wait = (attempt + 1) * 10
                print(f"[WARN] 429 Too Many Requests – retry in {wait}s")
                time.sleep(wait)
                continue

            # --- Autres erreurs HTTP ---
            print(f"[ERROR] HTTP {r.status_code}")
            return None

        except Exception as e:
            print(f"[ERROR] fetch_car_list exception: {e}")
            time.sleep(2)

    print("[ERROR] Max retry limit reached.")
    return None


def main():
    last_list = fetch_car_list()

    if not last_list:
        send_telegram("⚠️ Impossible de récupérer la liste initiale (429 ou autre erreur).")
        return

    # (Tu peux supprimer ce message si tu le veux)
    send_telegram(f"🚀 Bot lancé – {len(last_list)} voitures détectées.")

    current_list = fetch_car_list()

    if not current_list:
        send_telegram("⚠️ Impossible de récupérer la liste actuelle (429 ou autre erreur).")
        return

    added = [c for c in current_list if c not in last_list]
    removed = [c for c in last_list if c not in current_list]

    if not added and not removed:
        print("Aucun changement.")
        return

    msg = "🔔 Changement détecté !\n"
    if added:
        msg += "🟢 Ajoutés :\n" + "\n".join("• " + a for a in added) + "\n"
    if removed:
        msg += "🔴 Retirés :\n" + "\n".join("• " + r for r in removed) + "\n"

    msg += "📋 Liste actuelle :\n" + "\n".join("• " + c for c in current_list)

    send_telegram(msg)


if __name__ == "__main__":
    main()
