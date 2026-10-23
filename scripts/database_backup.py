"""SQLite snapshots and restore-to-new-file; never overwrite a database."""
from contextlib import closing
import argparse
import sqlite3
from pathlib import Path


def copy_database(source, target):
    source, target = Path(source).resolve(), Path(target).resolve()
    if not source.is_file():
        raise ValueError("Source database does not exist")
    target.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation prevents accidental overwrites, including a running DB.
    with target.open("xb"):
        pass
    with closing(sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)) as src:
        with closing(sqlite3.connect(target)) as dest:
            src.backup(dest)
            if dest.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("Database integrity check failed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source")
    parser.add_argument("target")
    args = parser.parse_args()
    copy_database(args.source, args.target)
    print("SQLite copy created and verified")


if __name__ == "__main__":
    main()
