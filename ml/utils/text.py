import re

def chunk_text(text, chunk_size=500):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunks.append(' '.join(words[i:i + chunk_size]))
    return chunks

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text
