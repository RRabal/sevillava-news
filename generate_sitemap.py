import feedparser
from datetime import datetime, timedelta, timezone
import os
from xml.sax.saxutils import escape
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

RSS_URL = "https://www.sevillava.fr/blog-feed.xml"
SITEMAP_PATH = "docs/newssitemap.xml"

# ✅ Google News accepte jusqu'à 48h (on garde 47h de marge)
MAX_AGE_HOURS = 47


def generate_news_sitemap():
    logging.info(f"Lecture RSS : {RSS_URL}")
    feed = feedparser.parse(RSS_URL)

    if feed.bozo:
        logging.warning(f"⚠️ RSS potentiellement mal formé : {feed.bozo_exception}")

    if not feed.entries:
        logging.error("❌ RSS vide ou inaccessible")
        return

    now = datetime.now(timezone.utc)
    limit_date = now - timedelta(hours=MAX_AGE_HOURS)

    seen_urls = set()
    sitemap_entries = []
    skipped = 0

    for entry in feed.entries:
        # ✅ Gestion robuste de la date (published_parsed peut être None)
        try:
            if not hasattr(entry, 'published_parsed') or entry.published_parsed is None:
                logging.warning(f"⚠️ Pas de date pour : {entry.get('link', 'URL inconnue')}")
                continue

            time_tuple = entry.published_parsed
            # feedparser retourne un time.struct_time à 9 éléments
            # mktime_tz gère le timezone offset (10ème élément)
            timestamp = feedparser.mktime_tz(time_tuple)
            if timestamp is None:
                continue

            published = datetime.fromtimestamp(timestamp, timezone.utc)

        except Exception as e:
            logging.warning(f"⚠️ Erreur parsing date : {e}")
            continue

        # ✅ Filtre temporel
        if published < limit_date:
            skipped += 1
            continue

        # ✅ Nettoyage URL (supprime query params et fragments)
        url = entry.link.split('?')[0].split('#')[0].rstrip('/')

        # ✅ Validation URL basique
        if not url.startswith('https://'):
            logging.warning(f"⚠️ URL ignorée (non HTTPS) : {url}")
            continue

        if url in seen_urls:
            continue
        seen_urls.add(url)

        # ✅ Escape complet du titre
        title = escape(entry.get('title', 'Sans titre').strip())
        date_iso = published.strftime('%Y-%m-%dT%H:%M:%S+00:00')

        sitemap_entries.append(f"""  <url>
    <loc>{url}</loc>
    <lastmod>{date_iso}</lastmod>
    <news:news>
      <news:publication>
        <news:name>Sevilla Va</news:name>
        <news:language>fr</news:language>
      </news:publication>
      <news:publication_date>{date_iso}</news:publication_date>
      <news:title>{title}</news:title>
    </news:news>
  </url>""")

    logging.info(f"📊 Articles inclus : {len(sitemap_entries)} | Ignorés (trop anciens) : {skipped}")

    if not sitemap_entries:
        logging.warning("⚠️ Aucun article récent → sitemap vide généré quand même")

    sitemap_content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset\n'
        '  xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
        '  xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">\n'
        + '\n'.join(sitemap_entries) + '\n'
        '</urlset>\n'
    )

    os.makedirs(os.path.dirname(SITEMAP_PATH), exist_ok=True)

    with open(SITEMAP_PATH, "w", encoding="utf-8") as f:
        f.write(sitemap_content)

    logging.info(f"✅ Sitemap écrit : {SITEMAP_PATH} ({len(sitemap_entries)} articles)")


if __name__ == "__main__":
    generate_news_sitemap()
