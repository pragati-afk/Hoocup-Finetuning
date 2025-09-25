#!/usr/bin/env python3
"""
convert_to_chat_jsonl.py

Converts a JSONL file with {"text": "..."} (one per line) into Azure chat-messages JSONL:
{"messages":[ {"role":"user","content":"..."}, {"role":"assistant","content":"..."} ]}

Usage:
    python convert_to_chat_jsonl.py [input.jsonl] [output.jsonl] [--mode MODE]

Modes:
    consecutive  - (default) pair line i -> user, line i+1 -> assistant
    alternate    - treat lines alternately: 0=user,1=assistant,2=user,3=assistant...
    wrap         - wrap each line as assistant content and set a generic user prompt

Examples:
    python convert_to_chat_jsonl.py test1.jsonl test1_chat.jsonl
    python convert_to_chat_jsonl.py test1.jsonl test1_chat.jsonl --mode wrap
"""

import json
import sys
from pathlib import Path
import argparse

# ----------------- Config -----------------
DEFAULT_INPUT = "test1.jsonl"
DEFAULT_OUTPUT = "test1_chat.jsonl"

# Generic prompt used in "wrap" mode (you can change this)
WRAP_USER_PROMPT = "Please respond to the following message as the assistant."

# Try to import a clean_text function from clean.py if it exists.
# If not found, we'll just use identity function.
def _get_cleaner():
    try:
        import clean  # noqa: F401
        if hasattr(clean, "clean_text"):
            return clean.clean_text
        # else maybe user exported differently
        if hasattr(clean, "clean"):
            return clean.clean
    except Exception:
        pass

    # Fallback: identity
    def identity(s: str) -> str:
        return s
    return identity

CLEANER = _get_cleaner()

# ----------------- Utilities -----------------
def load_text_lines(path: Path):
    lines = []
    with path.open(encoding="utf-8") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
                # common keys: 'text' or 'content'
                text = ""
                if isinstance(obj, dict):
                    # try typical fields
                    for key in ("text", "content", "message", "msg"):
                        if key in obj and isinstance(obj[key], str):
                            text = obj[key]
                            break
                else:
                    # if raw JSON is not dict, fall back to string
                    text = str(obj)
            except json.JSONDecodeError:
                # treat raw line as text
                text = raw
            text = text.strip()
            if text:
                # apply cleaner if available
                try:
                    text = CLEANER(text)
                except Exception:
                    # if cleaner fails, fallback
                    pass
                lines.append(text)
    return lines

def write_chat_records(records, outpath: Path):
    with outpath.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

# ----------------- Pairing strategies -----------------
def mode_consecutive(lines):
    """Pair consecutive lines: i -> user, i+1 -> assistant"""
    recs = []
    i = 0
    while i + 1 < len(lines):
        user = lines[i].strip()
        assistant = lines[i + 1].strip()
        if user and assistant:
            recs.append({"messages": [{"role": "user", "content": user}, {"role": "assistant", "content": assistant}]})
        i += 2
    return recs

def mode_alternate(lines):
    """Lines alternate: 0 user, 1 assistant, 2 user, 3 assistant ..."""
    recs = []
    i = 0
    while i + 1 < len(lines):
        user = lines[i].strip()
        assistant = lines[i + 1].strip()
        if user and assistant:
            recs.append({"messages": [{"role": "user", "content": user}, {"role": "assistant", "content": assistant}]})
        i += 2
    return recs

def mode_wrap(lines, prompt=WRAP_USER_PROMPT):
    """Wrap each single line as assistant content, with a generic user prompt."""
    recs = []
    for line in lines:
        assistant = line.strip()
        if assistant:
            recs.append({"messages": [{"role": "user", "content": prompt}, {"role": "assistant", "content": assistant}]})
    return recs

# ----------------- Main -----------------
def main():
    parser = argparse.ArgumentParser(description="Convert text-jsonl -> Azure Chat Messages JSONL")
    parser.add_argument("input", nargs="?", default=DEFAULT_INPUT, help="input jsonl (default: test1.jsonl)")
    parser.add_argument("output", nargs="?", default=DEFAULT_OUTPUT, help="output jsonl (default: test1_chat.jsonl)")
    parser.add_argument("--mode", choices=["consecutive", "alternate", "wrap"], default="consecutive",
                        help="pairing mode (default: consecutive)")
    parser.add_argument("--preview", action="store_true", help="print a small preview and exit (no write)")
    args = parser.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)

    if not in_path.exists():
        print(f"Input file not found: {in_path}")
        sys.exit(1)

    lines = load_text_lines(in_path)
    print(f"Loaded {len(lines)} text lines from {in_path}")

    if args.mode == "consecutive":
        records = mode_consecutive(lines)
    elif args.mode == "alternate":
        records = mode_alternate(lines)
    else:
        records = mode_wrap(lines)

    print(f"Converted to {len(records)} chat examples using mode='{args.mode}'")

    if args.preview:
        print("=== Preview first 3 records ===")
        for r in records[:3]:
            print(json.dumps(r, ensure_ascii=False, indent=2))
        return

    write_chat_records(records, out_path)
    print(f"Wrote {len(records)} lines to {out_path}")
    print("You're ready to upload this file to Azure for fine-tuning (chat messages format).")

if __name__ == "__main__":
    main()
