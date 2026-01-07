
import json
import re

input_file = 'current_titles.json'
output_file = 'new_titles.json'

emotion_words = ["Ultimate", "Complete", "Revealed", "Secrets", "Shocking", "Inside", "Unstoppable", "Legendary", "Exclusive", "Must-See", "Explained", "Jaw-Dropping"]
year = "2026"

def optimize_title(title):
    original_title = title
    
    # 1. Update Year (Replace 2024/2025 with 2026, or add 2026)
    if "2026" not in title:
        if "2025" in title:
            title = title.replace("2025", "2026")
        elif "2024" in title:
            title = title.replace("2024", "2026")
        else:
            title = f"{title} ({year})"

    # 2. Add Emotion Word (if not present)
    has_emotion = any(word.lower() in title.lower() for word in emotion_words)
    if not has_emotion:
        # Simple heuristic: Prepend "Ultimate" or "Inside" depending on context
        if "How" in title or "Guide" in title:
            prefix = "Ultimate"
        elif "Why" in title or "Reason" in title:
            prefix = "Revealed:"
        elif "Net Worth" in title or "Salary" in title or "House" in title or "Jet" in title:
            prefix = "Inside"
        else:
            prefix = "Complete"
        
        # Avoid prepending if it degrades grammar significantly, but for CTR, punchy prefixes work.
        # But we need to be careful. E.g. "Cristiano Ronaldo's Diet" -> "Complete Cristiano Ronaldo's Diet" (Ok)
        # "Inside the Content" -> "Inside Inside the Content" (Bad)
        
        if not title.startswith(prefix):
             # Try to insert after "Cristiano Ronaldo" if it starts with it?
             # Or just prepend/append.
             # "Revealed: " at start is safe.
             if prefix == "Revealed:":
                 title = f"{prefix} {title}"
             elif prefix == "Inside" and not title.startswith("Inside"):
                 title = f"{prefix} {title}"
             else:
                 # Append often works too: " - Ultimate Guide"
                 # But user asked for "Ultimate Cristiano Ronaldo..."
                 # Let's try to identify the structure.
                 pass

    # 3. Numbers
    # If it starts with a number, great.
    # If it's "Ways to...", make it "7 Ways to..." (Risky if content doesn't match).
    # The user example: "Cristiano Ronaldo Abs Workout" -> "Get Ronaldo's 6-Pack: His Complete 20-Minute Ab Workout (2026)"
    # This required understanding the content (20 mins, 6-pack). I can't do that safely for 170 files without reading them.
    # I will stick to safe semantic upgrades.
    
    # Specific rewrites based on patterns
    
    # Pattern: "Cristiano Ronaldo [Topic]"
    if title.startswith("Cristiano Ronaldo"):
        # "Cristiano Ronaldo Net Worth" -> "Cristiano Ronaldo Net Worth 2026: The Billion-Dollar Empire Revealed"
        # My logic above handled year.
        if "Net Worth" in title:
            return title.replace("Cristiano Ronaldo Net Worth", "Cristiano Ronaldo Net Worth 2026: The Billion-Dollar Empire Revealed").replace(" (2026)", "") # Remove duplicate year if added
            
    return title

# I will actually generate a "proposed" map using more specific logic in the loop below
# and manually reviewing/tweaking the logic to be safe.

with open(input_file, 'r', encoding='utf-8') as f:
    titles_map = json.load(f)

new_titles = {}

for filepath, title in titles_map.items():
    new_title = title
    
    # Skip if already optimized (contains 2026 and an emotion word)
    # But wait, I might want to upgrade 2025 to 2026.
    
    # Check for non-English (some titles looked Turkish in the list?)
    # "Ronaldo Hangi Takımda..." -> Skip or be careful.
    if any(x in title for x in ["Hangi", "Kaç", "Futbolu"]):
        # Keep as is, maybe update year only
        if "2025" in new_title:
            new_title = new_title.replace("2025", "2026")
        new_titles[filepath] = new_title
        continue

    # --- YEAR UPDATE ---
    if "2026" not in new_title:
        if "2025" in new_title:
             new_title = new_title.replace("2025", "2026")
        elif "2024" in new_title:
             new_title = new_title.replace("2024", "2026")
        else:
             # Append year
             new_title = f"{new_title} (2026)"

    # --- EMOTION & NUMBER UPGRADE ---
    
    # Pattern: "Cristiano Ronaldo [Noun]" -> "Inside Cristiano Ronaldo's [Noun] (2026)"
    # E.g. "Cristiano Ronaldo's Private Jet" -> "Inside Cristiano Ronaldo's Private Jet: Features & Photos (2026)"
    
    original_clean = title.replace("2025", "").replace("2024", "").strip()
    
    if "Abs Workout" in title:
         new_title = "Get Ronaldo's 6-Pack: His Complete 20-Minute Ab Workout (2026)" # Hardcoded from example/previous
    elif "Fitness Lessons" in title:
         new_title = "10 Ways to Train Like Ronaldo: Ultimate Fitness Secrets Revealed (2026)"
    elif "Diet Plan" in title:
         new_title = "Eat Like a Champion: Cristiano Ronaldo's Complete Diet Plan Revealed (2026)"
    elif "Daily Routine" in title:
         new_title = "Inside Ronaldo's Daily Routine: 24 Hours of Success & Discipline (2026)"
    elif "Net Worth" in title:
         new_title = "Cristiano Ronaldo Net Worth 2026: The Billion-Dollar Empire Revealed"
    
    # Generic Upgrades
    elif "Guide" in title and "Ultimate" not in title:
        new_title = new_title.replace("Guide", "Ultimate Guide")
    elif "Story" in title and "Untold" not in title:
        new_title = new_title.replace("Story", "Untold Story Revealed")
    elif "Review" in title and "Honest" not in title:
        new_title = "Honest Review: " + new_title
    elif "Why" in title and "Explained" not in title:
         if not new_title.endswith("Explained"):
             new_title = new_title + " - Explained"
             
    # Clean up formatted titles
    new_title = new_title.replace("2026 (2026)", "2026")
    new_title = new_title.replace("(2026) (2026)", "(2026)")
    
    new_titles[filepath] = new_title

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(new_titles, f, indent=2)

print(f"Generated {len(new_titles)} optimized titles.")
