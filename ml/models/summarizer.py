import os
import logging
from dotenv import load_dotenv
load_dotenv()
logger =logging.getLogger(__name__)


class Summarizer:
    def __init__(self):
        self.secret_prompt = os.getenv("SUMMARIZER_SYSTEM_PROMPT") or "You are an expert podcast analyst.Summarize the key insights"
        self.client = None
        self.model ="gpt-4o-mini"

    def _get_client(self):
        if self.client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError("OPENAI_API_KEY is required for podcast summarization")
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise RuntimeError(
                    "openai is required for podcast summarization. Install the ML requirements."
                ) from exc
            self.client = OpenAI(api_key=api_key)
        return self.client

    def summarize(self,transcript_text):
        if not transcript_text:
            return "Transcript is empty"
        logger.info("Generating Secure Summary")
        
        try:
            response = self._get_client().chat.completions.create(
                model= self.model,
                messages=[
                    {"role":"system","content":self.secret_prompt},
                    {"role":"user","content":f'Summarize this podcast:\n\n{transcript_text}'}
                ],
                temperature=0.2

            )
            return response.choices[0].message.content
        
        except Exception as e:
            logger.error(f"Summarize Error:{e}")
            print(f"Summarize error details:{e}")
            return f"summary failed:{str(e)}"

            
