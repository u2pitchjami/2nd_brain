from dotenv import load_dotenv
import time
import os
import logging
from handlers.logger_setup import setup_logging

# Chemin dynamique basé sur le script en cours
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, ".env")
# Charger le fichier .env
load_dotenv(env_path)

# Emplacement du fichier log
setup_logging()

from handlers.watcher import start_watcher

if __name__ == "__main__":
    start_watcher()