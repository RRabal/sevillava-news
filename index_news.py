import os
import json
import logging
import sys

from googleapiclient.discovery import build
from google.oauth2 import service_account


# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)


# Propriété Search Console
SITE_URL = "sc-domain:sevillava.fr"

# Nouveau News Sitemap généré automatiquement par Wix Velo
SITEMAP_URL = "https://www.sevillava.fr/_functions/newssitemap"


# Autorisation Search Console uniquement
SCOPES = [
    "https://www.googleapis.com/auth/webmasters"
]


def get_credentials(key_data: str):
    credentials_info = json.loads(key_data)

    return service_account.Credentials.from_service_account_info(
        credentials_info,
        scopes=SCOPES
    )


def submit_sitemap(credentials):
    """Soumet le News Sitemap Velo à Google Search Console."""

    service = build(
        "searchconsole",
        "v1",
        credentials=credentials,
        static_discovery=False
    )

    service.sitemaps().submit(
        siteUrl=SITE_URL,
        feedpath=SITEMAP_URL
    ).execute()

    logging.info(
        f"✅ News Sitemap soumis à Search Console : {SITEMAP_URL}"
    )


def run():

    key_data = os.getenv("GSC_JSON_KEY")

    if not key_data:
        logging.error("❌ Variable GSC_JSON_KEY manquante")
        sys.exit(1)

    try:

        credentials = get_credentials(key_data)

        submit_sitemap(credentials)

    except Exception as e:

        logging.error(
            f"❌ Erreur lors de la soumission Search Console : {e}"
        )

        sys.exit(1)


if __name__ == "__main__":
    run()
