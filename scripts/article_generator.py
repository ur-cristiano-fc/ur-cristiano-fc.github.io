"""Generate blog articles using Gemini AI"""
from google import genai
from config import TEXT_MODEL, GEMINI_API_KEY
import re

client = genai.Client(api_key=GEMINI_API_KEY)


def generate_article(title, focus_kw, permalink, semantic_kw, affiliate_links):
    """Generate SEO-optimized blog article"""
    prompt = f"""
write an SEO-optimised blog on the title {title}. using the Focus keyword {focus_kw} ,  using LSI Keywords {semantic_kw}
use the following
Rules:
- Simple English, a 10 year old can understand
- Don't write more than 3 sentences per paragraph, changes paragraph after 3 sentences
- Use "you" to address the reader
- link other websites for external linking where relevant
- also include related  affiliate links where it fits best: {affiliate_links},
- Use H2 and H3, h4, h5, h6 headings, no H1
- Use lists, tables, snippets, and other data formats
- Write more than 2000 words
- Add FAQ sections
- Write in Jekyll markdown format  artile filename extension .md only
- Naturally include focused & semantic keywords
- do not add any front matter or meta data
"""
    
    print("🤖 Generating article with Gemini...")
    response = client.models.generate_content(
        model=TEXT_MODEL,
        contents=prompt
    )
    
    # Remove any front matter that AI might have added
    content = remove_front_matter(response.text)
    
    # Add custom front matter
    article = create_custom_front_matter(title, focus_kw, permalink) + "\n\n" + content
    
    return article

def remove_front_matter(content):
    """Remove any existing front matter from AI-generated content"""
    # Remove front matter between --- delimiters
    content = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL)
    
    # Remove any stray YAML-like lines at the beginning
    lines = content.split('\n')
    clean_lines = []
    skip_yaml = True
    
    for line in lines:
        # Stop skipping once we hit actual content (heading or paragraph)
        if line.strip().startswith('#') or (line.strip() and not ':' in line):
            skip_yaml = False
        
        if not skip_yaml:
            clean_lines.append(line)
        elif skip_yaml and line.strip() and ':' not in line:
            # This is actual content, not YAML
            skip_yaml = False
            clean_lines.append(line)
    
    return '\n'.join(clean_lines).strip()


def create_custom_front_matter(title, focus_kw, permalink):
    """Create properly formatted Jekyll front matter"""
    # Escape quotes in title
    escaped_title = title.replace('"', '\\"')
    
    # Generate description (you can make this dynamic)
    description = generate_description(title, focus_kw)
    
    # Create front matter - NO LEADING SPACES!
    front_matter = f"""---
layout: post
title: "{escaped_title}"
description: "{description}"
keywords: "{focus_kw}"
author: ishowspeed
image: assets/images/{permalink}.webp
afflink: https://amzn.to/43Xm4Ci
affimage: assets/images/affiliate/Siuuuu-Celebration-Soccer-Night-Light-3D-Illusion.webp
affname: "Siuuuu Celebration Soccer Night Light 3D Illusion"
affdesc: "The soccer desk lamp is made of high-quality acrylic and ABS materials, LED light is stable and eye-friendly"
currentprice: $19.99
reviewnum: 294
brand: Cristiano Ronaldo
item: Decorations Gift
specialfeature: Dimmable Lamp
---"""
       
    return front_matter

def generate_description(title, focus_kw):
    """Generate SEO-optimized meta description (160 characters)"""
    prompt = f"""
Generate a compelling meta description for this blog post.

Title: {title}
Focus Keyword: {focus_kw}

Requirements:
- EXACTLY 150-160 characters (this is critical)
- Include the focus keyword naturally
- Action-oriented and engaging
- Make readers want to click
- No quotes or special characters
- Complete sentence

Return ONLY the description text, nothing else.
"""
    
    print("📝 Generating meta description...")
    response = client.models.generate_content(
        model=TEXT_MODEL,
        contents=prompt
    )
    
    description = response.text.strip()
    
    # Ensure it's under 160 characters
    if len(description) > 160:
        description = description[:157] + "..."
    
    print(f"✅ Description generated: {description} ({len(description)} chars)")
    
    return description



def generate_image_prompt(title):
    """Generate image prompt for Freepik AI"""
    prompt = f"""
Create a photorealistic featured image prompt for cristiano ronaldo to generate his actual image for this blog post:
Title: {title}

Requirements:
- realistic, high-quality
- NO text or words in the image
- Suitable as a blog featured image
- 2:1 aspect ratio
- Relevant to the topic

Return ONLY the image prompt, nothing else.
"""
    
    print("🎨 Generating image prompt...")
    response = client.models.generate_content(
        model=TEXT_MODEL,
        contents=prompt
    )
    return response.text.strip()
