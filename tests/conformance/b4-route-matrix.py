"""Static check: every declared HTTP route has exactly one row in the B4 route matrix.

Each row links to the declaration (`file#Lnnn`); the row's verb and path must match the
declaration at that line. `--fix` rewrites the line numbers after code moves, by
declaration order per file, and refuses if the verbs or paths no longer line up.
"""

from pathlib import Path
import re
import sys

REPO = Path(__file__).resolve().parents[2]
MATRIX_PATH = REPO / "docs/refactor-matriz-rotas.md"
ROUTES = re.compile(r"router\.(get|post|put|patch|delete)\s*\(\s*['\"]([^'\"]+)")
ROW = re.compile(r"^\| (B4-R\d{3}) \| `(\w+) ([^`]+)` \| \[[^]]+\]\(\.\./([^#)]+)#L(\d+)\)")
GLOBS = {
    "apiGateway": "routes/*.js",
    "projects": "routes/*.js",
    "users": "routes/*.js",
    "subscriptions": "routes/*.js",
    "imageStorageService": "route/*.js",
}


def declarations():
    found = {}
    for service, pattern in GLOBS.items():
        for path in sorted((REPO / service).glob(pattern)):
            source = path.read_text()
            rel = path.relative_to(REPO).as_posix()
            found[rel] = [(m.group(1).upper(), m.group(2), source.count("\n", 0, m.start()) + 1)
                          for m in ROUTES.finditer(source)]
    return found


def same_path(row_path, declared):
    tail = declared.rstrip("/") or "/"
    return row_path.rstrip("/").endswith(tail) or (tail == "/" and row_path.rstrip("/") in
                                                   ("", "/projects", "/users", "/subscriptions"))


def rows(text):
    return [m for m in (ROW.match(line) for line in text.split("\n")) if m]


def main(fix):
    text = MATRIX_PATH.read_text()
    decl = declarations()
    by_file = {}
    for row in rows(text):
        by_file.setdefault(row.group(4), []).append(row)
    if fix:
        lines = text.split("\n")
        for file, file_rows in by_file.items():
            assert len(file_rows) == len(decl[file]), (file, len(file_rows), len(decl[file]))
            for row, (verb, path, line) in zip(file_rows, decl[file]):
                assert row.group(2) == verb and same_path(row.group(3), path), (row.group(1), verb, path)
                i = lines.index(row.group(0) + row.string[len(row.group(0)):])
                lines[i] = lines[i].replace(f"#L{row.group(5)})", f"#L{line})", 1)
        text = "\n".join(lines)
        MATRIX_PATH.write_text(text)

    ids = [row.group(1) for row in rows(text)]
    assert len(ids) == len(set(ids)), "duplicate matrix IDs"
    declared = {(f, line): (verb, path) for f, items in decl.items() for verb, path, line in items}
    listed = {}
    for row in rows(text):
        key = (row.group(4), int(row.group(5)))
        assert key not in listed, f"two rows for {key}"
        listed[key] = row
    missing = sorted(set(declared) - set(listed))
    extra = sorted(set(listed) - set(declared))
    assert not missing, f"Routes missing from matrix: {missing}"
    assert not extra, f"Matrix references without a route: {extra}"
    for key, row in listed.items():
        verb, path = declared[key]
        assert row.group(2) == verb and same_path(row.group(3), path), \
            f"{row.group(1)}: matrix says {row.group(2)} {row.group(3)}, code has {verb} {path}"
    print(f"B4 route matrix: {len(declared)} route/verb declarations covered, verbs and paths match")


if __name__ == "__main__":
    main("--fix" in sys.argv[1:])
