from handlers.files import load_excluded_patterns
from handlers.files import get_recently_modified_files
import time
import logging
from handlers.check_categ import verify_and_correct_category

logger = logging.getLogger(__name__)

  # Emplacement du fichier log
logging.basicConfig(filename='/home/pipo/bin/dev/2nd_brain/obsidian_scripts/logs/auto_tags.log', level=logging.DEBUG, format='%(asctime)s - %(message)s')

# Dossiers à scanner
directories = [
    "/mnt/user/Documents/Obsidian/notes"
]

# Temps seuil : 1 heure (3600 secondes)
time_threshold = 3600

# Charger les patterns d'exclusion depuis un fichier texte
exclude_file = "/home/pipo/bin/dev/2nd_brain/obsidian_scripts/handlers/exclude_dirs.txt"
excluded_patterns = load_excluded_patterns(exclude_file)

# Récupérer les fichiers modifiés récemment
recent_files = get_recently_modified_files(directories, time_threshold, excluded_patterns)

# Afficher les fichiers trouvés
print(f"Fichiers modifiés récemment (dans les {time_threshold // 60} minutes) :")
for file in recent_files:
    print(file)
    verify_and_correct_category(file)