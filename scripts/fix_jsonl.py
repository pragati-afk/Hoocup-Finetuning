#!/usr/bin/env python3
"""
Fix JSONL file by removing empty lines and validating JSON format
"""
import json
import sys
from pathlib import Path

def fix_jsonl_file(input_file, output_file=None):
    """
    Fix JSONL file by:
    1. Removing empty lines
    2. Validating each line is valid JSON
    3. Ensuring proper chat format for fine-tuning
    """
    input_path = Path(input_file)
    if output_file is None:
        output_file = input_path.stem + "_fixed" + input_path.suffix
    
    output_path = Path(output_file)
    
    print(f"📂 Reading: {input_path}")
    print(f"💾 Writing: {output_path}")
    
    valid_lines = 0
    invalid_lines = 0
    empty_lines = 0
    
    with open(input_path, 'r', encoding='utf-8') as infile, \
         open(output_path, 'w', encoding='utf-8') as outfile:
        
        for line_num, line in enumerate(infile, 1):
            line = line.strip()
            
            # Skip empty lines
            if not line:
                empty_lines += 1
                print(f"⚠️  Line {line_num}: Empty line - skipping")
                continue
            
            # Validate JSON
            try:
                data = json.loads(line)
                
                # Validate chat format
                if "messages" not in data:
                    print(f"❌ Line {line_num}: Missing 'messages' field")
                    invalid_lines += 1
                    continue
                
                if not isinstance(data["messages"], list):
                    print(f"❌ Line {line_num}: 'messages' must be a list")
                    invalid_lines += 1
                    continue
                
                if len(data["messages"]) < 2:
                    print(f"❌ Line {line_num}: Need at least 2 messages (user + assistant)")
                    invalid_lines += 1
                    continue
                
                # Write valid line
                outfile.write(json.dumps(data, ensure_ascii=False) + '\n')
                valid_lines += 1
                
                if line_num <= 20 or line_num % 50 == 0:
                    print(f"✅ Line {line_num}: Valid")
                
            except json.JSONDecodeError as e:
                print(f"❌ Line {line_num}: Invalid JSON - {e}")
                invalid_lines += 1
                continue
    
    print(f"\n📊 Summary:")
    print(f"✅ Valid lines: {valid_lines}")
    print(f"❌ Invalid lines: {invalid_lines}")
    print(f"⚠️  Empty lines: {empty_lines}")
    print(f"📝 Output file: {output_path}")
    
    return output_path

def validate_jsonl_file(file_path):
    """
    Validate JSONL file for Azure OpenAI fine-tuning
    """
    print(f"\n🔍 Validating: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                print(f"❌ Line {line_num}: Empty line found!")
                return False
            
            try:
                data = json.loads(line)
                
                # Check required structure
                if "messages" not in data:
                    print(f"❌ Line {line_num}: Missing 'messages' field")
                    return False
                
                messages = data["messages"]
                if not isinstance(messages, list) or len(messages) < 2:
                    print(f"❌ Line {line_num}: Invalid messages format")
                    return False
                
                # Check message structure
                for msg_idx, msg in enumerate(messages):
                    if not isinstance(msg, dict):
                        print(f"❌ Line {line_num}, Message {msg_idx}: Not a dict")
                        return False
                    
                    if "role" not in msg or "content" not in msg:
                        print(f"❌ Line {line_num}, Message {msg_idx}: Missing role or content")
                        return False
                
            except json.JSONDecodeError as e:
                print(f"❌ Line {line_num}: JSON error - {e}")
                return False
    
    print("✅ JSONL file is valid!")
    return True

if __name__ == "__main__":
    # Fix the problematic file
    input_file = "output.jsonl"
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    
    if not Path(input_file).exists():
        print(f"❌ File not found: {input_file}")
        sys.exit(1)
    
    print("🛠️  Fixing JSONL file...")
    fixed_file = fix_jsonl_file(input_file)
    
    print("\n🔍 Validating fixed file...")
    if validate_jsonl_file(fixed_file):
        print(f"\n🎉 Success! Use this file for fine-tuning: {fixed_file}")
    else:
        print(f"\n❌ Still has issues. Check the file manually: {fixed_file}")