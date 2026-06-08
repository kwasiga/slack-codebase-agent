import os, time
from dotenv import load_dotenv
import voyageai

load_dotenv()
vo = voyageai.Client()

def embed_chunks(chunks):
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i: i + batch_size]
        texts = [chunk["chunk_text"] for chunk in batch]
        result = vo.embed(texts, model="voyage-code-3", input_type="document")
        for chunk, vector in zip(batch, result.embeddings):
            chunk["embedding"] = vector
        time.sleep(0.5)
    return chunks

