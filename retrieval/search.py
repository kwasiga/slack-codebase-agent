import psycopg2
import os
from dotenv import load_dotenv
from pgvector.psycopg2 import register_vector
from pgvector import Vector
import voyageai

load_dotenv()
vo = voyageai.Client()


db_url = os.getenv('DATABASE_URL')

def semantic_search(query, top_k=5):
    query_vector = Vector(vo.embed([query], model="voyage-code-3", input_type="query").embeddings[0])
    conn = psycopg2.connect(db_url)
    register_vector(conn)

    with conn.cursor() as cur:
        cur.execute(
            "SELECT file_path, start_line, end_line, chunk_text FROM chunks ORDER BY embedding <=> %s LIMIT %s",
            (query_vector, top_k)
        )
        rows = cur.fetchall()

    conn.close()
    return [
        {"file_path": r[0], "start_line": r[1], "end_line": r[2], "chunk_text": r[3]}
        for r in rows
    ]

    


