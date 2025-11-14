import requests
from bs4 import BeautifulSoup

# --- Configuration directe ---
URL = "https://www.odoo.com/fr_FR/salary_package/simulation/offer/29448?job_id=264&token=2b6b3ebf80c24cd0bceac5094cd92693"
TELEGRAM_TOKEN = "8515800222:AAHpgtDHRRN-uugssRo5zT7EltojjqS7LDs"
TELEGRAM_CHAT_ID = "491275817"


def send_telegram(msg):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data={"chat_id": TELEGRAM_CHAT_ID, "text": msg}
    )


def fetch_car_list():
    r = requests.get(URL)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    options = soup.find_all("option")
    return [o.get_text(strip=True) for o in options if o.get_text(strip=True)]


def main():
    last_list = fetch_car_list()
    send_telegram(f"🚀 Bot lancé – {len(last_list)} voitures détectées.")

    try:
        current_list = fetch_car_list()

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

    except Exception as e:
        send_telegram(f"⚠️ Erreur : {e}")


if __name__ == "__main__":
    main()

