"""Load the backed-up config/key; change only test-instance presentation/cookie."""
from pathlib import Path
exec(compile(Path('/app/test_restore/source_config.py').read_text(), 'backed_up_config', 'exec'))
APP_NAME = 'BTL METADATA RESTORE TEST · 8092'
SESSION_COOKIE_NAME = 'btl_s12a_metadata_restore_session'
