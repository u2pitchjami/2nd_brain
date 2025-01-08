import sqlite3
import json
import requests
import config    

# Connexion à la base SQLite de Hoarder

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Requête pour trouver les signets sans résumé
query = "SELECT id FROM bookmarks WHERE summary IS NULL;"
cursor.execute(query)

# Récupération des résultats
bookmarks = cursor.fetchall()

# Affichage ou traitement des résultats
for bookmark in bookmarks:
    bookmark_id = bookmark[0] 
    print("id:",bookmark_id)
    
    payload = {"0":{"json":{"bookmarkId":bookmark_id}}}
    #'{"0":{"json":{"bookmarkId":"k4tzz9wht9h6ghtjh75u3j1c"}}}'
    response = requests.post(
        API_URL,
        headers={
            "Authorization": TOKEN,
            "Content-Type": "application/json"
        },
        json=payload
    )

    if response.status_code == 200:
        print(f"Résumé généré pour : {bookmark_id}")
    else:
        print(f"Erreur sur {bookmark_id} : {response.status_code} - {response.text}")


# Export en JSON si nécessaire
#with open("bookmarks_without_summary.json", "w") as f:
#    json.dump(bookmarks, f, indent=4)

# Fermer la connexion
conn.close()
