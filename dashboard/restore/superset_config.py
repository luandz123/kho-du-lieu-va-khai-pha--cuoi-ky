"""Isolated S11B-4 metadata; never point this instance at production metadata."""
import os
from urllib.parse import quote
SECRET_KEY = os.environ['SUPERSET_SECRET_KEY']
SQLALCHEMY_DATABASE_URI = ('postgresql+psycopg2://superset_meta:' +
    quote(os.environ['METADATA_PASSWORD'], safe='') + '@metadata:5432/superset_metadata')
APP_NAME = 'BTL 11B-4 RESTORE TEST · 8091'
SQLALCHEMY_TRACK_MODIFICATIONS = False
WTF_CSRF_ENABLED = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_NAME = 'btl_s11b4_restore_session'
CACHE_CONFIG = {'CACHE_TYPE': 'NullCache'}
DATA_CACHE_CONFIG = {'CACHE_TYPE': 'NullCache'}
FEATURE_FLAGS = {'ALERT_REPORTS': False}
