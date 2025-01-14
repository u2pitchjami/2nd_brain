import sqlite3
from datetime import datetime

# Configuration
DB_PATH = '/mnt/user/appdata/hoarder/db.db'  # Remplacer par le bon chemin
EXPORT_PATH = '/mnt/user/Documents/Obsidian/notes/gpt_processed/hoarder_bookmarks.md'  # Chemin vers l'export

# Connexion à la base de données
def connect_db(db_path):
    return sqlite3.connect(f"file:{db_path}?mode=rwc", uri=True)

# Requête pour récupérer les signets récents
def get_recent_bookmarks(conn):
    cursor = conn.cursor()
    query = """
    SELECT id, url, title, crawledAt
    FROM bookmarkLinks
    WHERE import_obsidian = 'NO'
    ORDER BY crawledAt DESC;
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    print(f"[INFO] Nombre de signets récupérés : {len(rows)}")  # Debugging
    return rows

# Conversion du timestamp en date lisible
def convert_timestamp(timestamp):
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

# Génération des URLs de prévisualisation + Export Markdown
def generate_urls(bookmarks, conn):
    if not bookmarks:
        print("[INFO] Aucun signet à exporter.")
        return []

    urls = []
    try:
        with open(EXPORT_PATH, "w", encoding="utf-8") as f:
            f.write("# Signets Hoarder Récents\n\n")
            for bookmark in bookmarks:
                bookmark_id, url, title, date = bookmark
                readable_date = convert_timestamp(date)

                # Générer une entrée pour chaque signet
                entry = f"## {title}\n- Date: {readable_date}\n- [Voir l'URL Originale]({url})\n\n"
                urls.append(entry)
                f.write(entry)

                # Marquer comme importé avec la même connexion
                mark_as_imported(conn, bookmark_id)

        print(f"[INFO] Export terminé : {EXPORT_PATH}")
    except Exception as e:
        print(f"[ERREUR] Impossible d'écrire le fichier d'export : {e}")

    return urls

# Marquer les signets comme importés
def mark_as_imported(conn, bookmark_id):
    try:
        cursor = conn.cursor()
        query = "UPDATE bookmarkLinks SET import_obsidian = 'YES' WHERE id = ?;"
        cursor.execute(query, (bookmark_id,))
        conn.commit()
        print(f"[INFO] Signet marqué comme importé : {bookmark_id}")
    except Exception as e:
        print(f"[ERREUR] Impossible de marquer le signet {bookmark_id} comme importé : {e}")

# Exécution principale
def main():
    try:
        conn = connect_db(DB_PATH)
        bookmarks = get_recent_bookmarks(conn)
        urls = generate_urls(bookmarks, conn)

        if not urls:
            print("[INFO] Aucun signet à exporter.")
        conn.close()
    except Exception as e:
        print(f"[ERREUR] Échec de l'exécution : {e}")

if __name__ == "__main__":
    main()