import feedparser
from datetime import datetime, timedelta, timezone
import os
import time

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

    for entry in feed.entries:
        # Conversion de la date de l'article en objet datetime conscient du fuseau horaire (UTC)
        try:
            # On transforme le struct_time en timestamp puis en datetime UTC
            published_time = datetime.fromtimestamp(time.mktime(entry.published_parsed), timezone.utc)
        except Exception:
            continue # Si on ne peut pas lire la date, on ignore l'article

        # --- FILTRE : On ne garde que si l'article a moins de 48h ---
        if published_time < limit_date:
            continue 

        url = entry.link
        title = entry.title
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

    os.makedirs(os.path.dirname(SITEMAP_PATH), exist_ok=True)
    with open(SITEMAP_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(sitemap_content))

if __name__ == "__main__":
    generate_news_sitemap()
