from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.spatial.distance import euclidean
from collections import Counter
import hdbscan
import numpy as np

#----------------------------------------------------------
# Cluster long text description using clustering categories
#----------------------------------------------------------
class TextClusterEncoder ():
	def __init__(self):

		# Step 1: Encode text descriptions using TF-IDF
		self.vectorizer = TfidfVectorizer (max_features=500)

	def fit_transform (self, descriptions):
		# Step 1: Encode text descriptions using TF-IDF
		self.descriptions = descriptions
		self.tfidf_matrix = self.vectorizer.fit_transform (descriptions)

		# Step 2: Apply DBSCAN clustering
		hdb = hdbscan.HDBSCAN (min_cluster_size=2)  # Adjust parameters as needed
		self.cluster_labels = hdb.fit_predict (self.tfidf_matrix)
		print("Cluster Labels:", self.cluster_labels)

		return self.cluster_labels

	#-- Return the original value
	def inverse_transform (self, encValuesList):
		print ("inverse_transform input: ", encValuesList)
		cluster_id = encValuesList [0]
		freq_desc = self.get_cluster_representative_description (cluster_id)
		return freq_desc

	#-- Return encoded description closest to cluster_id
	def get_cluster_representative_description (self, cluster_id):
		cluster_labels = self.cluster_labels
		tfidf_matrix   = self.tfidf_matrix
		descriptions   = self.descriptions

		# Get the indices of descriptions belonging to the given cluster
		cluster_indices = np.where (cluster_labels == cluster_id)[0]
		
		# Ignore noise points or rff the cluster is empty, return a placeholder message
		if cluster_id == -1 or len(cluster_indices) == 0:
			return "No representative description found."

		# Compute the average vector (pseudo-centroid) for the cluster
		cluster_vectors = tfidf_matrix [cluster_indices].toarray ()
		avg_vector = np.mean (cluster_vectors, axis=0)

		# Find the description closest to the average vector
		closest_idx = cluster_indices [np.argmin (
			[euclidean (avg_vector.flatten(), vec.flatten()) for vec in cluster_vectors]
		)]

		# Return the most representative description
		return descriptions[closest_idx]

	#-- Select the Most Frequent Description per Cluster
	def get_most_frequent_description (self, cluster_id):
		cluster_labels = self.cluster_labels
		descriptions   = self.descriptions

		# Get the descriptions belonging to the given cluster
		cluster_descriptions = [descriptions[i] for i in np.where (cluster_labels == cluster_id)[0]]
		
		if len (cluster_descriptions) == 0:
			return "No description found for this cluster."
		
		# Count the occurrences of each description in the cluster
		description_counts = Counter (cluster_descriptions)
		
		# Return the most frequent description
		most_frequent_desc = description_counts.most_common(1)[0][0]
		return most_frequent_desc

