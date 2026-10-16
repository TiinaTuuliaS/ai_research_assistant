import unittest
from datetime import datetime

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from src.database import migrate_research_dates
from src.models import Base, Research, ResearchJob, User
from src.api import get_researches, job_payload


class ResearchDateTests(unittest.TestCase):
    def test_migration_preserves_legacy_data_and_unknown_dates(self):
        engine = create_engine("sqlite://")
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE researches (id INTEGER PRIMARY KEY, topic VARCHAR)"))
            connection.execute(text("CREATE TABLE research_jobs (id VARCHAR PRIMARY KEY)"))
            connection.execute(text("INSERT INTO researches (id, topic) VALUES (1, 'Old report')"))
        migrate_research_dates(engine)
        migrate_research_dates(engine)
        with engine.connect() as connection:
            self.assertEqual(connection.execute(text("SELECT topic, created_at FROM researches")).one(),
                             ("Old report", None))
        engine.dispose()

    def test_new_dates_are_utc_and_history_preserves_original_job_date(self):
        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)
        with Session(engine) as db:
            user = User(email="test@example.test", password="unused")
            db.add(user)
            db.flush()
            job = ResearchJob(id="date-test", user_id=user.id, topic="Topic", steps=[], status="completed")
            old = Research(topic="Legacy", result="Old", user_id=user.id, created_at=None)
            db.add_all([job, old])
            db.flush()
            self.assertIsNotNone(datetime.fromisoformat(job.created_at).tzinfo)
            report = Research(topic="Topic", result="Report", user_id=user.id, created_at=job.created_at)
            db.add(report)
            db.flush()
            job.research_id = report.id
            db.commit()
            history = get_researches(user, db)
            self.assertEqual(history[0]["created_at"], job.created_at)
            self.assertIsNone(history[1]["created_at"])
            self.assertEqual(job_payload(job, db)["created_at"], job.created_at)
        engine.dispose()
