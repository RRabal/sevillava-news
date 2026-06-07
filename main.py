import os
import re
import logging
from xml.sax.saxutils import escape
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

SITEMAP_PATH = "docs/newssitemap.xml"


def url_already_exists(content: str, url: str) -> bool:
    """Vérifie si l'URL est déjà présente dans le sitemap."""
    return f"<loc>{url}</loc>" in content


def add_article_to_sitemap(title: str, url: str, date: str):
    logging.info(f"🚀 Injection article : {title}")

    # ✅ Nettoyage URL
    url = url.split('?')[0].split('#')[0].rstrip('/')

    # ✅ Validation date ISO 8601
    try:
        datetime.fromisoformat(date.replace('Z', '+00:00'))
    except ValueError:
        logging.error(f"❌ Date invalide : {date} → utilisation date courante")
        date = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00')

    title_escaped = escape(title.strip())

    entry = f"""  <url>
    <loc>{url}</loc>
    <lastmod>{date}</lastmod>
    <news:news>
      <news:publication>
        <news:name>Sevilla Va</news:name>
        <news:language>fr</news:language>
      </news:publication>
      <news:publication_date>{date}</news:publication_date>
      <news:title>{title_escaped}</news:title>
    </news:news>
  </url>"""

    # ✅ Création du dossier docs si absent
    os.makedirs("docs", exist_ok=True)

    # ✅ CORRECTION : Désactive Jekyll pour éviter les erreurs de déploiement GitHub Pages
    open("docs/.nojekyll", "a").close()

    # ✅ Création du sitemap si absent
    if not os.path.exists(SITEMAP_PATH):
        logging.info("📄 Création nouveau sitemap")
        with open(SITEMAP_PATH, "w", encoding="utf-8") as f:
            f.write(
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<urlset\n'
                '  xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
                '  xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">\n'
                '</urlset>\n'
            )

    with open(SITEMAP_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # ✅ Dédoublonnage : on n'ajoute pas si URL déjà présente
    if url_already_exists(content, url):
        logging.info(f"⏭️ URL déjà présente dans le sitemap, injection ignorée : {url}")
        return

    # ✅ Insertion avant </urlset>
    content = content.replace("</urlset>", entry + "\n</urlset>")

    with open(SITEMAP_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    logging.info(
