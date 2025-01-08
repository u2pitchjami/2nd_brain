import sqlite3
import json

# Connexion à la base SQLite de Hoarder
db_path = "/mnt/user/Documents/hoarder/db.db"  # Chemin vers ta base SQLite
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Requête pour trouver les signets sans résumé
query = "SELECT id FROM bookmarks WHERE summary IS NULL;"
cursor.execute(query)

# Récupération des résultats
bookmarks = cursor.fetchall()

# Affichage ou traitement des résultats
for bookmark in bookmarks:
    print(bookmark)

# Export en JSON si nécessaire
with open("bookmarks_without_summary.json", "w") as f:
    json.dump(bookmarks, f, indent=4)

# Fermer la connexion
conn.close()
