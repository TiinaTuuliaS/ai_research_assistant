import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src import api
from src.models import Base, LoginSession, Research, User
from src.security import is_password_hash, token_hash, verify_password


class AuthenticationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.engine = create_engine(
            f"sqlite:///{Path(self.temp.name) / 'test.db'}",
            connect_args={"check_same_thread": False},
        )
        self.sessions = sessionmaker(bind=self.engine)
        self.engine_patch = patch.object(api, "engine", self.engine)
        self.sessions_patch = patch.object(api, "SessionLocal", self.sessions)
        self.engine_patch.start()
        self.sessions_patch.start()

        def test_db():
            with self.sessions() as db:
                yield db

        api.app.dependency_overrides[api.get_db] = test_db
        self.client = TestClient(api.app, headers={"X-Requested-With": "ResearchApp"})
        self.client.__enter__()
        self.password = "test-password-123!"

    def tearDown(self):
        self.client.__exit__(None, None, None)
        api.app.dependency_overrides.clear()
        self.sessions_patch.stop()
        self.engine_patch.stop()
        self.engine.dispose()
        self.temp.cleanup()

    def register_login(self, email="alice@example.test"):
        credentials = {"email": email, "password": self.password}
        self.assertEqual(self.client.post("/signup", json=credentials).status_code, 201)
        response = self.client.post("/login", json=credentials)
        self.assertEqual(response.status_code, 200)
        return response

    def test_cookie_hash_and_revocation(self):
        response = self.register_login()
        self.assertIn("HttpOnly", response.headers["set-cookie"])
        self.assertIn("SameSite=strict", response.headers["set-cookie"])
        token = self.client.cookies.get(api.COOKIE_NAME)
        with self.sessions() as db:
            user = db.query(User).one()
            self.assertTrue(is_password_hash(user.password))
            self.assertTrue(verify_password(self.password, user.password))
            self.assertEqual(db.query(LoginSession).one().token_hash, token_hash(token))
        self.assertEqual(self.client.get("/me").status_code, 200)
        self.assertEqual(self.client.post("/logout").status_code, 204)
        self.client.cookies.set(api.COOKIE_NAME, token)
        self.assertEqual(self.client.get("/me").status_code, 401)

    def test_cannot_impersonate_or_read_another_user(self):
        alice = self.register_login().json()["user_id"]
        with patch.object(api, "generate_report", return_value="Alice report"):
            self.assertEqual(self.client.post("/research", json={"topic": "Market"}).status_code, 200)
        self.client.post("/logout")
        bob = self.register_login("bob@example.test").json()["user_id"]
        self.assertNotEqual(alice, bob)
        self.assertEqual(self.client.get("/researches").json(), [])
        self.assertEqual(self.client.get(f"/researches/{alice}").status_code, 403)
        with patch.object(api, "generate_report") as generate:
            self.assertEqual(self.client.post("/research", json={"topic": "Market", "user_id": alice}).status_code, 422)
            generate.assert_not_called()
        self.client.cookies.clear()
        with patch.object(api, "generate_report") as generate:
            self.assertEqual(self.client.post("/research", json={"topic": "Market"}).status_code, 401)
            generate.assert_not_called()
        self.assertEqual(self.client.get(f"/researches/{alice}").status_code, 401)

    def test_expired_and_forged_sessions(self):
        self.register_login()
        with self.sessions() as db:
            db.query(LoginSession).update({"expires_at": int(time.time()) - 1})
            db.commit()
        self.assertEqual(self.client.get("/researches").status_code, 401)
        self.client.cookies.clear()
        self.client.cookies.set(api.COOKIE_NAME, "1")
        self.assertEqual(self.client.get("/me").status_code, 401)

    def test_password_migration_preserves_reports_and_login(self):
        with self.sessions() as db:
            user = User(email="legacy", password="old")
            db.add(user)
            db.flush()
            db.add(Research(topic="Existing", result="Keep me", user_id=user.id))
            db.commit()
            api.migrate_passwords(db)
            hashed = user.password
            api.migrate_passwords(db)
            self.assertEqual(user.password, hashed)
            self.assertTrue(verify_password("old", hashed))
        self.assertEqual(self.client.post("/login", json={"email": "legacy", "password": "old"}).status_code, 200)
        self.assertEqual(self.client.get("/researches").json()[0]["result"], "Keep me")

    def test_validation_and_csrf(self):
        self.assertEqual(self.client.post("/signup", json={"email": "x", "password": "short"}).status_code, 422)
        self.register_login()
        self.assertEqual(self.client.post("/signup", json={"email": " ALICE@example.test ", "password": self.password}).status_code, 409)
        self.assertEqual(self.client.post("/login", json={"email": "alice@example.test", "password": "wrong"}).status_code, 401)
        self.assertEqual(self.client.post("/research", json={"topic": "   "}).status_code, 422)
        self.assertEqual(self.client.post("/logout", headers={"Origin": "https://attacker.test"}).status_code, 403)
        self.assertEqual(self.client.post("/logout", headers={"X-Requested-With": ""}).status_code, 403)
        self.assertEqual(self.client.get("/me").headers["cache-control"], "no-store")

    def test_failed_report_is_not_saved(self):
        self.register_login()
        with patch.object(api, "generate_report", side_effect=ValueError("invalid citations")):
            response = self.client.post("/research", json={"topic": "Market"})
        self.assertEqual(response.status_code, 502)
        self.assertNotIn("invalid citations", response.text)
        self.assertEqual(self.client.get("/researches").json(), [])

    def test_logout_during_research_prevents_save(self):
        self.register_login()

        def revoked_report(*args):
            with self.sessions() as db:
                db.query(LoginSession).delete()
                db.commit()
            return "Do not save"

        with patch.object(api, "generate_report", side_effect=revoked_report):
            self.assertEqual(self.client.post("/research", json={"topic": "Market"}).status_code, 401)
        with self.sessions() as db:
            self.assertEqual(db.query(Research).count(), 0)


if __name__ == "__main__":
    unittest.main()
