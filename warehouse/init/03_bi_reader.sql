-- Tài khoản chỉ đọc cho Superset. Mật khẩu đặt riêng bằng lệnh:
--   ALTER ROLE bi_reader PASSWORD '<BI_READER_PASSWORD trong .env>';
CREATE ROLE bi_reader LOGIN;
ALTER ROLE bi_reader SET default_transaction_read_only = on;
GRANT USAGE ON SCHEMA dw, analytics, etl TO bi_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA dw, analytics, etl TO bi_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA dw, analytics, etl GRANT SELECT ON TABLES TO bi_reader;
