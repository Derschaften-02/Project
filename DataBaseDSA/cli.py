"""Command-line interface: one-shot subcommands, or an interactive shell."""
import argparse
import shlex
import sys
from pathlib import Path

from core.importer import import_file
from core.registry import all_models, get_model, unregister_model


# ---------- helpers ----------
def _get(table):
    model = get_model(table)
    if not model:
        names = ", ".join(all_models()) or "none yet"
        raise ValueError(f"No table '{table}'. Available: {names}")
    return model


def _print_rows(model, rows, max_width=30):
    cols = list(model.fields)
    heads = [model.labels.get(c, c) for c in cols]
    cells = [[("" if r[c] is None else str(r[c]))[:max_width] for c in cols] for r in rows]
    widths = [max([len(h)] + [len(row[i]) for row in cells]) for i, h in enumerate(heads)]
    print("  ".join(h.ljust(w) for h, w in zip(heads, widths)))
    print("  ".join("-" * w for w in widths))
    for row in cells:
        print("  ".join(v.ljust(w) for v, w in zip(row, widths)))


# ---------- commands ----------
def cmd_import(a):
    model = import_file(a.file, a.name)
    print(f"Imported {model.count()} rows into '{model.table}' "
          f"({', '.join(f'{c}:{t}' for c, t in model.fields.items())})")


def cmd_list(a):
    if not all_models():
        print("No tables yet. Try: import <file.csv>")
    for name, m in sorted(all_models().items()):
        print(f"{name:<24} {m.count():>7} rows   {len(m.fields)} columns")


def cmd_show(a):
    model = _get(a.table)
    rows = model.all(limit=a.limit)
    _print_rows(model, rows)
    print(f"\n({len(rows)} of {model.count()} rows)")


def cmd_search(a):
    models = [_get(a.table)] if a.table else [all_models()[n] for n in sorted(all_models())]
    found = False
    for m in models:
        rows = m.search(a.keyword, limit=a.limit)
        if rows:
            found = True
            print(f"== {m.table} ({len(rows)} match{'es' if len(rows) != 1 else ''})")
            _print_rows(m, rows)
            print()
    if not found:
        print("No matches.")


def cmd_drop(a):
    model = _get(a.table)
    if not a.yes and input(f"Delete '{a.table}' and its {model.count()} rows? [y/N] ").lower() != "y":
        print("Cancelled.")
        return
    model.drop()
    unregister_model(a.table)
    print(f"Dropped '{a.table}'.")


def cmd_gui(a):
    from ui.app import run_ui  # imported lazily so the CLI works without PyQt
    run_ui()


def cmd_shell(a):
    parser = build_parser()
    print("Adaptive DB shell. Type 'help' for commands, 'exit' to quit.")
    while True:
        try:
            line = input("db> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not line:
            continue
        if line in ("exit", "quit"):
            return
        if line in ("help", "?"):
            parser.print_help()
            continue
        try:
            run(parser.parse_args(shlex.split(line)))
        except SystemExit:  # argparse reports its own usage errors
            pass


# ---------- wiring ----------
def run(args):
    try:
        args.func(args)
    except (ValueError, FileNotFoundError) as e:
        print(f"[error] {e}")


def build_parser():
    p = argparse.ArgumentParser(prog="db", description="Adaptive database: import files, browse, search.")
    sub = p.add_subparsers(dest="command", metavar="command")

    def add(name, func, help_):
        sp = sub.add_parser(name, help=help_)
        sp.set_defaults(func=func)
        return sp

    s = add("import", cmd_import, "import a CSV into a new table")
    s.add_argument("file")
    s.add_argument("--name", help="table name (default: file name)")

    add("list", cmd_list, "list tables")

    s = add("show", cmd_show, "print rows of a table")
    s.add_argument("table")
    s.add_argument("-n", "--limit", type=int, default=20)

    s = add("search", cmd_search, "search every column (all tables unless --table)")
    s.add_argument("keyword")
    s.add_argument("-t", "--table")
    s.add_argument("-n", "--limit", type=int, default=50)

    s = add("drop", cmd_drop, "delete a table")
    s.add_argument("table")
    s.add_argument("-y", "--yes", action="store_true", help="skip confirmation")

    add("shell", cmd_shell, "interactive prompt")
    add("gui", cmd_gui, "open the PyQt window (default)")
    return p