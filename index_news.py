import os
import json
import logging
from googleapiclient.discovery import build
from google.oauth2 import service_account

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def index_and_submit_sitemap():
    key_data = os.getenv('GSC_JSON_KEY')

    if not key_data:
        logging.error("GSC_JSON_KEY manquant")
        return

    try:
        credentials_info = json.loads(key_data)

        credentials = service_account.Credentials.from_service_account_info(
            credentials_info,
            scopes=["https://www.googleapis.com/auth/webmasters"]
        )

        service = build('webmasters', 'v3', credentials=credentials, static_discovery=False)

        site_url = "https://www.sevillava.fr/"
        sitemap_url = "https://www.sevillava.fr/newssitemap.xml"

        service.sitemaps().submit(
            siteUrl=site_url,
            feedpath=sitemap_url
        ).execute()

        logging.info(f"Sitemap soumis : {sitemap_url}")

    except Exception as e:
        logging.error(f"Erreur : {e}")


if __name__ == "__main__":
    index_and_submit_sitemap()
