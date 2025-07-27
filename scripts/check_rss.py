import feedparser
import os

rss_url = "https://www.sevillava.fr/blog-feed.xml"  # ➤ Remplace par l'URL réelle de ton blog Wix
feed = feedparser.parse(rss_url)

# Dernier article
latest_post = feed.entries[0].link.strip()

# Vérifier si fichier existe
latest_path = "sevillava-news/data/latest.txt"
if os.path.exists(latest_path):
    with open(latest_path, "r") as f:
        last_saved = f.read().strip()
else:
    last_saved = ""

# Comparer et agir
if latest_post != last_saved:
    print(f"🆕 Nouveau post détecté ! → {latest_post}")
    with open(latest_path, "w") as f:
        f.write(latest_post)
    # Tu peux ajouter ici une autre action (ex: commit, tweet, etc.)
else:
    print("⏳ Pas de nouveau post.")
