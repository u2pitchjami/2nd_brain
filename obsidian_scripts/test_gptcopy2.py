import chromadb
from chromadb.utils.embedding_functions import OllamaEmbeddingFunction
from sklearn.cluster import KMeans
import logging
from handlers.logger_setup import setup_logging
from handlers.files import read_note_content
import numpy as np
from handlers.files import clean_content


def process_gpt_note(filepath):
    # Initialisation de ChromaDB
    client = chromadb.Client()

    # Fonction d'embedding avec Ollama
    embedding_function = OllamaEmbeddingFunction(
        model_name="nomic-embed-text:latest",
        url="http://192.168.50.12:11434/api/embeddings"
    )

    # Création ou récupération de la collection
    collection = client.get_or_create_collection(
        name="gpt_segments",
        embedding_function=embedding_function
    )

    # Exemple de note GPT
    content = read_note_content(filepath)
    gpt_note = clean_content(content, filepath)

    segments = split_note_by_lines(gpt_note)

    # Ajouter les segments à la collection
    for idx, segment in enumerate(segments):
        collection.add(
            documents=[segment],
            metadatas=[{"id": idx}],
            ids=[str(idx)]
        )

    # Étape 2 : Récupérer les embeddings et documents
    response = collection.get(include=["embeddings", "documents"])
    if response is None or response["documents"] is None:
        print("[ERREUR] Aucun segment disponible.")
        exit()

    embeddings = [embedding for embedding in response["embeddings"]]
    texts_from_db = [doc for doc in response["documents"]]

    # Étape 3 : Clustering avec KMeans
    n_clusters = 5  # Nombre de thèmes attendus
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    embeddings_array = np.array(embeddings)
    kmeans.fit(embeddings_array)

    # Regrouper les segments par cluster
    labels = kmeans.labels_
    clusters = {}
    for idx, label in enumerate(labels):
        clusters.setdefault(label, []).append(texts_from_db[idx])

    # Affichage des clusters
    for cluster_id, cluster_texts in clusters.items():
        print(f"\nCluster {cluster_id} :")
        for text in cluster_texts:
            print(f"  - {text}")


# Étape 1 : Découpe la note en segments
def split_note_by_lines(note):
    """
    Divise une note en lignes non vides.
    """
    return [line.strip() for line in note.splitlines() if line.strip()]