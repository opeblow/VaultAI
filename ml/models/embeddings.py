import logging
import os

logger =logging.getLogger(__name__)

class Embedder:
    def __init__(self,model_name="all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.index=None
        self.paragraphs = []#stores actual texts

    def _ensure_model(self):
        if self.model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise RuntimeError(
                    "sentence-transformers is required for embedding podcasts. "
                    "Install the ML requirements before running ingestion."
                ) from exc
            self.model = SentenceTransformer(self.model_name)

    @staticmethod
    def _load_faiss():
        try:
            import faiss
        except ImportError as exc:
            raise RuntimeError(
                "faiss-cpu is required for vector search. Install the ML requirements "
                "before running ingestion or podcast queries."
            ) from exc
        return faiss

    def reset(self):
        self.index = None
        self.paragraphs = []

    def add_to_index(self,text_list, reset=False):
        """Convert text to vectores and add them to faiss """
        if reset:
            self.reset()
        if not text_list:
            return

        self._ensure_model()
        faiss = self._load_faiss()
        import numpy as np

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
        faiss = self._load_faiss()
        os.makedirs(folder_path,exist_ok=True)
        faiss.write_index(self.index , f"{folder_path}/podcast.index")

        #save text paragraphs separately 
        with open (f"{folder_path}/paragraphs.txt","w",encoding="utf-8") as file:
            for line in self.paragraphs:
                file.write(line.replace("\n"," ") + "\n")

        logger.info(f"Index saved to {folder_path}")

    def load(self, folder_path):
        faiss = self._load_faiss()
        index_path = os.path.join(folder_path, "podcast.index")
        paragraphs_path = os.path.join(folder_path, "paragraphs.txt")

        if not os.path.exists(index_path) or not os.path.exists(paragraphs_path):
            raise FileNotFoundError(f"Podcast vault index is missing at {folder_path}")

        self.index = faiss.read_index(index_path)
        with open(paragraphs_path, "r", encoding="utf-8") as file:
            self.paragraphs = [line.strip() for line in file if line.strip()]

        logger.info(f"Index loaded from {folder_path}")

    def search(self,query,k=3):
        """Find top k most similar parts of the podcast"""
        if self.index is None or not self.paragraphs:
            return []
        self._ensure_model()
        query_vector = self.model.encode([query]).astype('float32')
        distances , indices = self.index.search(query_vector , k)
        results = [self.paragraphs[i] for i in indices[0] if i != -1]
        return results
        
        
