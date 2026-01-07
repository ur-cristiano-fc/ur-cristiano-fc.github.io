
import json
import os

input_file = 'internal_link_updates.json'

with open(input_file, 'r', encoding='utf-8') as f:
    updates = json.load(f)

count = 0
for filepath, append_content in updates.items():
    if not os.path.exists(filepath):
        print(f"Skipping missing file: {filepath}")
        continue
        
    try:
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(append_content)
        count += 1

    except Exception as e:
        print(f"Error updating {filepath}: {e}")

print(f"Successfully appended Related Posts to {count} files.")
