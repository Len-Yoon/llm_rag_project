# backend/app/db_check.py
import sqlite3, os

# 현재 파일 위치 기준으로 backend/vectorstore 폴더 찾기
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # backend/ 까지 올라감
db_path = os.path.join(BASE_DIR, "vectorstore", "chroma.sqlite3")

print("DB Path:", os.path.abspath(db_path))

conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("테이블 목록:", cur.fetchall())

cur.execute("SELECT COUNT(*) FROM embeddings;")
print("임베딩 저장 개수:", cur.fetchone())

cur.execute("SELECT * FROM embeddings LIMIT 3;")
print("샘플 row:", cur.fetchall())

conn.close()
