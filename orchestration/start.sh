#!/usr/bin/env bash
# Khởi động Airflow 1 container: khởi tạo metadata, tạo tài khoản admin, chạy scheduler + webserver.
set -euo pipefail
export AIRFLOW__CORE__DAGS_FOLDER=/opt/project/orchestration/dags

airflow db migrate
airflow users create --role Admin --username admin --password "${_AIRFLOW_WWW_USER_PASSWORD}" \
    --firstname Admin --lastname Movie --email admin@example.com 2>/dev/null || true

airflow scheduler &
exec airflow webserver --port 8080
