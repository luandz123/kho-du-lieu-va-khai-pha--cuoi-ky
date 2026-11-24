"""Kiểm tra chất lượng dữ liệu sau mỗi lần nạp kho. Sai bất kỳ điều nào -> thoát mã lỗi,
task trên Airflow chuyển đỏ và các task phía sau (huấn luyện lại gợi ý) không chạy.

Chạy: python -m warehouse.quality
"""
import sys

import psycopg2

from pipeline import config, lake
from transform.duck import connect as duck

CHECKS = {
    "Rating nằm trong khoảng 1-5":
        "SELECT count(*) FROM dw.fact_rating WHERE rating NOT BETWEEN 1 AND 5",
    "Mỗi người dùng có đúng 1 phiên bản hiện tại (SCD2)":
        "SELECT count(*) FROM (SELECT user_id FROM dw.dim_user GROUP BY user_id HAVING count(*) FILTER (WHERE is_current) <> 1) x",
    "Phiên bản SCD2 không chồng lấn thời gian":
        """SELECT count(*) FROM dw.dim_user a JOIN dw.dim_user b
           ON a.user_id = b.user_id AND a.user_key < b.user_key
          AND a.valid_from < coalesce(b.valid_to, 'infinity') AND b.valid_from < coalesce(a.valid_to, 'infinity')""",
    "Rating trỏ đúng phiên bản người dùng tại thời điểm chấm":
        """SELECT count(*) FROM dw.fact_rating f JOIN dw.dim_user u USING (user_key)
           WHERE f.rated_at < u.valid_from OR f.rated_at >= coalesce(u.valid_to, 'infinity')""",
    "Không có rating trong tương lai":
        "SELECT count(*) FROM dw.fact_rating WHERE rated_at > now() + interval '1 hour'",
    "Phim nào cũng có ít nhất 1 thể loại":
        "SELECT count(*) FROM dw.dim_movie m WHERE NOT EXISTS (SELECT 1 FROM dw.bridge_movie_genre b WHERE b.movie_key = m.movie_key)",
}


def main() -> int:
    failed = 0
    with psycopg2.connect(config.dw_dsn()) as conn, conn.cursor() as cur:
        for name, sql in CHECKS.items():
            cur.execute(sql)
            bad = cur.fetchone()[0]
            print(f"[{'OK ' if bad == 0 else 'LỖI'}] {name}" + (f": {bad} dòng sai" if bad else ""))
            failed += bad > 0

        # Đối soát gold ↔ kho. Bản mới nhất của mỗi cặp (user, phim) ở gold là trạng thái mà kho phải có.
        latest = f"""
            SELECT * FROM read_parquet('{lake.path('gold', 'fact_rating', 'data.parquet')}')
            QUALIFY row_number() OVER (PARTITION BY user_id, movie_id ORDER BY changed_at DESC) = 1"""
        g_pairs, g_deleted, g_max = duck().execute(
            f"SELECT count(*), count(*) FILTER (WHERE is_deleted), max(changed_at) FROM ({latest})").fetchone()
        cur.execute("SELECT count(*), count(*) FILTER (WHERE is_deleted), max(changed_at) FROM dw.fact_rating")
        d_pairs, d_deleted, d_max = cur.fetchone()
        results = [
            ("Đối soát số cặp (user, phim) gold ↔ kho", g_pairs == d_pairs, f"gold {g_pairs:,}, kho {d_pairs:,}"),
            # Rating bị xóa trên app (CDC op = 'd') phải được đánh dấu is_deleted trong kho.
            ("Đối soát rating đã xóa gold ↔ kho", g_deleted == d_deleted, f"gold {g_deleted:,}, kho {d_deleted:,}"),
            # Độ tươi: kho phải bắt kịp thay đổi mới nhất đã có trong lake.
            ("Kho bắt kịp thay đổi mới nhất trong lake", d_max is not None and d_max >= g_max,
             f"lake {g_max:%Y-%m-%d %H:%M:%S}, kho {d_max:%Y-%m-%d %H:%M:%S}" if d_max else "kho rỗng"),
        ]
        for name, ok, detail in results:
            print(f"[{'OK ' if ok else 'LỖI'}] {name}: {detail}")
            failed += not ok
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
