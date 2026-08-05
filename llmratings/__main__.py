"""CLI entry point. Ticket 12: --category picks one of five use-case
categories, each rendered at its fixed reasoning effort."""

import argparse
import os
import sys
from pathlib import Path

from . import fetch, identity, render


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="llm-ratings",
        description="Model-advice tables from DeepSWE, Terminal-Bench v2.1 and "
                    "Artificial Analysis (PoC).")
    ap.add_argument("--category", choices=[c[0] for c in render.CATEGORIES],
                    default="Chores",
                    help="use-case category (default: %(default)s); each "
                         "renders at its fixed reasoning effort")
    ap.add_argument("--fixtures", metavar="DIR",
                    default=".scratch/llm-ratings/fixtures/main",
                    help="serve saved source payloads from DIR instead of the "
                         "network (the test seam; live fetches land in ticket 15)")
    args = ap.parse_args(argv)

    if not os.environ.get("LLM_RATINGS_AA_API_KEY"):
        print("error: LLM_RATINGS_AA_API_KEY is not set — get a free API key at "
              "artificialanalysis.ai and export it", file=sys.stderr)
        return 1

    try:
        raw = fetch.fetch_all(args.fixtures)
        aliases = identity.load_aliases(Path(__file__).parent / "aliases.json")
        ds = identity.build(aliases, raw)
    except fetch.SourceError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    print(render.ATTRIBUTION)
    print()
    print("\n".join(render.render(ds, args.category)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
