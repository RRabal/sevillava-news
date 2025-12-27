import feedparser
from datetime import datetime
import os

RSS_URL = "https://www.sevillava.fr/blog-feed.xml"
SITEMAP_PATH = "docs/newssitemap.xml"

def generate_news_sitemap():
    feed = feedparser.parse(RSS_URL)
    
    # En-tête avec les namespaces spécifiques à Google News
    sitemap_content = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" ',
        '        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">',
    ]

    for entry in feed.entries:
        url = entry.link
        title = entry.title
        
        # Gestion de la date au format ISO 8601 (obligatoire pour Google News)
        try:
            date_str = datetime(*entry.published_parsed[:6]).strftime('%Y-%m-%dT%H:%M:%S+00:00')
        except:
            date_str = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+00:00')

        # Structure spécifique Google News
        item = [
            "  <url>",
            f"    <loc>{url}</loc>",
            "    <news:news>",
            "      <news:publication>",
            "        <news:name>Sevilla Va</news:name>", # Nom de votre site
            "        <news:language>fr</news:language>",
            "      </news:publication>",
            f"      <news:publication_date>{date_str}</news:publication_date>",
            f"      <news:title>{title}</news:title>",
            "    </news:news>",
            "  </url>"
        ]
        sitemap_content.extend(item)

    sitemap_content.append('</urlset>')

    # Création du dossier si besoin
    os.makedirs(os.path.dirname(SITEMAP_PATH), exist_ok=True)

    with open(SITEMAP_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(sitemap_content))

if __name__ == "__main__":
    generate_news_sitemap()
