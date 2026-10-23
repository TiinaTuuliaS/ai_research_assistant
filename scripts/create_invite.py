"""Create a single-use signup code in the configured database."""
import secrets
from dotenv import load_dotenv


def main():
    load_dotenv()
    from src.database import Base, engine, SessionLocal
    from src.models import SignupInvite
    from src.security import token_hash
    Base.metadata.create_all(bind=engine)
    code = secrets.token_urlsafe(24)
    with SessionLocal() as db:
        db.add(SignupInvite(token_hash=token_hash(code)))
        db.commit()
    print(code)


if __name__ == "__main__":
    main()
