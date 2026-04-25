import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0,str(ROOT_DIR))

try :
    from ml.pipelines.podcast_pipeline import PodcastPipeline

except ImportError:
    print("Error:Could not find 'ml.pipelines.podcast_pipeline")
    print("Make sure you are running  this from the project root ")
    sys.exit(1)

def run_interactive_test():
    print("\n" + "="*60)
    print("GLOBAL SAAS ENGINE:DIARIZATION VALIDATED ")
    print("="*60)

    USER_ID = "230405013"
    PODCAST_ID = "Beta_Test_Run_01"
    AUDIO_PATH = r"C:\Users\user\Documents\PODCAST\data\samples\test_audio.mpeg"

    for folder in ["data/samples","storage/users"]:
        if not os.path.exists(folder):
            os.makedirs(folder,exist_ok=True)

    if not os.path.exists(AUDIO_PATH):
        print(f"\n FILE MISSING :Place an audio file at : {AUDIO_PATH}")
        return
    try:
        print("\n Initializing ML Engine (Loading Whisper & Pyannote)..")
        pipeline = PodcastPipeline()
        print(f"\n INGESTING:Processing audio for user_{USER_ID}")
        print("Running transcription + smart speaker detection")
        start_time = time.time()
        result = pipeline.execute(USER_ID,PODCAST_ID,AUDIO_PATH)
        duration = time.time() - start_time

        print(f"\n SUCCESS:Processing completed in {duration:.2f}seconds")
        print(f" Language : {result.get('language','Unknown').upper()}")
        print(f"Speakers : {result.get('speaker_count',0)}")
        print(f"Speaker List : {result.get('speakers',[])}")
        print(f"Vault Path : {result.get('vault_path')}")

        print("\n" + "-"*60)
        print("SPEAKER TRANSCRIPT PREVIEW  (first 5 segments)")
        print("-"*60)

        for seg in result.get("labeled_segments",[])[:5]:
            print(f"[{seg['start']:>6.2f}s -> {seg['end']:>6.2f}s]" f"{seg['speaker']:>8}: {seg['text'][:90]}{'...' if len(seg['text']) > 90 else ''}")
        print("\n" + "-"*60)
        print("AI EXECUTIV SUMMARY")
        summary = result.get("summary","No summary generated")
        print(summary)
        print("=" *70 + "\n")

        print("SPEAKER-AWARE VAULTIS NOW OPEN")
        print("Ask anything about thepodcast.Type 'q' or 'quit' to exit")

        while True:
            query = input("ASK THE AI:").strip()

            if query.lower() in ['exit','quit','q']:
                print("\n Vault Locked.Session Ended")
                break
            if not query :
                continue
            print("Searching Vault")
            q_start= time.time()
            answer=pipeline.ask_ai(query)
            q_end = time.time()
            print(f"\n AI RESPONSE ({q_end - q_start:.2f}s):")
            print(answer)
            print("\n" + "-"*50)

    except Exception as e:
        print(f"Critical Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_interactive_test()
    



