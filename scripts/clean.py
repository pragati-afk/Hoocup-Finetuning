#!/usr/bin/env python3
"""
clean.py

Usage:
    python clean.py [input.jsonl output.jsonl]

Defaults:
    input.jsonl  -> merged_5.jsonl
    output.jsonl -> cleaned_5.jsonl
"""

import json
import re
import sys
from pathlib import Path

# === CONFIG ===
DEFAULT_INPUT = "merged_5.jsonl"
DEFAULT_OUTPUT = "cleaned_5.jsonl"

# Speaker labels to remove
SPEAKER_LABELS = [
    r"Geet",
    r"Aditya",
    r"Receptionist",
    r"Man\s*\d*",
    r"Young\s*Man",
    r"Coolie",
    r"Passenger",
    r"Bhai\s*saab",
    r"ladki",
    r"Reservation\s*waale\s*uncle",
    r"PREET",
    r"Manjeet",
]

# Stage/action fragments to remove
PHRASE_PATTERNS = [
    r"turns to the receptionist",
    r"looking down, indicating agreement",
    r"flings it to the table",
    r"quickly leaves",
    r"turns around",
    r"turns to look",
]

# Unwanted warning/label keywords (case-insensitive)
UNWANTED_KEYWORDS = [
    "warning:",
    "classified",
    "consignee",
    "grade a",
    "strictly for",
    "do not open",
    "confidential",
    "sensitive",
    "hazardous",
    "dangerous goods",
]

# Regexes for unwanted warnings
UNWANTED_REGEXES = [
    r"warning\s*:\s*grade\s*a.*consignee",
    r"strictly for consignee only",
    r"classified\s+substance",
]

# Drop the whole JSON record if matched
DROP_RECORD_IF_MATCH = True

# === COMPILED REGEX ===
RE_FLAGS = re.IGNORECASE | re.UNICODE
speaker_regex = re.compile(
    r"(?<!\S)(?:" + "|".join(SPEAKER_LABELS) + r")(?:(?:\s*[:\-\)\(]+)|\b)\s*",
    flags=RE_FLAGS,
)
phrase_regexes = [re.compile(p, flags=RE_FLAGS) for p in PHRASE_PATTERNS]
unwanted_regexes = [re.compile(p, flags=RE_FLAGS) for p in UNWANTED_REGEXES]
paren_dir_re = re.compile(r"[\(\[\{][^\)\]\}]{1,200}[\)\]\}]", flags=RE_FLAGS)


def is_unwanted_warning(text: str) -> bool:
    """Detect warning/label lines to drop."""
    if not text:
        return False
    low = text.lower()

    # keyword check
    for kw in UNWANTED_KEYWORDS:
        if kw in low:
            return True

    # regex check
    for rx in unwanted_regexes:
        if rx.search(text):
            return True

    # heuristic: mostly uppercase
    letters = [c for c in text if c.isalpha()]
    if letters:
        up_frac = sum(1 for c in letters if c.isupper()) / len(letters)
        if up_frac > 0.60 and len(text) > 10:
            return True

    return False


def clean_text(text: str) -> str:
    """Clean speaker labels, stage directions, etc."""
    if not text:
        return text

    original = text

    # remove phrases
    for pr in phrase_regexes:
        text = pr.sub("", text)

    # remove parenthetical directions
    text = paren_dir_re.sub("", text)

    # remove speaker labels
    for _ in range(2):
        text = speaker_regex.sub("", text)

    # remove stray uppercase NAME tokens
    text = re.sub(r"(?<!\S)[A-Z][A-Z0-9_\-]{1,20}(?=\s|[:\.\,]|$)", "", text)

    # clean punctuation
    text = re.sub(r"^[\s\:\-–—]+", "", text)
    text = re.sub(r"\s+[:\-,;]\s+", " ", text)

    # normalize spaces
    text = re.sub(r"\s+", " ", text).strip()

    # fallback if too short
    if len(text) < 3:
        return original.strip()

    return text


def process_file(inpath: Path, outpath: Path):
    count_in = 0
    count_out = 0
    with inpath.open("r", encoding="utf-8") as fin, outpath.open("w", encoding="utf-8") as fout:
        for raw in fin:
            line = raw.strip()
            if not line:
                continue
            count_in += 1

            try:
                obj = json.loads(line)
                text_val = obj.get("text", "") if isinstance(obj.get("text", ""), str) else ""
            except json.JSONDecodeError:
                obj = {"text": line}
                text_val = line

            # check for unwanted warnings
            if is_unwanted_warning(text_val):
                if DROP_RECORD_IF_MATCH:
                    continue
                else:
                    obj["text"] = ""
                    fout.write(json.dumps(obj, ensure_ascii=False) + "\n")
                    count_out += 1
                    continue

            # clean
            if text_val:
                obj["text"] = clean_text(text_val)

            fout.write(json.dumps(obj, ensure_ascii=False) + "\n")
            count_out += 1

    print(f"Processed {count_in} lines -> wrote {count_out} lines to {outpath}")


def main():
    argv = sys.argv[1:]
    if len(argv) == 0:
        in_file = Path(DEFAULT_INPUT)
        out_file = Path(DEFAULT_OUTPUT)
    elif len(argv) == 2:
        in_file = Path(argv[0])
        out_file = Path(argv[1])
    else:
        print("Usage: python clean.py [input.jsonl output.jsonl]")
        sys.exit(1)

    if not in_file.exists():
        print(f"Input file not found: {in_file}")
        sys.exit(1)

    process_file(in_file, out_file)


if __name__ == "__main__":
    main()
