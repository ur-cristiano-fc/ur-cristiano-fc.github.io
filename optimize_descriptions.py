
import json

input_file = 'current_metadata.json'
output_file = 'new_descriptions.json'

with open(input_file, 'r', encoding='utf-8') as f:
    metadata = json.load(f)

new_descriptions = {}

for filepath, data in metadata.items():
    title = data.get('title', '')
    desc = data.get('description', '')
    
    # 1. Update Year
    new_desc = desc
    if "2025" in new_desc:
        new_desc = new_desc.replace("2025", "2026")
    elif "2024" in new_desc:
        new_desc = new_desc.replace("2024", "2026")
    
    if "2026" not in new_desc:
        # Check if it ends with punctuation
        if new_desc and new_desc[-1] not in ['.', '!', '?']:
            new_desc += "."
        new_desc += " Updated for 2026."

    # 2. Heuristic Improvements
    # If description is very short or empty, generate from title
    if len(new_desc) < 50:
        new_desc = f"Discover the truth about {title}. This detailed guide covers everything you need to know in 2026."

    # 3. Add Call to Action (CTA) if missing
    cta_phrases = ["Read more", "Click to", "Find out", "Learn more", "Full story"]
    has_cta = any(cta.lower() in new_desc.lower() for cta in cta_phrases)
    
    if not has_cta:
        # Add a relevant CTA
        if "Net Worth" in title:
            new_desc += " Read the full breakdown now."
        elif "Workout" in title or "Routine" in title:
            new_desc += " Start your journey today."
        else:
            new_desc += " Read the full story now."
            
    # Clean up double punctuation or spaces
    new_desc = new_desc.replace("..", ".").replace("  ", " ").strip()
    
    # Update map
    new_descriptions[filepath] = new_desc

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(new_descriptions, f, indent=2)

print(f"Generated {len(new_descriptions)} optimized descriptions.")
