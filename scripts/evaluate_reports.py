"""Manual, paid end-to-end evaluation. Never writes to the application's database.

Run from the project root: uv run python -m scripts.evaluate_reports demand
Review the generated agent outputs and final report in .runtime/evaluations/.
"""
import argparse
import os
from datetime import datetime, timezone
from pathlib import Path

os.environ["CREWAI_TRACING_ENABLED"] = "false"

from src.api import generate_report


CASES = {
    "demand": dict(topic="Japanilainen curryravintola Tampereelle",
                   goal="Onko japanilaiseen curryyn keskittyvälle lounasravintolalle näyttöä kysynnästä?",
                   target_market="Tampereen lounasasiakkaat"),
    "competition": dict(topic="Vaatteiden korjauspalvelu Turussa",
                        goal="Miten pieni korjausompelimo voisi erottua paikallisista vaihtoehdoista?",
                        target_market="Turku, vaatteitaan korjauttavat kuluttajat"),
    "market": dict(topic="Käytettyjen huonekalujen markkina Suomessa",
                   goal="Miten markkina on kehittynyt ja mistä muutoksista löytyy näyttöä?",
                   target_market="Suomi"),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=CASES)
    args = parser.parse_args()
    folder = Path(".runtime/evaluations")
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    output = folder / f"{stamp}-{args.mode}.md"
    output.write_text(f"# {CASES[args.mode]['topic']}\n", encoding="utf-8")

    def progress(index, status, text):
        print(f"{args.mode}: stage {index + 1} {status}", flush=True)
        if status == "completed" and text:
            with output.open("a", encoding="utf-8") as handle:
                handle.write(f"\n## Agent {index + 1}\n\n{text}\n")

    result = generate_report(**CASES[args.mode], language="suomi",
                             research_type=args.mode, progress=progress)
    with output.open("a", encoding="utf-8") as handle:
        handle.write(f"\n# Final report\n\n{result}\n")
    print(f"Saved: {output}", flush=True)


if __name__ == "__main__":
    main()
