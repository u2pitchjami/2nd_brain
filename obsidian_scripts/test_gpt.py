import requests
from numpy import dot
from numpy.linalg import norm
from sklearn.cluster import KMeans
import logging
from handlers.logger_setup import setup_logging
from handlers.files import read_note_content

# Fonction pour obtenir des embeddings via Nomic
def get_embeddings_nomic(content, url="http://192.168.50.12:11434/api/embeddings"):
    """
    Envoie une requête à l'API de nomic-embed-text pour générer des embeddings.

    :param text: Texte à encoder.
    :param url: URL de l'API Nomic (par défaut http://localhost:8000/).
    :return: Embedding (liste de floats) ou None en cas d'échec.
    """
    payload = {
        "model": "nomic-embed-text:latest",
        "text": content
    }
    logging.debug(f"[DEBUG] get_embeddings_nomic Payload envoyé : {payload}")
    try:
        response = requests.post(url, json=payload, stream=True)
        response.raise_for_status()
        logging.debug(f"[DEBUG] Réponse brute (texte) : {response.text}")
        result = response.json()
        logging.debug(f"[DEBUG] get_embeddings_nomic : response : {result}")
        return response.json().get("embedding")
    except requests.exceptions.RequestException as e:
        print(f"[ERREUR] API Nomic : {e}")
        return None

# Fonction pour calculer la similarité cosine
def cosine_similarity(embedding1, embedding2):
    """Calcule la similarité cosine entre deux vecteurs."""
    return dot(embedding1, embedding2) / (norm(embedding1) * norm(embedding2))

# Découpe le texte en segments
def split_text_by_lines(content):
    """
    Divise le texte brut en segments basés sur les lignes.
    Chaque segment représente une ligne (ou un échange).
    
    :param text: Texte brut (note GPT).
    :return: Liste des segments.
    """
    logging.debug(f"[DEBUG] split_text_by_lines")
    return [line.strip() for line in content.splitlines() if line.strip()]

# Regroupe les segments en clusters
def cluster_segments(segments, embeddings, num_clusters=3):
    """
    Regroupe les segments similaires en utilisant KMeans.

    :param segments: Liste des segments de texte.
    :param embeddings: Liste des embeddings pour chaque segment.
    :param num_clusters: Nombre de clusters à former.
    :return: Dictionnaire avec les clusters et leurs segments associés.
    """
    logging.debug(f"[DEBUG] cluster_segments")
    kmeans = KMeans(n_clusters=num_clusters, random_state=42)
    logging.debug(f"[DEBUG] cluster_segments : kmeans : {kmeans}")
    labels = kmeans.fit_predict(embeddings)
    logging.debug(f"[DEBUG] cluster_segments : labels : {labels}")
    clusters = {i: [] for i in range(num_clusters)}
    for idx, label in enumerate(labels):
        clusters[label].append(segments[idx])

    logging.debug(f"[DEBUG] cluster_segments : clusters : {clusters}")
    return clusters

# Pipeline principal pour traiter une note
def process_gpt_note(filepath, api_url="http://192.168.50.12:11434/api/embeddings", num_clusters=3):
    """
    Traite une note GPT en regroupant les segments similaires par thème.

    :param note: Texte brut de la note GPT.
    :param api_url: URL de l'API Nomic pour générer les embeddings.
    :param num_clusters: Nombre de clusters à former.
    :return: Dictionnaire des clusters avec leur contenu.
    """
    logging.debug(f"[DEBUG] process_gpt_note : {filepath}")
    content = read_note_content(filepath)
    # Étape 1 : Découpe la note en segments
    segments = split_text_by_lines(content)
    logging.debug(f"[DEBUG] split_text_by_lines : segments : {segments}")
    # Étape 2 : Génère les embeddings pour chaque segment
    embeddings = [get_embeddings_nomic(segment, url=api_url) for segment in segments]
    logging.debug(f"[DEBUG] split_text_by_lines : embeddings1 : {embeddings}")
    embeddings = [e for e in embeddings if e is not None]  # Filtrer les erreurs
    logging.debug(f"[DEBUG] split_text_by_lines : embeddings2 : {embeddings}")
    if not embeddings:
        print("[ERREUR] Aucun embedding généré.")
        return None

    # Étape 3 : Regroupe les segments similaires en clusters
    clusters = cluster_segments(segments, embeddings, num_clusters=num_clusters)
    logging.debug(f"[DEBUG] split_text_by_lines : clusters : {clusters}")
    return clusters

