import os
import sys
import io
import tokenize
from typing import Tuple

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
TARGET_DIR = os.path.join(ROOT, 'Backend')


def strip_comments_from_code(src: str) -> str:
    buf = io.BytesIO(src.encode('utf-8'))
    out_tokens = []
    try:
        for tok in tokenize.tokenize(buf.readline):
            if tok.type == tokenize.COMMENT:
                # drop comments (both full-line and trailing)
                continue
            # Keep everything else unchanged
            out_tokens.append(tok)
        # Reconstruct code
        new_src = tokenize.untokenize(out_tokens).decode('utf-8')
        return new_src
    except Exception:
        # If tokenization fails (unlikely), return original to be safe
        return src


def process_file(path: str) -> Tuple[bool, str]:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            original = f.read()
    except UnicodeDecodeError:
        # Fallback to latin-1 just in case; we'll write back utf-8
        with open(path, 'r', encoding='latin-1') as f:
            original = f.read()
    stripped = strip_comments_from_code(original)
    if stripped != original:
        with open(path, 'w', encoding='utf-8', newline='') as f:
            f.write(stripped)
        return True, path
    return False, path


def main():
    base = TARGET_DIR
    if not os.path.isdir(base):
        print(f"Target dir not found: {base}")
        sys.exit(1)
    changed = 0
    visited = 0
    for root, _, files in os.walk(base):
        for name in files:
            if not name.endswith('.py'):
                continue
            visited += 1
            path = os.path.join(root, name)
            did_change, _ = process_file(path)
            if did_change:
                changed += 1
                print(f"Updated: {path}")
    print(f"Done. Visited {visited} .py files, updated {changed}.")


if __name__ == '__main__':
    main()

