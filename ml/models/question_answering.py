import os
import logging 
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

class QAMachine:
    def __init__(self,embedder_machine):
        self.embedder =embedder_machine
        self.client = None
        self.system_prompt = os.getenv("QA_SYSTEM_PROMPT") or "Answer questions using only the supplied podcast context."
        self.model ="gpt-4o-mini"

    def _get_client(self):
        if self.client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError("OPENAI_API_KEY is required for podcast Q&A")
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise RuntimeError(
                    "openai is required for podcast Q&A. Install the ML requirements."
                ) from exc
            self.client = OpenAI(api_key=api_key)
        return self.client

    def ask(self,user_question, vault_path=None):
        logger.info(f"Processing question :{user_question}")

        if vault_path:
            self.embedder.load(vault_path)

        context_chunks =self.embedder.search(user_question,k=3)
        if not context_chunks:
            return "I don't have enough indexed podcast context to answer that yet."

        context_text = "\n--\n".join(context_chunks)

        try:
            response = self._get_client().chat.completions.create(
                model=self.model,
                messages=[
                    {"role":"system","content":self.system_prompt},
                    {
                        "role": "user",
                        "content": (
                            f"TRANSCRIPT CONTEXT:\n{context_text}\n\n"
                            f"USER QUESTION: {user_question}\n\n"
                            "Answer using only the TRANSCRIPT CONTEXT."
                        ),
                    }

                ],
                temperature=0
            )
            return response.choices[0].message.content
        
        except Exception as e :
            logger.error(f"QA Error :{e}")
            return "I encountered an error trying  to find that answer ."

            
        
