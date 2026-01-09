import logging
from generator import generate_news_sitemap
from indexer import index_and_submit_sitemap

# Configuration unique du logging pour le workflow
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')

def run_workflow():
    logging.info("--- DÉBUT DU WORKFLOW SEO ---")
    
    try:
        # Étape 1 : Génération du fichier XML
        logging.info("Étape 1 : Génération du News Sitemap...")
        generate_news_sitemap()
        
        # Étape 2 : Soumission à Google
        # On ne lance l'étape 2 que si l'étape 1 a réussi
        logging.info("Étape 2 : Notification Google (Indexing + GSC)...")
        index_and_submit_sitemap()
        
        logging.info("--- WORKFLOW TERMINÉ AVEC SUCCÈS ---")
        
    except Exception as e:
        logging.error(f"Le workflow a échoué : {e}")

if __name__ == "__main__":
    run_workflow()
