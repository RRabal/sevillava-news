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

    # Google News limite à 1000 URLs par sitemap news
    for entry in feed.entries[:1000]:
        try:
            # Conversion de la date de l'article en datetime UTC
            published_time = datetime.fromtimestamp(time.mktime(entry.published_parsed), timezone.utc)
        except Exception:
            continue

        # --- FILTRE : Uniquement les articles de moins de 48h ---
        if published_time >= limit_date:
            url = entry.link
            # escape() permet de gérer les caractères comme & ou < dans les titres
            title = escape(entry.title)
            date_iso = published_time.strftime('%Y-%m-%dT%H:%M:%S+00:00')

            item = [
                "  <url>",
                f"    <loc>{url}</loc>",
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

    sitemap_content.append('</urlset>')

    # Création du dossier docs si inexistant
    os.makedirs(os.path.dirname(SITEMAP_PATH), exist_ok=True)

    with open(SITEMAP_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(sitemap_content))

if __name__ == "__main__":
    generate_news_sitemap()
