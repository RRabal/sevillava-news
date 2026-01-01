import os
import json
import logging
import feedparser
from googleapiclient.discovery import build
from google.oauth2 import service_account

logging.basicConfig(level=logging.INFO)

def index_new_urls():
    # 1. Récupérer la clé depuis les secrets GitHub
    key_data = os.getenv('GSC_JSON_KEY')
    if not key_data:
        logging.error("La variable GSC_JSON_KEY est vide !")
        return

    # 2. Authentification
    scopes = ["https://www.googleapis.com/auth/indexing"]
    credentials_info = json.loads(key_data)
    credentials = service_account.Credentials.from_service_account_info(
        credentials_info, scopes=scopes
    )
    service = build('indexing', 'v1', credentials=credentials)

    # 3. Récupérer l'URL à indexer (on reprend le flux RSS pour avoir l'URL exacte)
    feed = feedparser.parse("https://www.sevillava.fr/blog-feed.xml")
    if not feed.entries:
        return

    # On indexe l'article le plus récent
    latest_url = feed.entries[0].link.split('?')[0]
    
    body = {"url": latest_url, "type": "URL_UPDATED"}
    try:
        service.urlNotifications().publish(body=body).execute()
        logging.info(f"Notification envoyée à Google pour : {latest_url}")
    except Exception as e:
        logging.error(f"Erreur Indexing API : {e}")

if __name__ == "__main__":
    index_new_urls()
