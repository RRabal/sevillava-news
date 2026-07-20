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
    """Lit le sitemap existant pour préserver les entrées injectées."""
    existing = {}
    if not os.path.exists(path):
        return existing
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        import re
        blocks = re.findall(r'<url>.*?</url>', content, re.DOTALL)
        for block in blocks:
            loc_match = re.search(r'<loc>(.*?)</loc>', block)
            if loc_match:
                url = loc_match.group(1).strip()
                existing[url] = block
        logging.info(f"📂 Sitemap existant lu : {len(existing)} entrées")
    except Exception as e:
        logging.warning(f"⚠️ Impossible de lire le sitemap : {e}")
    return existing

def generate_news_sitemap():
    # --- 1. RÉCUPÉRATION DES INPUTS (WIX / GITHUB ACTIONS) ---
    input_title = os.environ.get("INPUT_TITLE", "").strip()
    input_url = os.environ.get("INPUT_URL", "").strip()
    input_date = os.environ.get("INPUT_DATE", "").strip()

    logging.info(f"Lecture RSS : {RSS_URL}")
    feed = feedparser.parse(RSS_URL)
    
    now = datetime.now(timezone.utc)
    limit_date = now - timedelta(hours=MAX_AGE_HOURS)
    existing_entries = parse_existing_sitemap(SITEMAP_PATH)

    seen_urls = set()
    sitemap_entries = []

    # --- 2. INJECTION DE L'ARTICLE REÇU DE WIX (PRIORITÉ) ---
    if input_title and input_url and input_date:
        try:
            # Nettoyage de l'URL
            clean_url = input_url.split('?')[0].split('#')[0].rstrip('/')
            
            # Conversion de la date reçue (doit être ISO)
            pub_date = datetime.fromisoformat(input_date.replace('Z', '+00:00'))
            
            if pub_date > limit_date:
                title_esc = escape(input_title)
                date_iso = pub_date.strftime('%Y-%m-%dT%H:%M:%S+00:00')
                
                logging.info(f"💉 Injection manuelle Wix : {title_esc}")
                
                sitemap_entries.append((pub_date, f"""  <url>
    <loc>{clean_url}</loc>
    <lastmod>{date_iso}</lastmod>
    <news:news>
      <news:publication>
        <news:name>SevillaVa</news:name>
        <news:language>fr</news:language>
      </news:publication>
      <news:publication_date>{date_iso}</news:publication_date>
      <news:title>{title_esc}</news:title>
    </news:news>
  </url>"""))
                seen_urls.add(clean_url)
        except Exception as e:
            logging.error(f"❌ Erreur lors de l'injection manuelle : {e}")

    # --- 3. TRAITEMENT DU FLUX RSS ---
    for entry in feed.entries:
        try:
            if not hasattr(entry, 'published_parsed') or entry.published_parsed is None:
                continue
            timestamp = calendar.timegm(entry.published_parsed)
            published = datetime.fromtimestamp(timestamp, timezone.utc)
            
            if published < limit_date:
                continue

            url = entry.link.split('?')[0].split('#')[0].rstrip('/')
            if url in seen_urls: # Évite les doublons si l'article Wix est déjà dans le RSS
                continue
            
            seen_urls.add(url)
            title = escape(entry.get('title', 'Sans titre').strip())
            date_iso = published.strftime('%Y-%m-%dT%H:%M:%S+00:00')

            sitemap_entries.append((published, f"""  <url>
    <loc>{url}</loc>
    <lastmod>{date_iso}</lastmod>
    <news:news>
      <news:publication>
        <news:name>SevillaVa</news:name>
        <news:language>fr</news:language>
      </news:publication>
      <news:publication_date>{date_iso}</news:publication_date>
      <news:title>{title}</news:title>
    </news:news>
  </url>"""))
        except Exception as e:
            logging.warning(f"⚠️ Erreur parsing RSS entry : {e}")

    # --- 4. RÉCUPÉRATION DES ARTICLES DU SITEMAP PRÉCÉDENT ---
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
                    continue
                seen_urls.add(url)
                sitemap_entries.append((pub_date, f"  {block.strip()}"))
            except:
                continue

    # --- 5. TRI ET GÉNÉRATION FINALE ---
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

    os.makedirs(os.path.dirname(SITEMAP_PATH), exist_ok=True)
    # On s'assure que .nojekyll existe
    with open("docs/.nojekyll", "w") as f: pass

    with open(SITEMAP_PATH, "w", encoding="utf-8") as f:
        f.write(sitemap_content)

    logging.info(f"✅ Sitemap finalisé : {len(entries_xml)} articles.")

if __name__ == "__main__":
    generate_news_sitemap()
