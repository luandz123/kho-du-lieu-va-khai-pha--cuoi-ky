-- Database giao dịch của "app xem phim" (nguồn thứ 3, nguồn cho CDC).
-- Đây là OLTP: thiết kế chuẩn hóa, phục vụ ghi nhanh từng dòng, KHÔNG phải kho dữ liệu.

CREATE TABLE users (
    user_id     integer PRIMARY KEY,
    gender      char(1) NOT NULL CHECK (gender IN ('F', 'M')),
    age         smallint NOT NULL,          -- mã nhóm tuổi theo MovieLens: 1, 18, 25, 35, 45, 50, 56
    occupation  smallint NOT NULL CHECK (occupation BETWEEN 0 AND 20),
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE movies (
    movie_id    integer PRIMARY KEY,
    title       text NOT NULL,
    year        smallint,
    imdb_id     text
);

CREATE TABLE ratings (
    user_id     integer NOT NULL REFERENCES users (user_id),
    movie_id    integer NOT NULL REFERENCES movies (movie_id),
    rating      smallint NOT NULL CHECK (rating BETWEEN 1 AND 5),
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, movie_id)
);

CREATE OR REPLACE FUNCTION touch_updated_at() RETURNS trigger AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END $$ LANGUAGE plpgsql;

CREATE TRIGGER ratings_touch BEFORE UPDATE ON ratings FOR EACH ROW EXECUTE FUNCTION touch_updated_at();
CREATE TRIGGER users_touch   BEFORE UPDATE ON users   FOR EACH ROW EXECUTE FUNCTION touch_updated_at();

-- REPLICA IDENTITY FULL: khi UPDATE/DELETE, WAL ghi cả giá trị cũ -> Debezium có trường "before".
ALTER TABLE ratings REPLICA IDENTITY FULL;
ALTER TABLE users   REPLICA IDENTITY FULL;

-- Publication: danh sách bảng mà Debezium (plugin pgoutput) được phép đọc thay đổi.
CREATE PUBLICATION dbz_publication FOR TABLE ratings, users;
