"""Search helpers, adapted from the original searchcode.py.

The old version searched `entry` objects with fixed fields (title, authors, ...).
The database now has arbitrary columns, so rows are plain dicts (what Model.all()
returns) and every function takes `columns` = which fields to look in.

Behaviour is unchanged:
  1. exact "contains" match, case-insensitive
  2. if nothing matches, fall back to a "close" search: split the term into words
     and rank rows by how many words matched
  3. exclusion search removes rows that contain a term
"""


def string_search(text, term):
    """True if `term` appears anywhere in `text` (case-insensitive)."""
    return term.lower() in ("" if text is None else str(text)).lower()


def _values(row, columns):
    return [row.get(c) for c in columns]


def close_search_score(row, columns, term):
    """How many (word, field) pairs match - the old closeSearch count."""
    words = term.split()
    return sum(string_search(v, w) for v in _values(row, columns) for w in words)


def entry_search(rows, columns, term):
    """Return (results, exact).

    exact=True  -> rows containing the whole term in at least one column
    exact=False -> no exact hit; rows ranked best-first by number of words matched
    """
    term = term.strip()
    if not term:
        return list(rows), True

    exact = [r for r in rows if any(string_search(v, term) for v in _values(r, columns))]
    if exact:
        return exact, True

    scored = [(close_search_score(r, columns, term), r) for r in rows]
    scored = [(s, r) for s, r in scored if s > 0]
    scored.sort(key=lambda t: t[0], reverse=True)  # most matched words first (stable)
    return [r for _, r in scored], False


def exclusion_search(rows, columns, term):
    """Return a NEW list without the rows that contain `term` in any of `columns`."""
    return [r for r in rows if not any(string_search(v, term) for v in _values(r, columns))]
