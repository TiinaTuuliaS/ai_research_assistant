import json
import tempfile
import unittest
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.models import Base, User, Research, LoginSession
from src.security import hash_password, verify_password
from scripts.transfer_admin import export_account, import_account


class AdminTransferTests(unittest.TestCase):
    def test_only_selected_credentials_transfer_and_existing_users_are_preserved(self):
        source, target = create_engine("sqlite://"), create_engine("sqlite://")
        self.addCleanup(source.dispose)
        self.addCleanup(target.dispose)
        Base.metadata.create_all(source)
        Base.metadata.create_all(target)
        with tempfile.TemporaryDirectory() as directory, Session(source) as src, Session(target) as dst:
            admin = User(email="admin@test.local", password=hash_password("original-password"))
            src.add(admin)
            src.flush()
            src.add(Research(topic="Private report", result="Private", user_id=admin.id))
            src.commit()
            original_id = admin.id
            path = Path(directory) / "admin.json"
            export_account(src, {admin.id}, path)
            self.assertEqual(set(json.loads(path.read_text())), {"version", "email", "password_hash"})
            with self.assertRaises(FileExistsError):
                export_account(src, {admin.id}, path)
            dst.add(User(email="other@test.local", password=hash_password("other-password")))
            dst.commit()
            identifier = import_account(dst, path)
            self.assertNotEqual(identifier, original_id)
            self.assertTrue(verify_password("original-password", dst.get(User, identifier).password))
            self.assertEqual(dst.query(Research).count(), 0)
            self.assertEqual(dst.query(LoginSession).count(), 0)
            with self.assertRaises(ValueError):
                import_account(dst, path)
            dst.rollback()
            self.assertEqual(dst.query(User).count(), 2)
            self.assertEqual(src.query(User).count(), 1)
            self.assertEqual(src.query(Research).count(), 1)

    def test_plaintext_password_is_rejected(self):
        engine = create_engine("sqlite://")
        self.addCleanup(engine.dispose)
        Base.metadata.create_all(engine)
        with tempfile.TemporaryDirectory() as directory, Session(engine) as db:
            path = Path(directory) / "invalid.json"
            path.write_text(json.dumps({"version": 1, "email": "admin@test.local", "password_hash": "plaintext"}))
            with self.assertRaises(ValueError):
                import_account(db, path)
            self.assertEqual(db.query(User).count(), 0)
