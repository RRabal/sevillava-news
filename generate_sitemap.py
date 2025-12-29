import feedparser
from datetime import datetime, timedelta, timezone
import os
import time
from xml.sax.saxutils import escape

RSS_URL = "https://www.sevillava.fr/blog-feed.xml"
SITEMAP_PATH = "docs/newssitemap.xml"

def generate_news_sitemap():
    feed = feedparser.parse(RSS_URL)
    
    # Seuil de 48 heures
    now = datetime.now(timezone.utc)
    limit_date = now - timedelta(hours=48)

    sitemap_content = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" ',
        '        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">',
    ]

    for entry in feed.entries[:1000]:  # max 1000 URLs par sitemap
        # Conversion de la date de l'article en objet datetime UTC
        try:
            published_time = datetime.fromtimestamp(time.mktime(entry.published_parsed), timezone.utc)
        except Exception:
            continue  # Si la date est invalide, on ignore l'article

        # --- FILTRE : articles publiés dans les 48 dernières heures ---
        if published_time < limit_
