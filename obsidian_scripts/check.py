from dotenv import load_dotenv
import time
import logging
import os
logger = logging.getLogger(__name__)

# Chemin dynamique basé sur le script en cours
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, ".env")
# Charger le fichier .env
load_dotenv(env_path)

from handlers.files import load_excluded_patterns
from handlers.files import get_recently_modified_files
from handlers.check_categ import verify_and_correct_category

base_path = os.getenv('BASE_PATH')
# Dossiers à scanner
#directories = base_path

directories = [
        base_path
    ]

print (f"directories {directories}")
# Temps seuil : 1 heure (3600 secondes)
time_threshold = 3600

# Charger les patterns d'exclusion depuis un fichier texte
exclude_file = os.getenv('EXCLUDE_FILE')
excluded_patterns = load_excluded_patterns(exclude_file)
# Récupérer les fichiers modifiés récemment
recent_files = get_recently_modified_files(directories, time_threshold, excluded_patterns)
# Afficher les fichiers trouvés
print(f"Fichiers modifiés récemment (dans les {time_threshold // 60} minutes) :")
for file in recent_files:
    print(file)
    verify_and_correct_category(file)