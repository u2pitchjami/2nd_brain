import logging
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from dotenv import load_dotenv

if not os.getenv('LOG_DIR'):  # 🔥 Charger .env seulement si LOG_DIR n'est pas défini
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, "..", ".env")  # Remonte d'un dossier si nécessaire
    load_dotenv(env_path)



logger = logging.getLogger()

def setup_logging():
    # Déterminer le chemin du fichier log basé sur la date
    log_dir = os.getenv('LOG_DIR', './logs')  # Valeur par défaut
    log_name = os.getenv('LOG_NAME', 'app')   # Valeur par défaut
    
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, f"{log_name}.log")  # Pas de date dans le nom
    # Configurer le logger principal
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Supprimer les handlers existants (évite duplication si setup_logging est rappelé)
    if logger.hasHandlers():
        logger.handlers.clear()

    # 🔥 Utiliser un TimedRotatingFileHandler pour créer un nouveau fichier chaque jour
    file_handler = TimedRotatingFileHandler(log_file, when="midnight", interval=1, backupCount=7, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.suffix = "%Y-%m-%d"  # Ajoute automatiquement la date aux fichiers archivés
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Ajouter un StreamHandler pour afficher les logs dans la console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
logging.getLogger().setLevel(logging.DEBUG)  # 🔥 S'assurer que tout est bien en DEBUG
