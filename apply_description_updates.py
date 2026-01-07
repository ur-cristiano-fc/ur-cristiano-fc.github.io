
import json
import os
import re

input_file = 'new_descriptions.json'

with open(input_file, 'r', encoding='utf-8') as f:
    updates = json.load(f)

count = 0
for filepath, new_desc in updates.items():
    if not os.path.exists(filepath):
        print(f"Skipping missing file: {filepath}")
        continue
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Escape double quotes
        safe_new_desc = new_desc.replace('"', '\\"')
        
        # Check if description field exists
        if re.search(r'^description:', content, re.MULTILINE):
            # Replace existing description
            # This regex needs to be careful not to match multiple lines if the description spans multiple lines (unlikely in this repo but possible)
            # Assuming single line: description: "..."
            replacement = f'description: "{safe_new_desc}"'
            new_content = re.sub(r'^description:.*$', replacement, content, count=1, flags=re.MULTILINE)
        else:
            # Add description if missing (insert after title)
            # Find title line
            replacement = f'description: "{safe_new_desc}"'
            new_content = re.sub(r'(^title:.*$)', r'\1\n' + replacement, content, count=1, flags=re.MULTILINE)
            
        if content != new_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            count += 1
        else:
            print(f"No match/change for description in: {filepath}")

    except Exception as e:
        print(f"Error updating {filepath}: {e}")

print(f"Successfully updated description for {count} files.")
