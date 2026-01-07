import feedparser
from datetime import datetime, timedelta, timezone
import os
import time
from xml.sax.saxutils import escape
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

RSS_URL = "https://www.sevillava.fr/blog-feed.xml"
SITEMAP_PATH = "newssitemap.xml"

def generate_news_sitemap():
    logging.info(f"Lecture du flux RSS : {RSS_URL}")
    feed = feedparser.parse(RSS_URL)
    
    if feed.bozo:
        logging.warning("Le flux RSS semble avoir des problèmes de format, mais on continue...")

    now = datetime.now(timezone.utc)
    limit_date = now - timedelta(hours=48)

    sitemap_content = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" ',
        '        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">',
    ]

    count = 0
    for entry in feed.entries[:1000]:
        try:
            published_time = datetime.fromtimestamp(time.mktime(entry.published_parsed), timezone.utc)
        except Exception:
            continue

        if published_time >= limit_date:
            # Nettoyage de l'URL (enlève les paramètres ?utm...)
            url = entry.link.split('?')[0]
            title = escape(entry.title)
            date_iso = published_time.strftime('%Y-%m-%dT%H:%M:%S+00:00')

            item = [
                "  <url>",
                f"    <loc>{url}</loc>",
                f"    <lastmod>{date_iso}</lastmod>",
                "    <news:news>",
                "      <news:publication>",
                "        <news:name>Sevilla Va</news:name>",
                "        <news:language>fr</news:language>",
                "      </news:publication>",
                f"      <news:publication_date>{date_iso}</news:publication_date>",
                f"      <news:title>{title}</news:title>",
                "    </news:news>",
                "  </url>"
            ]
            sitemap_content.extend(item)
            count += 1

    sitemap_content.append('</urlset>')
    
    os.makedirs(os.path.dirname(SITEMAP_PATH), exist_ok=True)
    with open(SITEMAP_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(sitemap_content))
    
    logging.info(f"Sitemap généré avec {count} articles récents.")

if __name__ == "__main__":
    generate_news_sitemap()
