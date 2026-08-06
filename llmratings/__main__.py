"""CLI entry point. Ticket 12: --category picks one of five use-case
categories, each rendered at its fixed reasoning effort. Ticket 15: the
default run fetches all three sources live; --fixtures opts into the offline
test seam. Ticket 17: the interactive TUI is a thin Textual shell
(docs/adr/0001) gated on a real TTY — no --interactive flag, and a missing
textual dependency errors out before the fetch."""

import argparse
import os
import sys
from pathlib import Path

from . import fetch, identity, render, tui


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="llm-ratings",
        description="Model-advice tables from DeepSWE, Terminal-Bench v2.1 and "
                    "Artificial Analysis (PoC).")
    ap.add_argument("--category", choices=[c[0] for c in render.CATEGORIES],
                    default="Chores",
                    help="use-case category (default: %(default)s); each "
                         "renders at its fixed reasoning effort")
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
        return tui.run(ds, args.category)

    print(render.ATTRIBUTION)
    print()
    print("\n".join(render.render(ds, args.category)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
