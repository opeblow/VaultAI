import faiss
import numpy as np
import logging
import os
from sentence_transformers import SentenceTransformer

logger =logging.getLogger(__name__)

class Embedder:
    def __init__(self,model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.index=None
        self.paragraphs = []#stores actual texts

    def add_to_index(self,text_list):
        """Convert text to vectores and add them to faiss """
        self.paragraphs.extend(text_list)
        embeddings = self.model.encode(text_list)

        nodes =np.array(embeddings).astype('float32')#converting to float32

        if self.index is None:
            dimension = nodes.shape[1]
            self.index = faiss.IndexFlatL2(dimension)

        self.index.add(nodes)
        logger.info(f"Added {len(text_list)} vectors to index")

    def save(self,folder_path="data/processed"):
        if self.index is None:
            return
        os.makedirs(folder_path,exist_ok=True)
        faiss.write_index(self.index , f"{folder_path}/podcast.index")

        #save text paragraphs separately 
        with open (f"{folder_path}/paragraphs.txt","w",encoding="utf-8") as file:
            for line in self.paragraphs:
                file.write(line.replace("\n"," ") + "\n")

        logger.info(f"Index saved to {folder_path}")

    def search(self,query,k=3):
        """Find top k most similar parts of the podcast"""
        query_vector = self.model.encode([query]).astype('float32')
        distances , indices = self.index.search(query_vector , k)
        results = [self.paragraphs[i] for i in indices[0] if i != -1]
        return results
        
        