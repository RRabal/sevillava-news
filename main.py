import os
import logging
from xml.sax.saxutils import escape
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

SITEMAP_PATH = "docs/newssitemap.xml"


def add_article_to_sitemap(title, url, date):
    logging.info("🚀 Ajout de l'article au sitemap")

    title = escape(title)

    entry = f"""
  <url>
    <loc>{url}</loc>
    <lastmod>{date}</lastmod>
    <news:news>
      <news:publication>
        <news:name>Sevilla Va</news:name>
        <news:language>fr</news:language>
      </news:publication>
      <news:publication_date>{date}</news:publication_date>
      <news:title>{title}</news:title>
    </news:news>
  </url>
"""

    os.makedirs("docs", exist_ok=True)

    # Si sitemap n'existe pas encore → création propre
    if not os.path.exists(SITEMAP_PATH):
        logging.info("📄 Création nouveau sitemap")
        with open(SITEMAP_PATH, "w", encoding="utf-8") as f:
            f.write("""<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">\n</urlset>""")

    # Lecture sitemap existant
    with open(SITEMAP_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Ajout nouvel article avant </urlset>
    content = content.replace("</urlset>", entry + "\n</urlset>")

    with open(SITEMAP_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    logging.info("✅ Sitemap mis à jour avec succès")


def run_workflow():
    title = os.environ.get("INPUT_TITLE")
    url = os.environ.get("INPUT_URL")
    date = os.environ.get("INPUT_DATE")

    logging.info("🔎 Lecture des inputs GitHub Actions")

    # Mode fallback si workflow cron (sans inputs)
    if not title or not url or not date:
        logging.warning("⚠️ Mode fallback (cron ou push main) → aucun article injecté")
        return

    logging.info(f"📰 Article reçu : {title}")

    add_article_to_sitemap(title, url, date)

    logging.info("🎯 Workflow terminé")


if __name__ == "__main__":
    run_workflow()
