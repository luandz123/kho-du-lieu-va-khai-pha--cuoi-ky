"""Initialize only the isolated Superset metadata DB; never the MovieLens DW."""
import contextlib
import io
import os
import subprocess
import sys


def main():
    for command in (["superset", "db", "upgrade"], ["superset", "init"]):
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode:
            print("Superset metadata initialization failed; no raw credential-bearing log printed.")
            return 1
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            from superset.app import create_app
            from superset.extensions import appbuilder
            app = create_app()
            with app.app_context():
                manager = appbuilder.sm
                if not manager.find_user(username="btl_admin"):
                    user = manager.add_user(
                        "btl_admin", "BTL", "Admin", "btl-admin@localhost.invalid",
                        manager.find_role("Admin"), os.environ["ADMIN_PASSWORD"],
                    )
                    if not user:
                        raise RuntimeError("admin initialization failed")
        print("Superset metadata ready. Local admin initialized; existing password not reset.")
        return 0
    except Exception:
        print("Local Superset admin initialization failed; credentials not printed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
