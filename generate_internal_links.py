
import os
import json
import random

# Load available posts and their titles/keywords (using the titles map I generated earlier)
with open('new_titles.json', 'r', encoding='utf-8') as f:
    all_posts = json.load(f)

# Load target files
with open('posts_missing_links.txt', 'r', encoding='utf-8') as f:
    target_files = [line.strip() for line in f if line.strip()]

# Helper to get URL slug from filename
# _posts/2025-06-27-cristiano-ronaldo-daily-routine.md -> /cristiano-ronaldo-daily-routine/
def get_url_from_filepath(filepath):
    basename = os.path.basename(filepath)
    # Remove date YYYY-MM-DD-
    slug = basename[11:-3] # remove date prefix and .md extension
    return f"/{slug}/"

def get_related_posts(current_file, all_posts_map, limit=5):
    # flexible matching logic
    # extract keywords from current file title
    current_title = all_posts_map.get(current_file, "")
    keywords = [w.lower() for w in current_title.split() if len(w) > 3 and w.lower() not in ['cristiano', 'ronaldo', '2025', '2026', 'with', 'what', 'from', 'this']]
    
    scored_posts = []
    
    for path, title in all_posts_map.items():
        if path == current_file: 
            continue
            
        score = 0
        title_lower = title.lower()
        for k in keywords:
            if k in title_lower:
                score += 1
        
        # Give some randomness for variety if scores are tied
        if score > 0:
            scored_posts.append((score, path, title))
            
    # Sort by score desc, then shuffle slightly?
    scored_posts.sort(key=lambda x: x[0], reverse=True)
    
    # Take top 10 matches and pick 5 random ones to avoid same links everywhere?
    top_matches = scored_posts[:15]
    if len(top_matches) < limit:
        # Fill with random posts if not enough matches
        remaining = [p for p in all_posts_map.items() if p[0] != current_file and p[0] not in [m[1] for m in scored_posts]]
        random.shuffle(remaining)
        for i in range(limit - len(top_matches)):
              if remaining:
                  path, title = remaining.pop()
                  top_matches.append((0, path, title))
    
    # Shuffle the top matches to rotate content
    random.shuffle(top_matches)
    return top_matches[:limit]

# Generate updates map
internal_link_updates = {}

for filepath in target_files:
    related = get_related_posts(filepath, all_posts)
    links_md = "\n\n## Related Posts\n\n"
    for _, path, title in related:
        url = get_url_from_filepath(path)
        # Clean title for display (remove quotes if any)
        clean_title = title.replace('"', '').replace("'", "")
        links_md += f"- [{clean_title}]({url})\n"
    
    internal_link_updates[filepath] = links_md

with open('internal_link_updates.json', 'w', encoding='utf-8') as f:
    json.dump(internal_link_updates, f, indent=2)

print(f"Generated internal link plans for {len(internal_link_updates)} files.")
