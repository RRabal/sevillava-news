import os
import json
import logging
import feedparser
import calendar
from datetime import datetime, timezone
from googleapiclient.discovery import build
from google.oauth2 import service_account

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

RSS_URL = "https://www.sevillava.fr/blog-feed.xml"
SITEMAP_URL = "https://www.sevillava.fr/newssitemap.xml"
SITE_URL = "https://www.sevillava.fr/"

MAX_AGE_MINUTES = 60
THROTTLE_MINUTES = 10
THROTTLE_FILE = "/tmp/last_push.txt"
MAX_URLS_PER_RUN = 5

SCOPES = [
    "https://www.googleapis.com/auth/indexing",
    "https://www.googleapis.com/auth/webmasters",
]


def is_fresh(entry) -> bool:
    """Vérifie si l'article a été publié dans la fenêtre MAX_AGE_MINUTES."""
    try:
        if not hasattr(entry, 'published_parsed') or entry.published_parsed is None:
            return False

        timestamp = calendar.timegm(entry.published_parsed)
        pub_date = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        delta = datetime.now(timezone.utc) - pub_date
        is_recent = delta.total_seconds() < MAX_AGE_MINUTES * 60

        if is_recent:
            logging.info(f"🕐 Article frais ({int(delta.total_seconds()/60)}min) : {entry.get('link', '')}")
        return is_recent
    except Exception as e:
        logging.warning(f"⚠️ Erreur vérification fraîcheur : {e}")
        return False


def can_push() -> bool:
    if not os.path.exists(THROTTLE_FILE):
        return True
    try:
        with open(THROTTLE_FILE, "r") as f:
            last = float(f.read().strip())
        delta = datetime.now(timezone.utc).timestamp() - last
        return delta > THROTTLE_MINUTES * 60
    except Exception:
        return True


def update_last_push():
    try:
        with open(THROTTLE_FILE, "w") as f:
            f.write(str(datetime.now(timezone.utc).timestamp()))
    except Exception:
        pass


def get_credentials(key_data: str):
    credentials_info = json.loads(key_data)
    return service_account.Credentials.from_service_account_info(
        credentials_info, scopes=SCOPES
    )


def submit_to_indexing_api(credentials, urls: list) -> int:
    if not urls:
        return 0
    service = build('indexing', 'v1', credentials=credentials, static_discovery=False)
    sent = 0
    for url in urls[:MAX_URLS_PER_RUN]:
        try:
            body = {"url": url, "type": "URL_UPDATED"}
            service.urlNotifications().publish(body=body).execute()
            logging.info(f"⚡ Indexing API envoyé : {url}")
            sent += 1
        except Exception as e:
            logging.error(f"❌ Indexing échoué pour {url} : {e}")
    return sent


def submit_sitemap(credentials):
    try:
        service = build('webmasters', 'v3', credentials=credentials, static_discovery=False)
        service.sitemaps().submit(siteUrl=SITE_URL, feedpath=SITEMAP_URL).execute()
        logging.info(f"✅ Sitemap soumis à GSC : {SITEMAP_URL}")
    except Exception as e:
        logging.error(f"❌ Erreur soumission sitemap : {e}")


def run():
    key_data = os.getenv('GSC_JSON_KEY')
    if not key_data:
        logging.error("❌ Variable GSC_JSON_KEY manquante")
        return

    try:
        credentials = get_credentials(key_data)
        fresh_urls = []

        # ✅ Priorité : URL injectée depuis Wix via workflow_dispatch
        injected_url = os.getenv('INPUT_URL', '').strip()
        if injected_url:
            clean_url = injected_url.split('?')[0].split('#')[0].rstrip('/')
            fresh_urls.append(clean_url)
            logging.info(f"🎯 URL injectée depuis Wix : {clean_url}")

        # ✅ Complétion via RSS si quota non atteint
        if len(fresh_urls) < MAX_URLS_PER_RUN:
            feed = feedparser.parse(RSS_URL)
            if feed.entries:
                for entry in feed.entries:
                    if len(fresh_urls) >= MAX_URLS_PER_RUN:
                        break
                    if is_fresh(entry):
                        url = entry.link.split('?')[0].split('#')[0].rstrip('/')
                        if url not in fresh_urls:
                            fresh_urls.append(url)

        logging.info(f"📊 URLs fraîches détectées : {len(fresh_urls)}")

        if fresh_urls and can_push():
            sent = submit_to_indexing_api(credentials, fresh_urls)
            if sent > 0:
                update_last_push()

        submit_sitemap(credentials)

    except Exception as e:
        logging.error(f"❌ Erreur générale : {e}")


if __name__ == "__main__":
    run()
