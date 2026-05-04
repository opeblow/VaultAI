import os
import logging
from typing import Dict
import subprocess

logger = logging.getLogger(__name__)


SUPPORTED_FORMATS ={
    ".mp3",".mpeg",".mp4",".wav",".m4a",
    ".ogg",".flac",".aac",".wma",".webm",
    ".mov",".avi",".mkv",".opus",".amr"
}
CONVERSION_NEEDED_FORMATS = {".wma",".amr",".opus"}


def _load_whisper():
    try:
        import whisper
    except ImportError as exc:
        raise RuntimeError(
            "openai-whisper is required for audio transcription. Install the ML "
            "requirements before running ingestion."
        ) from exc
    return whisper


def load_and_process(audio_path:str)->str:
    if not os.path.exists(audio_path):
        logger.error(f"Audio file not found :{audio_path}")
        raise FileNotFoundError(f"Could not find the audio file:{audio_path}")
    ext = os.path.splitext(audio_path)[1].lower()

    if ext not in SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported audio format : '{ext}'"
                f"Supported formats : {','.join(sorted(SUPPORTED_FORMATS))}"
            )
    logger.info(f"Loading audio from : {audio_path } (format:{ext})")

    if ext in CONVERSION_NEEDED_FORMATS:
         logger.info(f"Converting {ext} to 16KHz mono wav  for better compatibility")
         audio_path = _convert_to_wav(audio_path)

    if os.path.getsize(audio_path) == 0:
         raise ValueError(f"Audio file is empty :{audio_path}")
    logger.info(f"Audio ready - size:{os.path.getsize(audio_path)/(1024 * 1024):.2f}MB")

    try:
         whisper = _load_whisper()
         audio = whisper.load_audio(audio_path)
         duration = len(audio) / whisper.audio.SAMPLE_RATE
         logger.info(f"Audio Processed successfully - duration :{duration:.1f}s")

    except Exception as e :
         logger.error(f"Failed to load audio with whispher :{e}")
         raise 
    
    return audio_path


def get_duration(audio_path:str)->float:
     if not os.path.exists(audio_path):
          raise FileNotFoundError(f"Audio file not found :{audio_path}")
     
     whisper = _load_whisper()
     audio = whisper.load_audio(audio_path)
     duration = len(audio) / whisper.audio.SAMPLE_RATE

     logger.info(f"Audio duration :{duration:.1f}s ({duration/60:.1f}min)")
     return duration

def get_file_info(audio_path:str)-> Dict:
     if not os.path.exists(audio_path):
          raise FileNotFoundError(f"Audio file not found :{audio_path}")
     
     ext = os.path.splitext(audio_path)[1].lower()
     file_size = os.path.getsize(audio_path)
     duration = get_duration(audio_path)
     info = {
          "path":audio_path,
          "format":ext,
          "size_mb":round(file_size/(1024 * 1024),2),
          "duration_minutes":round(duration/60,1),
          "supported":ext in SUPPORTED_FORMATS
     }
     logger.info(f"File info retrieved : {info}")
     return info

def validate_audio(audio_path):
     if not os.path.exists(audio_path):
          raise FileNotFoundError(f"Audio file not found :{audio_path}")
     
     ext = os.path.splitext(audio_path)[1].lower()
     if ext not in SUPPORTED_FORMATS:
          raise ValueError(f"Unsupported format:{ext}")
     
     if os.path.getsize(audio_path) == 0:
        raise ValueError(f"Audio File is empty :{audio_path}")
     
     return True


def _convert_to_wav(audio_path:str) -> str:
     output_path = os.path.splitext(audio_path)[0] + "_converted.wav"
     try:
          result = subprocess.run(
               [
                    "ffmpeg","-i",audio_path,
                    "-ar","16000",
                    "-ac","1",
                    "-y",
                    output_path
               ],
               check=True,capture_output=True,text=True
          )
          logger.info(f"Succssfully converted  to WAV:{output_path}")
          return output_path
     except subprocess.CalledProcessError as e :
          logger.error(f"FFmpeg conversion failed : {e.stderr}")
          logger.warning("Falling back  to original file")
          return audio_path
     
     except FileNotFoundError:
          logger.warning("FFmpeg command not found.Make sure  FFmpeg is installed  and in PATH")
          logger.warning("Using original fle directly (may fail for some formats)")
          return audio_path
     
    
