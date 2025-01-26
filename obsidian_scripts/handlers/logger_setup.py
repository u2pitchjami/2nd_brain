import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

def setup_logging():
    # Déterminer le chemin du fichier log basé sur la date
    log_dir = os.getenv('LOG_DIR')
    log_name = os.getenv('LOG_NAME')
    
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    current_date = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"{current_date}_{log_name}.log")

    # Configurer le logger principal
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Ajouter un FileHandler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Ajouter un StreamHandler pour afficher les logs dans la console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger