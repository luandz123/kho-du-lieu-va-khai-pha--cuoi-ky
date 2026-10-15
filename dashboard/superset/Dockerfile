FROM apache/superset:6.1.0
USER root
RUN uv pip install --python /app/.venv/bin/python --no-cache psycopg2-binary==2.9.13
COPY --chown=superset:superset superset_config.py init_metadata.py /app/project/
USER superset
