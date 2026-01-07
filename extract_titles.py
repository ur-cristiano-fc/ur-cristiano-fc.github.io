
import os
import re
import json

posts_dir = '_posts'
output_file = 'current_titles.json'

titles = {}

for filename in os.listdir(posts_dir):
    if filename.endswith('.md'):
        filepath = os.path.join(posts_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            # Extract title using regex
            match = re.search(r'^title:\s*"(.*?)"', content, re.MULTILINE)
            if not match:
                match = re.search(r'^title:\s*(.*)', content, re.MULTILINE)
            
            if match:
                title = match.group(1).strip('"').strip("'")
                titles[filepath] = title
            else:
                titles[filepath] = "NO_TITLE_FOUND"

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(titles, f, indent=2)

print(f"Extracted {len(titles)} titles to {output_file}")
