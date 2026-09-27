import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src import api
from src.models import Base, LoginSession, Research, ResearchJob, ResearchUsage, User
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

    def test_research_brief_reaches_generator_and_rejects_invalid_budget(self):
        self.register_login()
        brief = {"topic": "Service", "goal": "Test demand", "target_market": "Finland", "budget_eur": 0}
        with patch.object(api, "generate_report", return_value="Practical plan") as generate:
            response = self.client.post("/research", json=brief)
            self.assertEqual(response.status_code, 200)
            generate.assert_called_once_with("Service", "suomi", "Test demand", "Finland", 0)
        with patch.object(api, "generate_report") as generate:
            for invalid in (-1, 10_000_001, "not-a-number"):
                self.assertEqual(self.client.post("/research", json={**brief, "budget_eur": invalid}).status_code, 422)
            self.assertEqual(self.client.post("/research", json={**brief, "goal": "x" * 1001}).status_code, 422)
            generate.assert_not_called()

    def test_omitted_budget_remains_unknown(self):
        self.register_login()
        with patch.object(api, "generate_report", return_value="Plan") as generate:
            self.client.post("/research", json={"topic": "Service"})
            generate.assert_called_once_with("Service", "suomi", "", "", None)

    def test_research_modes_change_agent_brief(self):
        self.register_login()
        for mode, expected in [("demand", "Assess demand"), ("competition", "Compare competitors"), ("market", "Map this industry")]:
            with patch.object(api, "generate_report", return_value="Report") as generate:
                response = self.client.post("/research", json={"topic": "Service", "research_type": mode, "problem": "Customer pain", "competitors": "Company A", "goal": "Recent changes"})
                self.assertEqual(response.status_code, 200)
                self.assertIn(expected, generate.call_args.args[2])
                self.assertEqual(generate.call_args.kwargs["research_type"], mode)
        self.assertEqual(self.client.post("/research", json={"topic": "Service", "research_type": "unknown"}).status_code, 422)

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

    def test_job_progress_history_and_ownership(self):
        self.register_login()
        def generate(*args, progress):
            for i in range(5):
                progress(i, "running", None)
                with self.sessions() as db:
                    job = db.query(ResearchJob).one()
                    self.assertEqual(job.steps[i]["status"], "running")
                progress(i, "completed", f"Perspective {i}")
                progress(i, "running", None)  # Delayed events cannot erase output.
            return "Final report\n\n## Lähteet\nSources"
        with patch.object(api, "generate_report", side_effect=generate):
            response = self.client.post("/research-jobs", json={"topic": "Market"})
        self.assertEqual(response.status_code, 202)
        path = f'/research-jobs/{response.json()["id"]}'
        job = self.client.get(path).json()
        self.assertEqual(job["status"], "completed")
        self.assertEqual(job["steps"][0]["output"], "Perspective 0")
        self.assertEqual(self.client.get("/researches").json()[0]["steps"], job["steps"])
        self.client.post("/logout")
        self.assertEqual(self.client.get(path).status_code, 401)
        self.register_login("bob@example.test")
        self.assertEqual(self.client.get(path).status_code, 404)

    def test_failed_job_keeps_progress_but_does_not_save_report(self):
        self.register_login()
        def fail(*args, progress):
            progress(0, "completed", "Actual finding")
            progress(1, "running", None)
            raise ValueError("secret provider detail")
        with patch.object(api, "generate_report", side_effect=fail):
            response = self.client.post("/research-jobs", json={"topic": "Market"})
        job = self.client.get(f'/research-jobs/{response.json()["id"]}').json()
        self.assertEqual(job["status"], "failed")
        self.assertEqual(job["steps"][0]["status"], "completed")
        self.assertEqual(job["steps"][1]["status"], "failed")
        self.assertNotIn("secret", job["error"])
        self.assertEqual(self.client.get("/researches").json(), [])

    def test_existing_job_is_reused_without_new_generation(self):
        owner = self.register_login().json()["user_id"]
        with self.sessions() as db:
            db.add(ResearchJob(id="existing", user_id=owner, topic="Old", status="running", steps=api.new_steps()))
            db.commit()
        with patch.object(api, "generate_report") as generate:
            response = self.client.post("/research-jobs", json={"topic": "Another"})
            self.assertEqual(response.json()["id"], "existing")
            generate.assert_not_called()

    def test_revoked_job_cannot_save(self):
        self.register_login()
        def revoke(*args, **kwargs):
            with self.sessions() as db:
                db.query(LoginSession).delete()
                db.commit()
            return "Not saved"
        with patch.object(api, "generate_report", side_effect=revoke):
            self.client.post("/research-jobs", json={"topic": "Market"})
        with self.sessions() as db:
            self.assertEqual(db.query(Research).count(), 0)
            self.assertEqual(db.query(ResearchJob).one().status, "failed")

    def test_three_attempts_shared_by_both_routes_and_persist_after_login(self):
        self.register_login()
        with patch.object(api, "generate_report", return_value="Report") as generate:
            for path in ("/research-jobs", "/research", "/research-jobs"):
                self.assertIn(self.client.post(path, json={"topic": "Market"}).status_code, (200, 202))
            for path in ("/research", "/research-jobs"):
                response = self.client.post(path, json={"topic": "Fourth"})
                self.assertEqual(response.status_code, 429)
                self.assertEqual(response.json()["detail"]["quota"]["remaining"], 0)
            self.assertEqual(generate.call_count, 3)
        self.client.post("/logout")
        response = self.client.post("/login", json={"email": "alice@example.test", "password": self.password})
        self.assertEqual(response.json()["quota"], {"limit": 3, "used": 3, "remaining": 0})
        self.assertEqual(len(self.client.get("/researches").json()), 3)
        self.register_login("other@example.test")
        self.assertEqual(self.client.get("/me").json()["quota"]["remaining"], 3)

    def test_failed_attempts_count_but_invalid_requests_do_not(self):
        self.register_login()
        self.client.post("/research-jobs", json={"topic": ""})
        self.assertEqual(self.client.get("/me").json()["quota"]["remaining"], 3)
        with patch.object(api, "generate_report", side_effect=ValueError("failure")):
            self.client.post("/research-jobs", json={"topic": "Market"})
            self.client.post("/research", json={"topic": "Market"})
        self.assertEqual(self.client.get("/me").json()["quota"]["remaining"], 1)

    def test_legacy_attempts_imported_once_without_double_counting(self):
        owner = self.register_login().json()["user_id"]
        with self.sessions() as db:
            db.query(ResearchUsage).delete()
            report = Research(topic="Old", result="Saved", user_id=owner)
            db.add(report)
            db.flush()
            db.add(ResearchJob(id="old", user_id=owner, research_id=report.id,
                               topic="Old", status="completed", steps=api.new_steps()))
            db.add(Research(topic="Legacy", result="Saved", user_id=owner))
            db.commit()
        for _ in range(2):
            self.assertEqual(self.client.get("/me").json()["quota"]["used"], 2)

    def test_concurrent_reservations_cannot_exceed_limit(self):
        owner = self.register_login().json()["user_id"]
        def reserve(_):
            with self.sessions() as db:
                try:
                    api.reserve_research(db, owner)
                    db.commit()
                    return True
                except api.HTTPException as error:
                    self.assertEqual(error.status_code, 429)
                    return False
        with ThreadPoolExecutor(max_workers=6) as pool:
            self.assertEqual(sum(pool.map(reserve, range(6))), 3)
        self.assertEqual(self.client.get("/me").json()["quota"]["used"], 3)


if __name__ == "__main__":
    unittest.main()
