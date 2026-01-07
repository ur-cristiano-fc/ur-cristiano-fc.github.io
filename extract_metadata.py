
import os
import re
import json

posts_dir = '_posts'
output_file = 'current_metadata.json'

metadata = {}

for filename in os.listdir(posts_dir):
    if filename.endswith('.md'):
        filepath = os.path.join(posts_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Extract title
            title_match = re.search(r'^title:\s*"(.*?)"', content, re.MULTILINE)
            if not title_match:
                title_match = re.search(r'^title:\s*(.*)', content, re.MULTILINE)
            
            # Extract description
            desc_match = re.search(r'^description:\s*"(.*?)"', content, re.MULTILINE)
            if not desc_match:
                desc_match = re.search(r'^description:\s*(.*)', content, re.MULTILINE)
                
            data = {}
            if title_match:
                data['title'] = title_match.group(1).strip('"').strip("'")
            
            if desc_match:
                data['description'] = desc_match.group(1).strip('"').strip("'")
            else:
                data['description'] = "" # No description found
                
            metadata[filepath] = data

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(metadata, f, indent=2)

print(f"Extracted metadata from {len(metadata)} posts.")
