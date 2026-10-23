from contextlib import closing
import tempfile
import sqlite3
import unittest
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.frontend import install_frontend
from scripts.database_backup import copy_database


class DeploymentTests(unittest.TestCase):
    def test_spa_routes_assets_and_api_are_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "static").mkdir()
            (root / "static" / "app.js").write_text("console.log(1)")
            (root / "index.html").write_text("<html>Demo</html>")
            app = FastAPI()
            @app.get("/me")
            def me():
                return {"api": True}
            install_frontend(app, root)
            client = TestClient(app)
            for path in ("/", "/history", "/login", "/signup"):
                self.assertIn("<html>Demo</html>", client.get(path).text)
            self.assertEqual(client.get("/static/app.js").status_code, 200)
            self.assertEqual(client.get("/me").json(), {"api": True})
            self.assertEqual(client.get("/unknown-api").status_code, 404)
            self.assertEqual(client.get("/static/missing.js").status_code, 404)

    def test_backup_restore_and_overwrite_refusal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, backup, restored = [root / name for name in ("live.db", "backup.db", "restored.db")]
            with closing(sqlite3.connect(source)) as db:
                db.execute("CREATE TABLE example (value TEXT)")
                db.execute("INSERT INTO example VALUES ('saved report')")
                db.commit()
            copy_database(source, backup)
            copy_database(backup, restored)
            with closing(sqlite3.connect(restored)) as db:
                self.assertEqual(db.execute("SELECT value FROM example").fetchone()[0], "saved report")
            with self.assertRaises(FileExistsError):
                copy_database(backup, source)
