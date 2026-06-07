import os
import json
import logging
import feedparser
import calendar
import urllib.request
import sys
from datetime import datetime, timezone
from googleapiclient.discovery import build
from google.oauth2 import service_account

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

RSS_URL = "https://www.sevillava.fr/blog-feed.xml"
SITEMAP_URL = "https://www.sevillava.fr/newssitemap.xml"
# SITE_URL doit correspondre exactement à ta propriété Search Console
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
    """Vérifie si l'article est récent."""
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
    """Évite d'envoyer trop de requêtes à la suite."""
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
    """Enregistre le moment du dernier envoi."""
    try:
        with open(THROTTLE_FILE, "w") as f:
            f.write(str(datetime.now(timezone.utc).timestamp()))
    except Exception:
        pass

def get_credentials(key_data: str):
    """Charge les clés Google."""
    credentials_info = json.loads(key_data)
    return service_account.Credentials.from_service_account_info(
        credentials_info, scopes=SCOPES
    )

def submit_to_indexing_api(credentials, urls: list) -> int:
    """Envoie les URLs à l'API d'indexation (prioritaire)."""
    if not urls:
        return 0
    try:
        # L'API d'indexation utilise la version v3
        service = build('indexing', 'v3', credentials=credentials, static_discovery=False)
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
    except Exception as e:
        logging.error(f"❌ Erreur build Indexing API : {e}")
        return 0

def submit_sitemap(credentials):
    """Informe Google de la mise à jour du sitemap."""
    try:
        # Nom moderne de l'API : searchconsole v1
        service = build('searchconsole', 'v1', credentials=credentials, static_discovery=False)
        service.sitemaps().submit(siteUrl=SITE_URL, feedpath=SITEMAP_URL).execute()
        logging.info(f"✅ Sitemap soumis via Search Console API : {SITEMAP_URL}")
    except Exception as e:
        logging.warning(f"⚠️ API Search Console : tentative via Ping suite à : {e}")
        try:
            ping_url = f"https://www.google.com/ping?sitemap={SITEMAP_URL}"
            urllib.request.urlopen(ping_url)
            logging.info(f"✅ Sitemap soumis via Ping Google")
        except Exception as ping_e:
            logging.error(f"❌ Échec total soumission sitemap : {ping_e}")

def run():
    """Fonction principale."""
    key_data = os.getenv('GSC_JSON_KEY')
    if not key_data:
        logging.error("❌ Variable GSC_JSON_KEY manquante")
        sys.exit(1)

    try:
        credentials = get_credentials(key_data)
        fresh_urls = []

        # 1. URL injectée manuellement ou via Wix
        in
