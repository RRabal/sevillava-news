import os
import json
import logging
import feedparser
import calendar
import sys
from datetime import datetime, timezone
from googleapiclient.discovery import build
from google.oauth2 import service_account

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

RSS_URL = "https://www.sevillava.fr/blog-feed.xml"
SITEMAP_URL = "https://www.sevillava.fr/newssitemap.xml"
SITE_URL = "sc-domain:sevillava.fr" 

MAX_AGE_MINUTES = 60
THROTTLE_MINUTES = 10
THROTTLE_FILE = "/tmp/last_push.txt"
MAX_URLS_PER_RUN = 5

SCOPES = [
    "https://www.googleapis.com/auth/indexing",
    "https://www.googleapis.com/auth/webmasters", # Requis pour Search Console
]

def is_fresh(entry) -> bool:
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
    except Exception:
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
    try:
        service = build('indexing', 'v3', credentials=credentials, static_discovery=False)
        sent = 0
        for url in urls:
            try:
                body = {"url": url, "type": "URL_UPDATED"}
                service.urlNotifications().publish(body=body).execute()
                logging.info(f"⚡ Indexing API envoyé : {url}")
                sent += 1
            except Exception as e:
                logging.error(f"❌ Indexing échoué pour {url} : {e}")
        return sent
    except Exception as e:
        logging.error(f"❌ Erreur Indexing API : {e}")
        return 0

def submit_sitemap(credentials):
    """Soumet le sitemap via l'API Search Console."""
    try:
        # Note: On utilise 'searchconsole' v1
        service = build('searchconsole', 'v1', credentials=credentials, static_discovery=False)
        service.sitemaps().submit(siteUrl=SITE_URL, feedpath=SITEMAP_URL).execute()
        logging.info(f"✅ Sitemap soumis avec succès via l'API")
    except Exception as e:
        logging.error(f"❌ Erreur soumission sitemap : {e}")

def run():
    key_data = os.getenv('GSC_JSON_KEY')
    if not key_data:
        logging.error("❌ Variable GSC_JSON_KEY manquante")
        sys.exit(1)

    try:
        credentials = get_credentials(key_data)
        fresh_urls = []

        # 1. Check URL manuelle (GitHub Input)
        injected_url = os.getenv('INPUT_URL', '').strip()
        if injected_url:
            clean_url = injected_url.split('?')[0].split('#')[0].rstrip('/')
            fresh_urls.append(clean_url)

        # 2. Check RSS
        feed = feedparser.parse(RSS_URL)
        if feed.entries:
            for entry in feed.entries:
                if len(fresh_urls) >= MAX_URLS_PER_RUN:
                    break
                if is_fresh(entry):
                    url = entry.link.split('?')[0].split('#')[0].rstrip('/')
                    if url not in fresh_urls:
                        fresh_urls.append(url)

        logging.info(f"📊 URLs à traiter : {len(fresh_urls)}")

        if fresh_urls:
            if can_push():
                sent = submit_to_indexing_api(credentials, fresh_urls)
                if sent > 0:
                    update_last_push()
            else:
                logging.info("⏳ Throttling actif (10min)")

        # Toujours essayer de soumettre le sitemap
        submit_sitemap(credentials)

    except Exception as e:
        logging.error(f"❌ Erreur : {e}")

if __name__ == "__main__":
    run()
