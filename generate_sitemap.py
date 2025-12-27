import feedparser
from datetime import datetime
import os

RSS_URL = "https://www.sevillava.fr/blog-feed.xml"
# Chemin précis vers votre fichier dans le dépôt
SITEMAP_PATH = "docs/newssitemap.xml"

def generate_sitemap():
    feed = feedparser.parse(RSS_URL)
    
    sitemap_content = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]

    for entry in feed.entries:
        url = entry.link
        try:
            # Formatage de la date pour Google (YYYY-MM-DD)
            date_str = datetime(*entry.published_parsed[:6]).strftime('%Y-%m-%d')
            lastmod = f"    <lastmod>{date_str}</lastmod>"
        except:
            lastmod = ""

        item = [
            "  <url>",
            f"    <loc>{url}</loc>",
            lastmod,
            "  </url>"
        ]
        sitemap_content.extend([line for line in item if line.strip()])

    sitemap_content.append('</urlset>')

    # Créer le dossier docs s'il n'existe pas (sécurité)
    os.makedirs(os.path.dirname(SITEMAP_PATH), exist_ok=True)

    with open(SITEMAP_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(sitemap_content))

if __name__ == "__main__":
    generate_sitemap()
