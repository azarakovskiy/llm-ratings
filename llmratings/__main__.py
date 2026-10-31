"""CLI entry point. Ticket 12's --category (five fixed-effort use-case
categories) is replaced by ticket 18's --role: one of the roles from the
checked-in roles.json (tab order = file order), each role's objective
selecting every model's best reasoning effort. Ticket 15: the default run
fetches all three rating sources live, plus best-effort OpenRouter
enrichment (ticket 18); --fixtures opts into the offline test seam.
Ticket 17: the interactive TUI is a thin Textual shell (docs/adr/0001)
gated on a real TTY — no --interactive flag, and a missing textual
dependency errors out before the fetch."""

import argparse
import os
import sys
from pathlib import Path

from . import fetch, identity, render, tui
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
        description="Model-advice tables from DeepSWE, Terminal-Bench v2.1 and "
                    "Artificial Analysis (PoC).")
    ap.add_argument("--role", choices=[r["name"] for r in roles],
                    default=roles[0]["name"],
                    help="role tab (default: %(default)s); the role's "
                         "objective selects each model's best reasoning "
                         "effort")
    ap.add_argument("--fixtures", metavar="DIR", default=None,
                    help="serve saved source payloads from DIR instead of "
                         "the network (the offline test seam; the default is "
                         "a live fetch on every run)")
    args = ap.parse_args(argv)

    if not os.environ.get("LLM_RATINGS_AA_API_KEY"):
        print("error: LLM_RATINGS_AA_API_KEY is not set — get a free API key at "
              "artificialanalysis.ai and export it", file=sys.stderr)
        return 1

    # Interactive only on a real terminal: stdin AND stdout must be ttys
    # (redirected stdout must stay batch, not ANSI frames). A missing
    # textual dependency is reported before the fetch — no network
    # round-trip for a setup error.
    interactive = sys.stdin.isatty() and sys.stdout.isatty()
    if interactive and not tui.available():
        print("error: textual is not installed — run `make deps`",
              file=sys.stderr)
        return 1

    try:
        raw = fetch.fetch_all(args.fixtures)
        aliases = identity.load_aliases(Path(__file__).parent / "aliases.json")
        ds = identity.build(aliases, raw)
    except fetch.SourceError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if interactive:
        return tui.run(ds, roles, args.role)

    session = Session(ds, roles, args.role)
    print(render.ATTRIBUTION)
    print()
    print("\n".join(render.render(ds, session.role, result=session.query())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
