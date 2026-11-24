# Một image dùng chung cho Airflow và 2 service chạy nền (consumer CDC, producer Wikipedia).
FROM apache/airflow:2.10.4-python3.12

# Thư mục tải file tạm (IMDb...). Volume rỗng gắn vào sẽ thừa hưởng quyền sở hữu này.
USER root
RUN mkdir -p /opt/data && chown airflow:root /opt/data
USER airflow

COPY requirements-pipeline.txt /tmp/requirements-pipeline.txt
RUN pip install --no-cache-dir -r /tmp/requirements-pipeline.txt

# Cài sẵn extension httpfs của DuckDB để đọc/ghi MinIO (S3) mà không cần tải lúc chạy.
RUN python -c "import duckdb; duckdb.sql('INSTALL httpfs')"
