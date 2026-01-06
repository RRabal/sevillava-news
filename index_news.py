import os
import json
import logging
import feedparser
from googleapiclient.discovery import build
from google.oauth2 import service_account

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def index_and_submit_sitemap():
    key_data = os.getenv('GSC_JSON_KEY')
    if not key_data:
        logging.error("La variable GSC_JSON_KEY est vide.")
        return

    try:
        credentials_info = json.loads(key_data)
        
        # --- AJOUT DU SCOPE WEBMASTERS ---
        scopes = [
            "https://www.googleapis.com/auth/indexing",
            "https://www.googleapis.com/auth/webmasters" 
        ]
        
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info, scopes=scopes
        )

        # 1. NOTIFICATION DES URLS (Indexing API)
        idx_service = build('indexing', 'v1', credentials=credentials, static_discovery=False)
        feed = feedparser.parse("https://www.sevillava.fr/blog-feed.xml")
        
        if feed.entries:
            for entry in feed.entries[:2]:
                url = entry.link.split('?')[0]
                body = {"url": url, "type": "URL_UPDATED"}
                idx_service.urlNotifications().publish(body=body).execute()
                logging.info(f"✅ Indexing API : {url}")

        # 2. MISE À JOUR DU SITEMAP (Search Console API)
        # Note : siteUrl doit être identique à la propriété dans GSC (avec / à la fin souvent)
        gsc_service = build('webmasters', 'v3', credentials=credentials, static_discovery=False)
        site_url = "https://www.sevillava.fr/"
        sitemap_url = "https://news.sevillava.fr/newssitemap.xml" # Assurez-vous du nom exact

        gsc_service.sitemaps().submit(
            siteUrl=site_url,
            feedpath=sitemap_url
        ).execute()
        logging.info(f"🚀 Sitemap News soumis avec succès : {sitemap_url}")

    except Exception as e:
        logging.error(f"❌ Erreur : {e}")

if __name__ == "__main__":
    index_and_submit_sitemap()
