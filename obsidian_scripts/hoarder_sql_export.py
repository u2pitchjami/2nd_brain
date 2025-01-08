import sqlite3
import time
from datetime import datetime

# Configuration
DB_PATH = '/mnt/user/appdata/hoarder/db.db'  # Remplacer par le bon chemin
BASE_URL = 'http://192.168.50.12:3000/dashboard/preview/'
EXPORT_PATH = '/mnt/user/Documents/Obsidian/notes/imports/hoarder_bookmarks.md'  # Chemin vers l'export

# Connexion à la base de données
def connect_db(db_path):
    return sqlite3.connect(f"file:{db_path}?mode=rwc", uri=True)

# Requête pour récupérer les signets récents
def get_recent_bookmarks(conn, limit=20):
    cursor = conn.cursor()
    query = """
    SELECT id, title, crawledAt
    FROM bookmarkLinks
    WHERE import_obsidian = 'NO'
    ORDER BY crawledAt DESC
    LIMIT ?;
    """
    cursor.execute(query, (limit,))
    return cursor.fetchall()
# Conversion du timestamp en date lisible
def convert_timestamp(timestamp):
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

# Génération des URLs de prévisualisation + Export Markdown
def generate_urls(bookmarks, conn):
    urls = []
    try:
        with open(EXPORT_PATH, "w") as f:
            f.write("# Signets Hoarder Récents\n\n")
            for bookmark in bookmarks:
                bookmark_id, title, date = bookmark
                readable_date = convert_timestamp(date)
                url = f"{BASE_URL}{bookmark_id}"
                entry = f"## {title}\n- Date: {readable_date}\n- [Voir dans Hoarder]({url})\n\n"
                urls.append(entry)
                f.write(entry)
                
                # Marquer comme importé avec la même connexion
                mark_as_imported(conn, bookmark_id)
    except Exception as e:
        print(f"[ERREUR] Impossible d'écrire le fichier d'export : {e}")
    
    return urls

 
def mark_as_imported(conn, bookmark_id):
    cursor = conn.cursor()
    query = "UPDATE bookmarkLinks SET import_obsidian = 'YES' WHERE id = ?;"
    cursor.execute(query, (bookmark_id,))
    conn.commit()

# Exécution principale
def main():
    conn = connect_db(DB_PATH)
    bookmarks = get_recent_bookmarks(conn)
    urls = generate_urls(bookmarks, conn)
    
    print("Signets récents exportés dans 'hoarder_bookmarks.md'\n")
    conn.close()

if __name__ == "__main__":
    main()
