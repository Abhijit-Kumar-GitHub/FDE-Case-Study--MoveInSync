"""One command: refresh everything that answers "How are our Play Store ratings?"

  python run.py                 scrape -> label new reviews -> metrics -> dashboard, queue, digest
  python run.py --skip-scrape   rebuild from data already on disk
  python run.py --memo          also re-render the recommendation (HTML + PDF)

Labelling: with ANTHROPIC_API_KEY set, new reviews go to Claude Sonnet 5.5 (Batch API,
budget-capped); without it, keyword rules label them and anything they can't place
goes to the needs-review queue.
"""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import analyze  # noqa: E402
import report  # noqa: E402


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--skip-scrape", action="store_true")
    p.add_argument("--memo", action="store_true")
    p.add_argument("--owner", default=os.environ.get("GITHUB_REPOSITORY_OWNER", "OWNER"), help="GitHub user/org for links")
    a = p.parse_args()

    if not a.skip_scrape:
        import scrape
        scrape.run()
    if os.environ.get("ANTHROPIC_API_KEY"):
        import classify_api
        classify_api.run()
    else:
        print("no ANTHROPIC_API_KEY: new reviews are labelled by keyword rules (see README)")
    analyze.main()
    report.main(a.owner)
    if a.memo:
        import memo
        memo.render(a.owner)


if __name__ == "__main__":
    main()
