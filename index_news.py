import os
import json
import logging
import feedparser
from datetime import datetime, timezone
from googleapiclient.discovery import build
from google.oauth2 import service_account

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

RSS_URL = "https://www.sevillava.fr/blog-feed.xml"
SITEMAP_URL = "https://www.sevillava.fr/newssitemap.xml"
SITE_URL = "https://www.sevillava.fr/"

# ✅ Fenêtre élargie : on indexe les articles publiés dans les 60 dernières minutes
MAX_AGE_MINUTES = 60

# ✅ Throttling : pas plus d'un push toutes les 10 minutes
THROTTLE_MINUTES = 10
THROTTLE_FILE = "/tmp/last_push.txt"  # /tmp évite les conflits git

# ✅ Quota Google Indexing API : 200 req/jour, on limite à 5 par run
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
        timestamp = feedparser.mktime_tz(entry.published_parsed)
        if timestamp is None:
            return False
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
    """Throttling basé sur un fichier timestamp."""
    if not os.path.exists(THROTTLE_FILE):
        return True
    try:
        with open(THROTTLE_FILE, "r") as f:
            last = float(f.read().strip())
        delta = datetime.now(timezone.utc).timestamp() - last
        remaining = THROTTLE_MINUTES * 60 - delta
        if remaining > 0:
            logging.info(f"⏱ Throttling actif → {int(remaining)}s restantes")
            return False
        return True
    except Exception:
        return True


def update_last_push():
    """Met à jour le timestamp du dernier push."""
    try:
        with open(THROTTLE_FILE, "w") as f:
            f.write(str(datetime.now(timezone.utc).timestamp()))
    except Exception as e:
        logging.warning(f"⚠️ Impossible d'écrire throttle file : {e}")


def get_credentials(key_data: str):
    """Crée les credentials Google depuis la clé JSON."""
    credentials_info = json.loads(key_data)
    return service_account.Credentials.from_service_account_info(
        credentials_info,
        scopes=SCOPES
    )


def submit_to_indexing_api(credentials, urls: list) -> int:
    """Soumet les URLs à l'Indexing API. Retourne le nombre de succès."""
    if not urls:
        return 0

    service = build(
        'indexing', 'v1',
        credentials=credentials,
        static_discovery=False
    )

    sent = 0
    for url in urls[:MAX_URLS_PER_RUN]:
        try:
            body = {"url": url, "type": "URL_UPDATED"}
            response = service.urlNotifications().publish(body=body).execute()
            logging.info(f"⚡ Indexing OK : {url} → {response.get('urlNotificationMetadata', {}).get('latestUpdate', {}).get('url', '')}")
            sent += 1
        except Exception as e:
            logging.error(f"❌ Indexing échoué pour {url} : {e}")

    return sent


def submit_sitemap(credentials):
    """Soumet le sitemap à Google Search Console."""
    try:
        service = build(
            'webmasters', 'v3',
            credentials=credentials,
            static_discovery=False
        )
        service.sitemaps().submit(
            siteUrl=SITE_URL,
            feedpath=SITEMAP_URL
        ).execute()
        logging.info(f"✅ Sitemap soumis à GSC : {SITEMAP_URL}")
    except Exception as e:
        logging.error(f"❌ Erreur soumission sitemap : {e}")


def run():
    # ✅ Vérification clé API
    key_data = os.getenv('GSC_JSON_KEY')
    if not key_data:
        logging.error("❌ Variable GSC_JSON_KEY manquante")
        return

    # ✅ Throttling check
    throttling_active = not can_push()

    try:
        credentials = get_credentials(key_data)
    except Exception as e:
        logging.error(f"❌ Erreur credentials : {e}")
        return

    # ✅ Parse RSS
    feed = feedparser.parse(RSS_URL)
    if not feed.entries:
        logging.warning("⚠️ RSS vide")
        # On soumet quand même le sitemap
        submit_sitemap(credentials)
        return

    # ✅ Collecte des URLs fraîches
    fresh_urls = []
    for entry in feed.entries:
        if len(fresh_urls) >= MAX_URLS_PER_RUN:
            break
        if is_fresh(entry):
            url = entry.link.split('?')[0].split('#')[0].rstrip('/')
            if url not in fresh_urls:
                fresh_urls.append(url)

    logging.info(f"📊 URLs fraîches détectées : {len(fresh_urls)}")

    # ✅ Indexing API (si pas throttlé et articles frais)
    if fresh_urls and not throttling_active:
        sent = submit_to_indexing_api(credentials, fresh_urls)
        if sent > 0:
            update_last_push()
            logging.info(f"✅ {sent} URL(s) soumises à l'Indexing API")
    elif throttling_active:
        logging.info("⏱ Indexing API skippée (throttling)")
    else:
        logging.info("⏱ Aucun article assez récent pour l'Indexing API")

    # ✅ Soumission sitemap (toujours)
    submit_sitemap(credentials)


if __name__ == "__main__":
    run()
