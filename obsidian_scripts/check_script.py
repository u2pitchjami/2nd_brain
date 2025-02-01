# pylint: disable=C0413
import os
import logging
from dotenv import load_dotenv


# Chemin dynamique basé sur le script en cours
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, ".env")
# Charger le fichier .env
load_dotenv(env_path)
from handlers.logger_setup import setup_logging # noqa: C0413
setup_logging()
from handlers.utils.files import load_excluded_patterns # noqa: C0413
from handlers.utils.files import get_recently_modified_files # noqa: C0413
from handlers.standalone.process_project import scan_notes_and_update_projects # noqa: C0413
from handlers.standalone.check_categ import verify_and_correct_category # noqa: C0413

base_path = os.getenv('BASE_PATH')
# Dossiers à scanner
directories = base_path

directories = [
        base_path
    ]


# Temps seuil : 1 heure (3600 secondes)
time_threshold = 3600

# Charger les patterns d'exclusion depuis un fichier texte
exclude_file = os.getenv('EXCLUDE_FILE')
excluded_patterns = load_excluded_patterns(exclude_file)
# Récupérer les fichiers modifiés récemment
recent_files = get_recently_modified_files(directories, time_threshold, excluded_patterns)
logging.debug("[DEBUG] Check Script recent_files : %s", recent_files)
# Afficher les fichiers trouvés
logging.info("[INFO] Fichiers modifiés récemment (dans les %d minutes) :", time_threshold // 60)
for file in recent_files:
    logging.info("[INFO] %s :", file)
    verify_and_correct_category(file)
    scan_notes_and_update_projects(file)
