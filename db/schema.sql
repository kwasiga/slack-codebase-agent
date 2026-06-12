CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS chunks (
    id SERIAL PRIMARY KEY,
    file_path TEXT,
    start_line INT,
    end_line INT,
    chunk_text TEXT,
    embedding vector(1024)
);
