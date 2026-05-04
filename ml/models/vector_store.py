import os
import pickle


def _load_vector_deps():
    try:
        import faiss
        import numpy as np
    except ImportError as exc:
        raise RuntimeError(
            "faiss-cpu and numpy are required for vector storage. Install the ML "
            "requirements before running ingestion or podcast queries."
        ) from exc
    return faiss, np


class VectorMachine:
    def __init__(self,base_storage="storage/users"):
        self.base_storage=base_storage

    def _get_path(self,user_id,podcast_id):
        path=os.path.join(self.base_storage,str(user_id),"indices",str(podcast_id))
        os.makedirs(path,exist_ok=True)
        return path
    
    def create_index(self,user_id,podcast_id,chunks,embeddings):
        faiss, np = _load_vector_deps()
        target_path = self._get_path(user_id,podcast_id)
        dimension = len(embeddings[0])
        index = faiss.IndexFlatL2(dimension)
        index.add(np.array(embeddings).astype('float32'))

        faiss.write_index(index,os.path.join(target_path, "index.faiss"))
        with open(os.path.join(target_path,"chunks.pkl"),"wb") as file:
            pickle.dump(chunks,file)
        print(f"Vault Created :{target_path}")
        return target_path
    
    def load_index(self,user_id,podcast_id):
        faiss, _ = _load_vector_deps()
        target_path = os.path.join(self.base_storage,str(user_id),"indices",str(podcast_id))
        if not os.path.exists(target_path):
            raise FileNotFoundError(f"Index not found for {user_id}/{podcast_id}")
        
        index=faiss.read_index(os.path.join(target_path,"index.faiss"))
        with open(os.path.join(target_path,"chunks.pkl"),"rb") as file:
            chunks = pickle.load(file)
        return index,chunks
        
