import os
import json
import logging
import feedparser
import calendar
import urllib.request
from datetime import datetime, timezone
from googleapiclient.discovery import build
from google.oauth2 import service_account

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

RSS_URL = "https://www.sevillava.fr/blog-feed.xml"
SITEMAP_URL = "https://www.sevillava.fr/newssitemap.xml"
# ### FIX : Vérifie bien ce nom dans ta Search Console
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
    # Utilisation de la v3 qui est la plus stable pour l'indexing
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

def submit_sitemap(credentials):
    """Soumet le sitemap via l'API Search Console ou par Ping HTTP en secours."""
    try:
        # Tentative via l'API moderne
        service = build('searchconsole', 'v1', credentials=credentials, static_discovery=False)
        service.sitemaps().submit(siteUrl=SITE_URL, feedpath=SITEMAP_URL).execute()
        logging.info(f"✅ Sitemap soumis via Search
