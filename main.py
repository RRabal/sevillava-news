import logging
# Noms corrigés ici :
from generate_sitemap import generate_news_sitemap
from index_news import index_and_submit_sitemap

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')

def run_workflow():
    logging.info("--- DÉBUT DU WORKFLOW SEO ---")
    try:
        logging.info("Étape 1 : Génération du News Sitemap...")
        generate_news_sitemap()
        
        logging.info("Étape 2 : Notification Google (Indexing + GSC)...")
        index_and_submit_sitemap()
        
        logging.info("--- WORKFLOW TERMINÉ AVEC SUCCÈS ---")
    except Exception as e:
        logging.error(f"Le workflow a échoué : {e}")
        raise e 

if __name__ == "__main__":
    run_workflow()
