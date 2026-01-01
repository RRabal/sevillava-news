import os
import json
import logging
import feedparser
from googleapiclient.discovery import build
from google.oauth2 import service_account

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def index_new_urls():
    # 1. Récupérer la clé depuis les secrets GitHub
    key_data = os.getenv('GSC_JSON_KEY')
    if not key_data:
        logging.error("La variable GSC_JSON_KEY est vide ou introuvable.")
        return

    try:
        # 2. Authentification
        scopes = ["https://www.googleapis.com/auth/indexing"]
        credentials_info = json.loads(key_data)
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info, scopes=scopes
        )
        
        # 3. Construction du service avec static_discovery=False (Correction de l'erreur)
        service = build('indexing', 'v1', credentials=credentials, static_discovery=False)
        
        # 4. Récupérer l'URL à indexer depuis le flux RSS
        feed = feedparser.parse("https://www.sevillava.fr/blog-feed.xml")
        if not feed.entries:
            logging.warning("Aucun article trouvé dans le flux RSS.")
            return

        # On prend les 2 derniers articles pour être sûr
        for entry in feed.entries[:2]:
            url = entry.link.split('?')[0]
            body = {"url": url, "type": "URL_UPDATED"}
            
            try:
                service.urlNotifications().publish(body=body).execute()
                logging.info(f"✅ Notification envoyée avec succès pour : {url}")
            except Exception as e:
                logging.error(f"❌ Erreur Google Indexing pour {url} : {e}")

    except Exception as e:
        logging.error(f"❌ Erreur critique : {e}")

if __name__ == "__main__":
    index_new_urls()
