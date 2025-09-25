import json

def convert_to_jsonl(input_file, output_file, user_name, assistant_name):
    """Convert conversation text to JSONL format for fine-tuning"""
    data = []
    
    with open(input_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    for i in range(0, len(lines)-1, 2):
        if i+1 >= len(lines):
            break
            
        speaker1, msg1 = lines[i].split(":", 1)
        speaker2, msg2 = lines[i+1].split(":", 1)

        if speaker1.strip() == user_name and speaker2.strip() == assistant_name:
            entry = {
                "messages": [
                    {"role": "user", "content": msg1.strip()},
                    {"role": "assistant", "content": msg2.strip()}
                ]
            }
            data.append(entry)

    with open(output_file, "w", encoding="utf-8") as f:
        for entry in data:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"✅ Converted {len(data)} pairs and saved to {output_file}")

if __name__ == "__main__":
    convert_to_jsonl("conversations.txt", "output.jsonl", user_name="", assistant_name="Radhika")
