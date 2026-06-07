import feedparser
import calendar
from datetime import datetime, timedelta, timezone
import os
from xml.sax.saxutils import escape
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

RSS_URL = "https://www.sevillava.fr/blog-feed.xml"
SITEMAP_PATH = "docs/newssitemap.xml"
MAX_AGE_HOURS = 47


def parse_existing_sitemap(path: str) -> dict:
    """
    Lit le sitemap existant et retourne un dict {url: entry_xml_block}.
    Permet de préserver les articles déjà présents (injectés via Wix).
    """
    existing = {}
    if not os.path.exists(path):
        return existing

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extraction brute des blocs <url>...</url>
        import re
        blocks = re.findall(r'<url>.*?</url>', content, re.DOTALL)
        for block in blocks:
            loc_match = re.search(r'<loc>(.*?)</loc>', block)
            if loc_match:
                url = loc_match.group(1).strip()
                existing[url] = block
        logging.info(f"📂 Sitemap existant lu : {len(existing)} entrées")
    except Exception as e:
        logging.warning(f"⚠️ Impossible de lire le sitemap existant : {e}")

    return existing


def generate_news_sitemap():
    logging.info(f"Lecture RSS : {RSS_URL}")
    feed = feedparser.parse(RSS_URL)

    if not feed.entries:
        logging.error("❌ RSS vide ou inaccessible")
        return

    now = datetime.now(timezone.utc)
    limit_date = now - timedelta(hours=MAX_AGE_HOURS)

    # ✅ Lecture du sitemap existant pour préserver les entrées injectées
    existing_entries = parse_existing_sitemap(SITEMAP_PATH)

    seen_urls = set()
    sitemap_entries = []

    # ✅ Traitement du flux RSS
    for entry in feed.entries:
        try:
            if not hasattr(entry, 'published_parsed') or entry.published_parsed is None:
                continue

            timestamp = calendar.timegm(entry.published_parsed)
            published = datetime.fromtimestamp(timestamp, timezone.utc)

        except Exception as e:
            logging.warning(f"⚠️ Erreur parsing date : {e}")
            continue

        if published < limit_date:
            continue

        url = entry.link.split('?')[0].split('#')[0].rstrip('/')
        if url in seen_urls:
            continue
        seen_urls.add(url)

        title = escape(entry.get('title', 'Sans titre').strip())
        date_iso = published.strftime('%Y-%m-%dT%H:%M:%S+00:00')

        sitemap_entries.append((published, f"""  <url>
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
  </url>"""))

    # ✅ Ajout des entrées du sitemap existant NON présentes dans le RSS
    import re
    for url, block in existing_entries.items():
        if url in seen_urls:
            continue

        date_match = re.search(r'<news:publication_date>(.*?)</news:publication_date>', block)
        if date_match:
            try:
                date_str = date_match.group(1).strip()
                pub_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                if pub_date < limit_date:
                    logging.info(f"🗑️ Entrée expirée ignorée : {url}")
                    continue
                seen_urls.add(url)
                logging.info(f"♻️ Entrée préservée depuis sitemap existant : {url}")
                sitemap_entries.append((pub_date, f"  {block.strip()}"))
            except Exception as e:
                logging.warning(f"⚠️ Impossible de parser la date de {url} : {e}")
                continue
        else:
            logging.warning(f"⚠️ Pas de date trouvée pour {url}, entrée ignorée")

    # ✅ Tri par date décroissante
    sitemap_entries.sort(key=lambda x: x[0], reverse=True)
    entries_xml = [xml for _, xml in sitemap_entries]

    sitemap_content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset\n'
        '  xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
        '  xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">\n'
        + '\n'.join(entries_xml) + '\n'
        '</urlset>\n'
    )

    # ✅ Création du dossier et désactivation de Jekyll
    os.makedirs(os.path.dirname(SITEMAP_PATH), exist_ok=True)
    open("docs/.nojekyll", "a").close() # Empêche l'erreur de build Jekyll

    with open(SITEMAP_PATH, "w", encoding="utf-8") as f:
        f.write(sitemap_content)

    logging.info(f"✅ Sitemap écrit : {SITEMAP_PATH} ({len(entries_xml)} articles)")


if __name__ == "__main__":
    generate_news_sitemap()
