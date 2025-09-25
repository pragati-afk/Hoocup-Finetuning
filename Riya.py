import re
import json
from typing import List, Tuple

LINE_RE = re.compile(r'^\s*(?:\[\d{1,2}:\d{2}(?::\d{2})?\]\s*)?([^:]+?)\s*:\s*(.*)$')

def parse_chat_file(infile: str) -> List[Tuple[str, str]]:
    """Parse lines like 'Name: message' into (speaker, message) tuples."""
    chats: List[Tuple[str, str]] = []
    with open(infile, "r", encoding="utf-8") as f:
        for line in f:
            m = LINE_RE.match(line)
            if not m:
                continue
            speaker = m.group(1).strip()
            text = m.group(2).strip()
            if text == "":
                continue
            chats.append((speaker, text))
    return chats

def build_finetune_examples(chats: List[Tuple[str,str]], assistant_name: str):
    """Create fine-tuning pairs in OpenAI format."""
    assistant_lower = assistant_name.lower()
    examples = []

    for i, (speaker, message) in enumerate(chats):
        if speaker.lower() != assistant_lower:
            continue

        # find last partner message before this assistant reply
        partner_msg = None
        for j in range(i - 1, -1, -1):
            prev_speaker, prev_message = chats[j]
            if prev_speaker.lower() != assistant_lower:
                partner_msg = prev_message
                break

        if partner_msg is None:
            continue  # skip assistant messages with no prior partner msg

        example = {
            "messages": [
                {"role": "user", "content": partner_msg},
                {"role": "assistant", "content": message}
            ]
        }
        examples.append(example)

    return examples

def write_jsonl(examples: List[dict], outfile: str = "final.jsonl"):
    with open(outfile, "w", encoding="utf-8") as fo:
        for ex in examples:
            fo.write(json.dumps(ex, ensure_ascii=False) + "\n")
    print(f"Wrote {len(examples)} examples to {outfile}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Build fine-tuning JSONL pairs (user=partner, assistant=Riya) from chat text."
    )
    parser.add_argument("infile", help="Input chat text file (e.g. conversation.txt)")
    parser.add_argument("--assistant", default="Riya", help="Assistant name (default: Riya)")
    parser.add_argument("--outfile", default="final.jsonl", help="Output JSONL filename (default: final.jsonl)")
    args = parser.parse_args()

    chats = parse_chat_file(args.infile)
    examples = build_finetune_examples(chats, args.assistant)
    write_jsonl(examples, args.outfile)
