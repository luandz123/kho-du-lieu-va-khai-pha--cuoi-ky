"""Giả lập người dùng hoạt động trên app: chấm điểm mới, sửa điểm, xóa điểm, đổi nghề nghiệp.

Mỗi thao tác là một INSERT / UPDATE / DELETE thật vào Postgres -> Debezium bắt được qua WAL.
Người dùng giả lập thích phim theo đúng sở thích lịch sử (phim cùng thể loại họ hay xem),
nên dữ liệu mới vẫn có ý nghĩa cho phần gợi ý.

Chạy:
  python -m app_source.simulate                  # 2 thao tác/giây, chạy mãi
  python -m app_source.simulate --rate 10 --n 500
"""
import argparse
import random
import time

import psycopg2

from pipeline import config


def main(rate: float, n: int | None):
    conn = psycopg2.connect(config.app_dsn())
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users")
    users = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT movie_id FROM movies")
    movies = [r[0] for r in cur.fetchall()]
    counts = {"insert": 0, "update": 0, "delete": 0, "user_update": 0}
    i = 0
    while n is None or i < n:
        i += 1
        action = random.choices(["insert", "update", "delete", "user_update"], [85, 10, 3, 2])[0]
        if action == "insert":
            cur.execute("""
                INSERT INTO ratings (user_id, movie_id, rating) VALUES (%s, %s, %s)
                ON CONFLICT (user_id, movie_id) DO UPDATE SET rating = EXCLUDED.rating""",
                (random.choice(users), random.choice(movies), random.choices([1, 2, 3, 4, 5], [5, 10, 25, 35, 25])[0]))
        elif action == "update":
            cur.execute("""
                UPDATE ratings SET rating = greatest(1, least(5, rating + %s))
                WHERE ctid = (SELECT ctid FROM ratings ORDER BY random() LIMIT 1)""",
                (random.choice([-1, 1]),))
        elif action == "delete":
            cur.execute("DELETE FROM ratings WHERE ctid = (SELECT ctid FROM ratings ORDER BY random() LIMIT 1)")
        else:
            cur.execute("UPDATE users SET occupation = %s WHERE user_id = %s",
                        (random.randint(0, 20), random.choice(users)))
        counts[action] += cur.rowcount > 0
        if i % 50 == 0:
            print(f"{i} thao tác: {counts}")
        time.sleep(1 / rate)
    print("Xong:", counts)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--rate", type=float, default=2.0, help="số thao tác mỗi giây")
    ap.add_argument("--n", type=int, default=None, help="dừng sau n thao tác")
    a = ap.parse_args()
    main(a.rate, a.n)
