import psycopg2
from pgvector.psycopg2 import register_vector
import os
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv('DATABASE_URL')

def store_chunks(chunks):
    conn = psycopg2.connect(db_url)  # DATABASE_URL from env
    register_vector(conn)
    cur = conn.cursor()
    
    cur.execute("TRUNCATE chunks;")
    
    rows = [(chunk["file_path"], chunk["start_line"], chunk["end_line"], chunk["chunk_text"], chunk["embedding"]) for chunk in chunks]
    cur.executemany("INSERT INTO chunks (file_path, start_line, end_line, chunk_text, embedding) VALUES (%s, %s, %s, %s, %s)", rows)
    
    conn.commit()
    cur.close()
    conn.close()

    return len(rows)