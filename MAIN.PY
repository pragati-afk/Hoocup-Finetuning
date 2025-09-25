import re
import json

def extract_chats_with_partner_jsonl(infile, person, outfile="output.jsonl"):
    """
    Extract all chat lines from a given person in format 'Name : message'
    and save them as JSONL with partner info.
    Each line in the JSONL looks like:
    {"speaker": "Alice", "partner": "Bob", "message": "Hello Bob"}
    """
    pattern = re.compile(r'^\s*([^:]+)\s*:\s*(.*)$')
    person_lower = person.lower()

    # Read all parsed lines into (speaker, message) tuples
    chats = []
    with open(infile, "r", encoding="utf-8") as f:
        for line in f:
            m = pattern.match(line)
            if m:
                chats.append((m.group(1).strip(), m.group(2).strip()))

    results = []
    for i, (speaker, message) in enumerate(chats):
        if speaker.lower() == person_lower:
            # Look ahead to the next line's speaker (if exists)
            partner = chats[i + 1][0] if i + 1 < len(chats) else "Unknown"
            results.append({
                "speaker": speaker,
                "partner": partner,
                "message": message
            })

    # Save to JSONL
    with open(outfile, "w", encoding="utf-8") as f:
        for item in results:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"Saved {len(results)} messages for '{person}' to {outfile}")


# -------- Example usage --------
if __name__ == "__main__":
    chat_file = "conversation.txt"   # <-- replace with your file name
    name = input("namep: ")
    extract_chats_with_partner_jsonl(chat_file, name)