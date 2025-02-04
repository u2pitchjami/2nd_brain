# pylint: disable=C0413
import os
import sys
from dotenv import load_dotenv

# Chemin dynamique basé sur le script en cours
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, ".env")
# Charger le fichier .env
load_dotenv(env_path)
base_script = os.getenv('BASE_SCRIPT')
sys.path.append(os.path.abspath(base_script))
from handlers.start.watcher import start_watcher
from handlers.logger_setup import setup_logging
# Emplacement du fichier log
setup_logging()

if __name__ == "__main__":
    start_watcher()
