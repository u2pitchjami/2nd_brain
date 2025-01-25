import chromadb
from chromadb.utils.embedding_functions import OllamaEmbeddingFunction
from sklearn.cluster import KMeans
import numpy as np

# Configurez la fonction d'embedding Ollama
ef = OllamaEmbeddingFunction(
    model_name="nomic-embed-text",
    url="http://192.168.50.12:11434/api/embeddings"
)

# Exemple de textes à encoder
texts = ["Voici un article sur les lamas...", "Un autre texte à encoder", "Encore un exemple"]

# Générez les embeddings
embeddings = ef(texts)

# Convertissez les embeddings en tableau numpy
embeddings_array = np.array(embeddings)

# Appliquez KMeans
kmeans = KMeans(n_clusters=2, random_state=42)
kmeans.fit(embeddings_array)

# Obtenez les labels des clusters
labels = kmeans.labels_

print("Labels des clusters:", labels)
