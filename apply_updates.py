
import json
import os
import re

input_file = 'new_titles.json'

with open(input_file, 'r', encoding='utf-8') as f:
    updates = json.load(f)

count = 0
for filepath, new_title in updates.items():
    if not os.path.exists(filepath):
        print(f"Skipping missing file: {filepath}")
        continue
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Regex to find title line
        # Handle double quotes, single quotes, or no quotes
        # We want to replace the whole line: title: "..."
        
        # New pattern: title: "NEW TITLE"
        # Escape double quotes in new title if needed
        safe_new_title = new_title.replace('"', '\\"')
        replacement = f'title: "{safe_new_title}"'
        
        # Pattern to match: title: (anything until newline)
        new_content = re.sub(r'^title:.*$', replacement, content, count=1, flags=re.MULTILINE)
        
        if content != new_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            count += 1
            # print(f"Updated: {filepath}")
        else:
            print(f"No match for title in: {filepath}")

    except Exception as e:
        print(f"Error updating {filepath}: {e}")

print(f"Successfully updated {count} files.")
