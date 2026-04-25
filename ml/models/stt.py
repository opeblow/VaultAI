import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class SpeechToText():
    def __init__(self,model_name="tiny"):
        self.model_name = model_name
        self.model = None
        logger.info(f"SpeechToText initialized (model will load on first use).")
    
    def _ensure_model(self):
        if self.model is None:
            import whisper
            self.model = whisper.load_model(self.model_name)
            logger.info(f"Model '{self.model_name}' loaded successfully.")

    def transcribe(self,audio_path):
        self._ensure_model()
        result = self.model.transcribe(audio_path,fp16=False)
        return result

    def transcribe_with_timestamps(self,audio_path):
        self._ensure_model()
        result = self.model.transcribe(audio_path,fp16=False,word_timestamps=True,verbose=False)
        segments = result.get("segments",[])
        labeled = self._assign_speakers(segments)
        for seg in labeled:
            logger.info(
                f"[{seg['start']:>6.2f}s -> {seg['end']:>6.2f}s]"f"{seg['speaker']}:{seg['text']}"
            )
        language_info = result.get("language","en")
        return labeled , language_info
    
    def _assign_speakers(self,segments:list)->list[dict]:
        if not segments :
            return []
        PAUSE_THRESHOLD =1.5
        labeeled_segments = []
        speaker_index =0
        speaker_names = [
            "HOST",
            "GUEST_1",
            'GUEST_2',
            "GUEST_3",
            "SPEAKER_4",
            "SPEAKER_5"
        ]
        prev_end = None

        for i ,segment in enumerate(segments):
            start = segment["start"]
            end = segment["end"]
            text = segment["text"].strip()

            if not text:
                continue
            if prev_end is not None:
                pause = start - prev_end
                if pause > PAUSE_THRESHOLD:
                    speaker_index = min(speaker_index + 1,len(speaker_names) -1)
            speaker = speaker_names[speaker_index]
            labeeled_segments.append(
                {
                    "start":round(start,3),
                    "end":round(end,3),
                    "text":text,
                    "speaker":speaker,
                    "labeled_text":f"{speaker}:{text}",
                    "pause_before":round(start-prev_end,3) if prev_end else 0.0
                }
            )
            prev_end =end
        speakers_found = set(s["speaker"] for s in labeeled_segments)
        logger.info(
            f"Speaker detection complete -"
            f"{len(speakers_found)} speaker(s) found:{speakers_found}"
        )
        return labeeled_segments
        
    def detect_language(self,audio_path):
        self._ensure_model()
        import whisper
        audio= whisper.load_audio(audio_path)
        audio = whisper.pad_or_trim(audio)
        pat = whisper.log_mel_spectrogram(audio).to(self.model.device)
        _, probs = self.model.detect_language(pat)
        detected_language = max(probs ,key=probs.get)
        logger.info (f"Detected Language: {detected_language} (Confidence:{probs[detected_language]:.2f})")
        return detected_language , probs
    
    def get_full_transcript(self,audio_path:str)->str:
        self._ensure_model()
        result = self.model.transcribe(audio_path)
        return result
    
    def get_speaker_transcript(self,audio_path:str)->str:
        """Returns full transcript formatted with  speaker labels.
        Perfect for feeding into the summarizer
        Example output:
        HOST:Welcome to the show today...
        GUEST_1:Thanks for having me...
        HOST:Let's talk about AI...
        
        """
        segments = self.transcribe_with_timestamps(audio_path)
        lines = []
        current_speaker = None
        current_text = []
        for seg in segments:
            if seg["speaker"] != current_speaker:
                if current_speaker and current_text:
                    lines.append(f"{current_speaker}:{''.join(current_text)}")
                current_speaker = seg["speaker"]
                current_text = [seg["text"]]
            else:
                current_text.append(seg["text"])

        if current_speaker and current_text:
            lines.append(f"{current_speaker}: {''.join(current_text)}")

        return "\n".join(lines)
    
    
