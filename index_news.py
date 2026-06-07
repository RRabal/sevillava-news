import os
import json
import logging
import feedparser
from datetime import datetime, timezone
from googleapiclient.discovery import build
from google.oauth2 import service_account

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

RSS_URL = "https://www.sevillava.fr/blog-feed.xml"

# ⏱ CONFIG
MAX_AGE_MINUTES = 15
THROTTLE_MINUTES = 10
THROTTLE_FILE = "last_push.txt"


# ✅ Vérifie si article récent
def is_fresh(entry):
    if hasattr(entry, 'published_parsed'):
        pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - pub_date
        return delta.total_seconds() < MAX_AGE_MINUTES * 60
    return False


# ✅ Throttling
def can_push():
    if not os.path.exists(THROTTLE_FILE):
        return True

    with open(THROTTLE_FILE, "r") as f:
        last = float(f.read().strip())

    delta = datetime.now(timezone.utc).timestamp() - last
    return delta > THROTTLE_MINUTES * 60


def update_last_push():
    with open(THROTTLE_FILE, "w") as f:
        f.write(str(datetime.now(timezone.utc).timestamp()))


def run():
    key_data = os.getenv('GSC_JSON_KEY')

    if not key_data:
        logging.error("❌ GSC_JSON_KEY manquant")
        return

    if not can_push():
        logging.info("⏱ Throttling actif → skip Indexing API")
        return

    try:
        credentials_info = json.loads(key_data)

        scopes = [
            "https://www.googleapis.com/auth/indexing",
            "https://www.googleapis.com/auth/webmasters"
        ]

        credentials = service_account.Credentials.from_service_account_info(
            credentials_info, scopes=scopes
        )

        feed = feedparser.parse(RSS_URL)

        # ✅ Indexing API intelligent
        idx_service = build('indexing', 'v1', credentials=credentials, static_discovery=False)

        sent = 0

        for entry in feed.entries[:3]:  # batch max 3
            if is_fresh(entry):
                url = entry.link.split('?')[0]

                body = {
                    "url": url,
                    "type": "URL_UPDATED"
                }

                idx_service.urlNotifications().publish(body=body).execute()
                logging.info(f"⚡ Indexing envoyé : {url}")
                sent += 1

        if sent > 0:
            update_last_push()
        else:
            logging.info("⏱ Aucun article assez récent pour Indexing API")

        # ✅ Soumission sitemap (toujours utile)
        gsc_service = build('webmasters', 'v3', credentials=credentials, static_discovery=False)

        gsc_service.sitemaps().submit(
            siteUrl="https://www.sevillava.fr/",
            feedpath="https://www.sevillava.fr/newssitemap.xml"
        ).execute()

        logging.info("✅ Sitemap soumis à Google")

    except Exception as e:
        logging.error(f"❌ Erreur : {e}")


if __name__ == "__main__":
    run()
