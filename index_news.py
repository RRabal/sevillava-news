import json
import logging
import os
import feedparser
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Configuration du logging pour voir ce qui se passe dans GitHub Actions
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

RSS_URL = "https://www.sevillava.fr/blog-feed.xml"

def notify_google():
    # 1. Récupérer la clé JSON depuis la variable d'environnement (Secret GitHub)
    service_account_info = os.getenv('GSC_JSON_KEY')
    if not service_account_info:
        logging.error("Le secret GSC_JSON_KEY est vide ou introuvable.")
        return

    try:
        info = json.loads(service_account_info)
        scopes = ["https://www.googleapis.com/auth/indexing"]
        credentials = service_account.Credentials.from_service_account_info(info, scopes=scopes)
        service = build('indexing', 'v3', credentials=credentials)
    except Exception as e:
        logging.error(f"Erreur d'authentification : {e}")
        return

    # 2. Récupérer les derniers articles du flux RSS
    feed = feedparser.parse(RSS_URL)
    
    # On prend les 3 derniers articles pour ne pas saturer les quotas
    for entry in feed.entries[:3]:
        url = entry.link.split('?')[0] # URL propre
        
        body = {
            "url": url,
            "type": "URL_UPDATED"
        }
        
        try:
            response = service.urlNotifications().publish(body=body).execute()
            logging.info(f"Succès ! Google va indexer : {url}")
        except Exception as e:
            logging.error(f"Erreur pour l'URL {url} : {e}")

if __name__ == "__main__":
    notify_google()
