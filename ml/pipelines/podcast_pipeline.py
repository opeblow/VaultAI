import os
import json
from ml.utils.audio import load_and_process
from ml.utils.text import chunk_text,clean_text
from ml.models.stt import SpeechToText
from ml.models.summarizer import Summarizer
from ml.models.vector_store import VectorMachine
from ml.models.embeddings import Embedder
from ml.models.question_answering import QAMachine
from dotenv import load_dotenv
load_dotenv()

class PodcastPipeline:
    def __init__(self):
        self.stt_engine = SpeechToText()
        self.summarizer_engine = Summarizer()
        self.vector_store = VectorMachine()
        self.embedder_engine = Embedder()
        self.qa_machine = QAMachine(embedder_machine=self.embedder_engine)
        print("ML ENGINE INITIALIZED")
        

    def execute(self,user_id,podcast_id,audio_input_path):
        print(f"\n [GLOBAL INGESTION] Initiating for user {user_id}")

        processed_audio_path = load_and_process(audio_input_path)
        print("Generating speaker-aware transcript")
        labeled_segments , language_info = self.stt_engine.transcribe_with_timestamps(processed_audio_path)
        speaker_transcript = "\n".join([s["labeled_text"] for s in labeled_segments])
        print(f"Language Detected :{language_info.upper()}")

        full_text = " ".join([s["text"] for s in labeled_segments])
        cleaned_text = clean_text(full_text)
        chunks = chunk_text(cleaned_text)

        print("Building Isolated Vector Vault..")
        user_vault_path = os.path.join(
            "storage","users",str(user_id),"indices",str(podcast_id)
        )
        os.makedirs(user_vault_path,exist_ok=True)
        self.embedder_engine.add_to_index(chunks)
        self.embedder_engine.save(folder_path = user_vault_path)
        self.vector_store.current_vault_path = user_vault_path

        print("Generating AI Executive Summary")
        summary = self.summarizer_engine.summarize(speaker_transcript)

        speakers_found = list(set(s["speaker"] for s in labeled_segments))
        metadata ={
            "user_id":user_id,
            "podcast_id":podcast_id,
            "language":language_info,
            "speakers":speakers_found,
            "speakers_count":len(speakers_found),
            "segments":labeled_segments,
            "summary":summary
        }
        with open(os.path.join(user_vault_path,"metadata.json"),"w")as file:
            json.dump(metadata,file,indent=4)
        print(f"[{podcast_id}] indexed,searchable,and speaker-labeled")

        return {
            "status":"success",
            "language":language_info,
            "summary":summary,
            "vault_path":user_vault_path,
            "labeled_segments":labeled_segments,
            "speaker_count":len(speakers_found),
            "speakers":speakers_found
        }

    def ask_ai(self, question: str) -> str:
        print(f" AI Query : '{question}'")
        return self.qa_machine.ask(user_question=question)

