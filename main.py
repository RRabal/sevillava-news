import os
import logging
from xml.sax.saxutils import escape

logging.basicConfig(level=logging.INFO)

SITEMAP_PATH = "docs/newssitemap.xml"

def run_workflow():
    title = os.environ.get("INPUT_TITLE")
    url = os.environ.get("INPUT_URL")
    date = os.environ.get("INPUT_DATE")

    logging.info("🚀 Ajout article au sitemap")

    if not title or not url:
        raise Exception("Données article manquantes")

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

    if not os.path.exists(SITEMAP_PATH):
        with open(SITEMAP_PATH, "w") as f:
            f.write("""<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">\n</urlset>""")

    with open(SITEMAP_PATH, "r") as f:
        content = f.read()

    content = content.replace("</urlset>", entry + "\n</urlset>")

    with open(SITEMAP_PATH, "w") as f:
        f.write(content)

    logging.info("✅ Sitemap mis à jour")

if __name__ == "__main__":
    run_workflow()
