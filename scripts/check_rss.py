import feedparser
import os
from datetime import datetime

rss_url = "https://www.sevillava.fr/blog-feed.xml"
sitemap_file = "newssitemap.xml"
last_seen_file = "last_seen.txt"

def get_last_seen():
    if os.path.exists(last_seen_file):
        with open(last_seen_file, "r") as f:
            return f.read().strip()
    return None

def save_last_seen(link):
    with open(last_seen_file, "w") as f:
        f.write(link)

def generate_sitemap(entry):
    pub_date = datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%dT%H:%M:%SZ")
    sitemap = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">
  <url>
    <loc>{entry.link}</loc>
    <news:news>
      <news:publication>
        <news:name>Sevillava News</news:name>
        <news:language>fr</news:language>
      </news:publication>
      <news:publication_date>{pub_date}</news:publication_date>
      <news:title>{entry.title}</news:title>
    </news:news>
  </url>
</urlset>'''
    with open(sitemap_file, "w", encoding="utf-8") as f:
        f.write(sitemap)

def main():
    feed = feedparser.parse(rss_url)
    latest = feed.entries[0]
    latest_link = latest.link

    last_seen = get_last_seen()

    if latest_link != last_seen:
        print(f"🆕 Nouvel article détecté : {latest.title}")
        generate_sitemap(latest)
        save_last_seen(latest_link)
        print(f"🗺️ Sitemap news mis à jour → {sitemap_file}")
    else:
        print("⏳ Aucun nouvel article.")

if __name__ == "__main__":
    main()
