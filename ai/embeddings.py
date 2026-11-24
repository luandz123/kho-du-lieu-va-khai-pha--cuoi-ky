"""Tạo vector (embedding) mô tả cho từng phim và lưu vào kho (bảng dw.movie_embedding, pgvector).

Mỗi phim được ghép thành 1 đoạn văn: tên, năm, thể loại, đạo diễn, diễn viên, quốc gia
và đoạn mở đầu bài Wikipedia (tiếng Anh + tiếng Việt nếu có). Mô hình multilingual-e5-small
biến đoạn văn thành vector 384 chiều; hai phim có nội dung giống nhau thì 2 vector gần nhau
(cosine lớn). Mô hình đa ngôn ngữ (~100 ngôn ngữ) nên câu hỏi tiếng Việt được đặt vào cùng
không gian với mô tả tiếng Anh. E5 được huấn luyện cho tìm kiếm: câu hỏi thêm tiền tố "query: ",
tài liệu thêm "passage: ".

Dùng cho:
  - tìm phim bằng câu mô tả tự do (app, trang "Tìm phim");
  - gợi ý theo nội dung trong mô hình hybrid (ai/hybrid.py).

Chạy: python -m ai.embeddings
"""
import threading

import numpy as np
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

from pipeline import config, lake
from transform.duck import connect

MODEL_NAME = "intfloat/multilingual-e5-small"
MAX_TOKENS = 256   # mặc định 128; mô tả phim cần dài hơn
_model = None
_lock = threading.Lock()


def model():
    """Tải mô hình 1 lần cho cả tiến trình. Có khóa để app tải nền lúc khởi động mà không bị tải 2 lần."""
    global _model
    with _lock:
        if _model is None:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer(MODEL_NAME, device="cpu")
            _model.max_seq_length = MAX_TOKENS
    return _model


def is_loaded() -> bool:
    return _model is not None


def encode(texts: list[str], kind: str = "query") -> np.ndarray:
    """kind = 'query' (câu người dùng gõ) hoặc 'passage' (mô tả phim).
    Vector đã chuẩn hóa độ dài 1, nên tích vô hướng = cosine similarity."""
    texts = [f"{kind}: {t}" for t in texts]
    return model().encode(texts, batch_size=32, normalize_embeddings=True, show_progress_bar=len(texts) > 200)


def movie_documents() -> pd.DataFrame:
    s = lambda t: f"read_parquet('{lake.path('silver', t, 'data.parquet')}')"
    summaries = (s("summaries") if lake.exists(lake.path("silver", "summaries", "data.parquet")) else
                 "(SELECT NULL::VARCHAR imdb_id, NULL::VARCHAR summary_en, NULL::VARCHAR summary_vi LIMIT 0)")
    sql = f"""
        SELECT m.movie_id, m.title, m.year, m.genres, i.directors, i.top_cast, w.countries,
               su.summary_en, su.summary_vi
        FROM {s('movies')} m
        LEFT JOIN {s('imdb_movies')} i USING (imdb_id)
        LEFT JOIN {s('wiki_links')} w USING (imdb_id)
        LEFT JOIN {summaries} su USING (imdb_id)
    """
    df = connect().execute(sql).df()

    def join(v):
        return ", ".join(v) if isinstance(v, (list, tuple, np.ndarray)) and len(v) else ""

    def doc(r):
        # Mô tả nội dung đặt ngay sau tên phim: mô hình chỉ đọc MAX_TOKENS token đầu.
        parts = [f"{r.title} ({r.year})." if pd.notna(r.year) else f"{r.title}.",
                 f"Genres: {join(r.genres).replace('|', ', ')}."]
        if isinstance(r.summary_en, str):
            parts.append(r.summary_en[:700])
        if isinstance(r.summary_vi, str):
            parts.append(r.summary_vi[:400])
        if join(r.directors):
            parts.append(f"Directed by {join(r.directors)}.")
        if join(r.top_cast):
            parts.append(f"Starring {join(r.top_cast)}.")
        if join(r.countries):
            parts.append(f"Country: {join(r.countries)}.")
        return " ".join(parts)

    df["doc"] = df.apply(doc, axis=1)
    return df[["movie_id", "doc"]]


def main():
    docs = movie_documents()
    print(f"Tạo embedding cho {len(docs):,} phim bằng {MODEL_NAME} ...")
    vectors = encode(docs["doc"].tolist(), kind="passage")
    with psycopg2.connect(config.dw_dsn()) as conn, conn.cursor() as cur:
        cur.execute("SELECT movie_id, movie_key FROM dw.dim_movie")
        keys = dict(cur.fetchall())
        rows = [(keys[mid], d, "[" + ",".join(f"{x:.6f}" for x in v) + "]")
                for mid, d, v in zip(docs["movie_id"], docs["doc"], vectors) if mid in keys]
        execute_values(cur, """
            INSERT INTO dw.movie_embedding (movie_key, doc, embedding) VALUES %s
            ON CONFLICT (movie_key) DO UPDATE SET doc = EXCLUDED.doc, embedding = EXCLUDED.embedding""",
            rows, template="(%s, %s, %s::vector)", page_size=500)
        cur.execute("CREATE INDEX IF NOT EXISTS ix_movie_embedding_hnsw ON dw.movie_embedding "
                    "USING hnsw (embedding vector_cosine_ops)")
    print(f"dw.movie_embedding: {len(rows):,} vector")


if __name__ == "__main__":
    main()
