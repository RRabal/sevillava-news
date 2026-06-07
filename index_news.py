import os
import json
import logging
import feedparser
from googleapiclient.discovery import build
from google.oauth2 import service_account

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

RSS_URL = "https://www.sevillava.fr/blog-feed.xml"

def run():
    key_data = os.getenv('GSC_JSON_KEY')

    if not key_data:
        logging.error("GSC_JSON_KEY manquant")
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

        # 🔥 INDEXING API (ULTRA FAST)
        idx_service = build('indexing', 'v1', credentials=credentials, static_discovery=False)

        feed = feedparser.parse(RSS_URL)

        if feed.entries:
            latest = feed.entries[0]  # le plus récent
            url = latest.link.split('?')[0]

            body = {
                "url": url,
                "type": "URL_UPDATED"
            }

            idx_service.urlNotifications().publish(body=body).execute()
            logging.info(f"⚡ Indexing API envoyé : {url}")

        # ✅ SEARCH CONSOLE
        gsc_service = build('webmasters', 'v3', credentials=credentials, static_discovery=False)

        site_url = "https://www.sevillava.fr/"
        sitemap_url = "https://www.sevillava.fr/newssitemap.xml"

        gsc_service.sitemaps().submit(
            siteUrl=site_url,
            feedpath=sitemap_url
        ).execute()

        logging.info("✅ Sitemap soumis GSC")

    except Exception as e:
        logging.error(f"❌ Erreur : {e}")


if __name__ == "__main__":
    run()
