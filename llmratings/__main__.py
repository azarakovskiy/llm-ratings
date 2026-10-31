"""Local web launch or noninteractive batch advice from one shared policy.

Each launch loads the three rating sources and best-effort OpenRouter catalog
once. --fixtures reads offline payloads instead. --web serves one session on
loopback until Ctrl-C; without it, output is batch even in a terminal.
"""

import argparse
import os
import sys
from pathlib import Path

from . import fetch, identity, render
from .session import Session


def main(argv=None):
    # LLM_RATINGS_ROLES is a test seam only (same pattern as
    # LLM_RATINGS_HTTP_BASE): it swaps the roles file, never a second
    # config surface — roles.json remains the one user-editable file.
    roles_path = os.environ.get("LLM_RATINGS_ROLES") or \
        Path(__file__).parent / "roles.json"
    try:
        roles = render.load_roles(roles_path)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    ap = argparse.ArgumentParser(
        prog="llm-ratings",
        description="Compare models using Artificial Analysis, DeepSWE and "
                    "Terminal-Bench v2.1. Without --web, print batch advice "
                    "and exit, including in a terminal.",
        epilog="Python standard library only; no dependency installation. "
               "Set LLM_RATINGS_AA_API_KEY (dummy for fixtures). "
               "make run loads .env and adds --web. Offline example: "
               "LLM_RATINGS_AA_API_KEY=dummy python3 -m llmratings --web "
               "--fixtures .scratch/llm-ratings/fixtures/main --role Explorer. "
               "Fixtures contain historical/synthetic data, not live advice. "
               "Open the printed http://127.0.0.1:PORT/ URL; stop with Ctrl-C. "
               "See README.md for controls, source dates and failure behavior.")
    ap.add_argument("--role", choices=[r["name"] for r in roles],
                    default=roles[0]["name"],
                    help="initial role (default: %(default)s); its index and "
                         "objective select each model's measured reasoning effort")
    ap.add_argument("--web", action="store_true",
                    help="serve one local-only browser session; prints the "
                         "loopback URL and runs until Ctrl-C")
    ap.add_argument("--fixtures", metavar="DIR", default=None,
                    help="read saved source payloads from DIR without network "
                         "access; default: fetch live sources once per launch")
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

    session = Session(ds, roles, args.role)
    if args.web:
        from .web import serve
        return serve(session)
    print(render.ATTRIBUTION)
    print()
    print("\n".join(render.render(ds, session.role, result=session.query())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
