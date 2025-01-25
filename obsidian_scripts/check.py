from handlers.files import load_excluded_patterns
import time
import logging
from handlers.check_categ import verify_and_correct_category

logger = logging.getLogger(__name__)

base_path = os.getenv('BASE_PATH')

# Dossiers à scanner
directories = base_path

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