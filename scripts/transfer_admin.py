"""Transfer one account's credentials, never reports, sessions or source IDs."""
import argparse
import json
import os
from pathlib import Path
from sqlalchemy import func, text
from src.security import is_password_hash


def export_account(db, admin_ids, target):
    from src.models import User
    if len(admin_ids) != 1:
        raise ValueError("Select exactly one configured admin with --user-id")
    user = db.get(User, next(iter(admin_ids)))
    if not user or not is_password_hash(user.password):
        raise ValueError("Configured admin with a supported password hash not found")
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8") as output:
        json.dump({"version": 1, "email": user.email, "password_hash": user.password}, output)
    try:
        target.chmod(0o600)
    except OSError:
        pass


def import_account(db, source):
    from src.models import User
    data = json.loads(Path(source).read_text(encoding="utf-8"))
    if set(data) != {"version", "email", "password_hash"} or data["version"] != 1:
        raise ValueError("Invalid transfer format")
    email = data["email"]
    if not isinstance(email, str) or not email.strip() or len(email) > 254 or not is_password_hash(data["password_hash"]):
        raise ValueError("Invalid account credentials")
    if db.bind.dialect.name == "sqlite":
        db.execute(text("BEGIN IMMEDIATE"))
    if db.query(User).filter(func.lower(func.trim(User.email)) == email.strip().lower()).first():
        raise ValueError("Account already exists; no credentials were overwritten")
    user = User(email=email, password=data["password_hash"])
    db.add(user)
    db.commit()
    return user.id


def main():
    from dotenv import load_dotenv
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["export", "import"])
    parser.add_argument("file")
    parser.add_argument("--user-id", type=int)
    args = parser.parse_args()
    from src.database import Base, engine, SessionLocal
    import src.models
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if args.action == "export":
            admins = {int(value.strip()) for value in os.getenv("ADMIN_USER_IDS", "").split(",") if value.strip()}
            if args.user_id is not None:
                if args.user_id not in admins:
                    raise ValueError("Selected account is not a configured admin")
                admins = {args.user_id}
            export_account(db, admins, args.file)
            print("Private transfer file created. No source account was changed.")
        else:
            user_id = import_account(db, args.file)
            print(f"Account imported. Set Railway ADMIN_USER_IDS={user_id} and redeploy.")


if __name__ == "__main__":
    main()
