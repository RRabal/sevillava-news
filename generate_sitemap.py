import xml.etree.ElementTree as ET
import feedparser

# Charger le flux RSS Wix
feed = feedparser.parse('feed.xml')

# Créer la structure du sitemap
urlset = ET.Element('urlset', xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")

for entry in feed.entries:
    url = ET.SubElement(urlset, 'url')
    loc = ET.SubElement(url, 'loc')
    loc.text = entry.link
    lastmod = ET.SubElement(url, 'lastmod')
    lastmod.text = entry.published  # date du flux RSS

# Sauvegarder le sitemap dans docs/
tree = ET.ElementTree(urlset)
tree.write('docs/newssitemap.xml', encoding='utf-8', xml_declaration=True)
