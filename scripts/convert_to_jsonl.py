# convert_to_jsonl.py
import json
from pathlib import Path
import sys
import shutil

script_dir = Path(__file__).resolve().parent
default_json = script_dir / "female_only_sentences.json"
default_jsonl = script_dir / "female_only_sentences.jsonl"

# Accept optional args: input (json or jsonl) and output (.jsonl)
input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else default_jsonl

# If no input arg provided:
# - if default_jsonl exists, do nothing (already ready)
# - else try to convert default_json -> default_jsonl
if input_path is None:
    if default_jsonl.exists():
        print(f"✅ Found existing JSONL: {default_jsonl}. Nothing to do.")
        raise SystemExit(0)
    input_path = default_json

# If user passed a .jsonl file as input, just copy it to output_path (or skip if same file)
if input_path.suffix.lower() == ".jsonl":
    if input_path.resolve() == output_path.resolve():
        print(f"✅ Input is already the target JSONL: {input_path}")
        raise SystemExit(0)
    print(f"Copying {input_path} -> {output_path}")
    shutil.copy2(input_path, output_path)
    print(f"✅ Copied to {output_path}")
    raise SystemExit(0)

# Otherwise expect a JSON array to convert
if not input_path.exists():
    print("ERROR: input file not found:", input_path)
    print("Script dir:", script_dir)
    print("Files in script dir:")
    for p in sorted(script_dir.iterdir()):
        print("  ", p.name)
    raise SystemExit(1)

with input_path.open("r", encoding="utf-8") as f:
    data = json.load(f)

count = 0
with output_path.open("w", encoding="utf-8") as out:
    for item in data:
        text = item.get("female", "").strip()
        if not text:
            continue
        entry = {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that replies in Hinglish (female style)."},
                {"role": "user", "content": "Say something."},
                {"role": "assistant", "content": text}
            ]
        }
        out.write(json.dumps(entry, ensure_ascii=False) + "\n")
        count += 1

print(f"✅ Converted {count} entries -> {output_path}")
