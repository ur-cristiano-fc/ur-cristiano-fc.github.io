"""Automatically create and post 3 Pinterest pins for blog articles"""
import os
import time
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from pinterest import Pinterest
from article_generator import client, TEXT_MODEL
import random

# Blog site URL
BLOG_SITE = "https://ur-cristiano-fc.github.io"

# Pinterest API credentials
PINTEREST_ACCESS_TOKEN = os.environ.get("PINTEREST_ACCESS_TOKEN")
PINTEREST_BOARD_ID = os.environ.get("PINTEREST_BOARD_ID")  # Default board

# Pin design settings
PIN_WIDTH = 1000
PIN_HEIGHT = 1500  # Pinterest optimal ratio 2:3


def get_pinterest_client():
    """Initialize Pinterest API client"""
    if not PINTEREST_ACCESS_TOKEN:
        raise ValueError("PINTEREST_ACCESS_TOKEN not found in environment")
    
    return Pinterest(access_token=PINTEREST_ACCESS_TOKEN)


def get_available_boards():
    """Fetch user's Pinterest boards"""
    try:
        client = get_pinterest_client()
        boards = client.boards.list()
        
        board_list = []
        for board in boards:
            board_list.append({
                'id': board['id'],
                'name': board['name'],
                'description': board.get('description', ''),
                'pin_count': board.get('pin_count', 0)
            })
        
        print(f"✅ Found {len(board_list)} Pinterest boards:")
        for b in board_list:
            print(f"   📌 {b['name']} ({b['pin_count']} pins)")
        
        return board_list
        
    except Exception as e:
        print(f"⚠️ Error fetching boards: {e}")
        return []


def select_relevant_board(title, focus_kw, available_boards):
    """Use Gemini AI to select the most relevant Pinterest board"""
    
    if not available_boards:
        print("⚠️ No boards found, using fallback")
        return PINTEREST_BOARD_ID if 'PINTEREST_BOARD_ID' in globals() else None
    
    if len(available_boards) == 1:
        # Only one board, use it
        board = available_boards[0]
        print(f"✅ Only one board available: {board['name']}")
        return board['id']
    
    # Prepare board descriptions for Gemini
    board_descriptions = []
    for i, board in enumerate(available_boards):
        desc = f"{i}. {board['name']}"
        if board['description']:
            desc += f" - {board['description']}"
        desc += f" ({board.get('pin_count', 0)} pins)"
        board_descriptions.append(desc)
    
    boards_text = '\n'.join(board_descriptions)
    
    prompt = f"""
Article Title: "{title}"
Focus Keyword: "{focus_kw}"

Available Pinterest Boards:
{boards_text}

Task: Select the MOST relevant board for this article about Cristiano Ronaldo.

Requirements:
- Choose the board that best matches the article topic
- Consider board name, description, and existing content (pin count)
- For training/workout articles → fitness/training boards
- For family/personal articles → lifestyle/personal boards  
- For match/performance articles → highlights/football boards
- Return ONLY the number (0-{len(available_boards)-1}) of the best board

Example response: 2

Your response (only the number):
"""
    
    try:
        response = client.models.generate_content(
            model=TEXT_MODEL,
            contents=prompt
        )
        
        selected_idx = int(response.text.strip())
        
        if 0 <= selected_idx < len(available_boards):
            selected_board = available_boards[selected_idx]
            print(f"🤖 Gemini AI selected board: '{selected_board['name']}'")
            print(f"   Reason: Best match for topic '{focus_kw}'")
            return selected_board['id']
        else:
            # Fallback to first board
            print(f"⚠️ Invalid selection, using first board: {available_boards[0]['name']}")
            return available_boards[0]['id']
            
    except Exception as e:
        print(f"⚠️ Board selection failed: {e}")
        # Fallback to first board
        return available_boards[0]['id'] if available_boards else None


def generate_pin_variations(title, focus_kw, article_content):
    """Generate 3 different pin descriptions and hashtag sets using Gemini AI"""
    
    # Extract article excerpt for context
    article_excerpt = article_content[:500] if len(article_content) > 500 else article_content
    
    prompt = f"""
Generate 3 UNIQUE Pinterest pin variations for this blog post.

Article Title: "{title}"
Focus Keyword: "{focus_kw}"
Article Excerpt: "{article_excerpt}"

For EACH of the 3 pins, create:
1. A catchy, click-worthy description (100-150 characters)
2. A unique set of 8-12 relevant hashtags
3. A short hook phrase (5-8 words) for the pin image

Make each variation DIFFERENT:
- Pin 1: Educational/Informative tone
- Pin 2: Inspirational/Motivational tone  
- Pin 3: Curiosity-driven/Question-based tone

Format your response EXACTLY like this:

PIN 1
Description: [description here]
Hook: [hook phrase here]
Hashtags: #tag1 #tag2 #tag3 #tag4 #tag5 #tag6 #tag7 #tag8

PIN 2
Description: [description here]
Hook: [hook phrase here]
Hashtags: #tag1 #tag2 #tag3 #tag4 #tag5 #tag6 #tag7 #tag8

PIN 3
Description: [description here]
Hook: [hook phrase here]
Hashtags: #tag1 #tag2 #tag3 #tag4 #tag5 #tag6 #tag7 #tag8
"""
    
    try:
        print("🤖 Generating 3 pin variations with Gemini...")
        response = client.models.generate_content(
            model=TEXT_MODEL,
            contents=prompt
        )
        
        # Parse the response
        variations = parse_pin_variations(response.text)
        
        if len(variations) == 3:
            print(f"✅ Generated {len(variations)} unique pin variations")
            return variations
        else:
            print(f"⚠️ Expected 3 variations, got {len(variations)}")
            return generate_fallback_variations(title, focus_kw)
            
    except Exception as e:
        print(f"⚠️ Pin generation failed: {e}")
        return generate_fallback_variations(title, focus_kw)


def parse_pin_variations(response_text):
    """Parse Gemini's response into structured pin data"""
    
    variations = []
    current_pin = {}
    
    lines = response_text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        
        if line.startswith('PIN '):
            if current_pin:
                variations.append(current_pin)
            current_pin = {}
        
        elif line.startswith('Description:'):
            current_pin['description'] = line.replace('Description:', '').strip()
        
        elif line.startswith('Hook:'):
            current_pin['hook'] = line.replace('Hook:', '').strip()
        
        elif line.startswith('Hashtags:'):
            hashtags = line.replace('Hashtags:', '').strip()
            current_pin['hashtags'] = hashtags
    
    # Add last pin
    if current_pin:
        variations.append(current_pin)
    
    return variations


def generate_fallback_variations(title, focus_kw):
    """Generate fallback variations if AI fails"""
    
    return [
        {
            'description': f"Discover everything about {focus_kw}! Click to read more.",
            'hook': f"{focus_kw.title()} Guide",
            'hashtags': f"#{focus_kw.replace(' ', '')} #CristianoRonaldo #CR7 #Football #Soccer #Fitness #Motivation #Sports #Goals"
        },
        {
            'description': f"Want to know about {focus_kw}? This article has all the answers!",
            'hook': f"Learn About {focus_kw.title()}",
            'hashtags': f"#{focus_kw.replace(' ', '')} #Ronaldo #FootballLegend #SoccerTips #Training #Inspiration #Success #Champion"
        },
        {
            'description': f"Everything you need to know about {focus_kw}. Read now!",
            'hook': f"{focus_kw.title()} Explained",
            'hashtags': f"#{focus_kw.replace(' ', '')} #CristianoRonaldo #Football #Athlete #Workout #Goals #Dedication #Excellence"
        }
    ]


def create_pinterest_pin(base_image_path, hook_text, output_path, style='modern'):
    """Create a visually appealing Pinterest pin from the blog's featured image
    
    Args:
        base_image_path: Path to the blog's featured image
        hook_text: Text to overlay on the pin
        output_path: Where to save the pin
        style: Design style ('modern', 'bold', 'minimal')
    """
    
    # Load the base image
    base_img = Image.open(base_image_path)
    
    # Create pin canvas
    pin = Image.new('RGB', (PIN_WIDTH, PIN_HEIGHT), (255, 255, 255))
    
    # Resize and position base image (takes up top 60% of pin)
    img_height = int(PIN_HEIGHT * 0.6)
    
    # Resize base image to fit width while maintaining aspect ratio
    aspect_ratio = base_img.height / base_img.width
    new_width = PIN_WIDTH
    new_height = int(new_width * aspect_ratio)
    
    if new_height > img_height:
        new_height = img_height
        new_width = int(new_height / aspect_ratio)
    
    base_img = base_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Center the image horizontally
    x_offset = (PIN_WIDTH - new_width) // 2
    pin.paste(base_img, (x_offset, 0))
    
    # Create text area
    draw = ImageDraw.Draw(pin)
    
    # Style-specific colors
    if style == 'modern':
        bg_color = (45, 52, 54)
        text_color = (255, 255, 255)
        accent_color = (255, 71, 87)
    elif style == 'bold':
        bg_color = (255, 71, 87)
        text_color = (255, 255, 255)
        accent_color = (45, 52, 54)
    else:  # minimal
        bg_color = (255, 255, 255)
        text_color = (45, 52, 54)
        accent_color = (255, 71, 87)
    
    # Draw bottom section background
    text_area_y = img_height
    draw.rectangle(
        [(0, text_area_y), (PIN_WIDTH, PIN_HEIGHT)],
        fill=bg_color
    )
    
    # Add accent bar
    accent_height = 8
    draw.rectangle(
        [(0, text_area_y), (PIN_WIDTH, text_area_y + accent_height)],
        fill=accent_color
    )
    
    # Load fonts
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 56)
        url_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
    except:
        title_font = ImageFont.load_default()
        url_font = ImageFont.load_default()
    
    # Draw hook text (multi-line if needed)
    hook_lines = wrap_text(hook_text, title_font, PIN_WIDTH - 80)
    
    y_position = text_area_y + accent_height + 60
    
    for line in hook_lines:
        bbox = draw.textbbox((0, 0), line, font=title_font)
        text_width = bbox[2] - bbox[0]
        x = (PIN_WIDTH - text_width) // 2
        
        draw.text((x, y_position), line, font=title_font, fill=text_color)
        y_position += bbox[3] - bbox[1] + 20
    
    # Draw website URL at bottom
    url_text = "ur-cristiano-fc.github.io"
    bbox = draw.textbbox((0, 0), url_text, font=url_font)
    text_width = bbox[2] - bbox[0]
    x = (PIN_WIDTH - text_width) // 2
    y = PIN_HEIGHT - 80
    
    draw.text((x, y), url_text, font=url_font, fill=accent_color)
    
    # Save the pin
    pin.save(output_path, 'PNG', quality=95, optimize=True)
    print(f"✅ Pin created: {output_path}")
    
    return output_path


def wrap_text(text, font, max_width):
    """Wrap text to fit within max_width"""
    
    words = text.split()
    lines = []
    current_line = []
    
    draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    
    for word in words:
        current_line.append(word)
        test_line = ' '.join(current_line)
        bbox = draw.textbbox((0, 0), test_line, font=font)
        width = bbox[2] - bbox[0]
        
        if width > max_width:
            if len(current_line) == 1:
                lines.append(current_line[0])
                current_line = []
            else:
                current_line.pop()
                lines.append(' '.join(current_line))
                current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines


def post_to_pinterest(pin_image_path, title, description, hashtags, link, board_id):
    """Upload pin to Pinterest"""
    
    try:
        pinterest = get_pinterest_client()
        
        # Combine description with hashtags
        full_description = f"{description}\n\n{hashtags}"
        
        # Create pin
        pin = pinterest.pins.create(
            board_id=board_id,
            title=title[:100],  # Pinterest title limit
            description=full_description[:500],  # Pinterest description limit
            link=link,
            image_path=pin_image_path
        )
        
        pin_url = f"https://pinterest.com/pin/{pin['id']}"
        print(f"✅ Posted to Pinterest: {pin_url}")
        
        return {
            'success': True,
            'pin_id': pin['id'],
            'pin_url': pin_url
        }
        
    except Exception as e:
        print(f"❌ Pinterest posting failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def create_and_post_pinterest_pins(title, focus_kw, permalink, featured_image_path, article_content):
    """Main function: Create and post 3 Pinterest pins for a blog article
    
    Args:
        title: Blog post title
        focus_kw: Focus keyword
        permalink: Article permalink
        featured_image_path: Path to blog's featured image
        article_content: Full article text for context
    
    Returns:
        List of results for each pin
    """
    
    print(f"\n{'='*60}")
    print(f"📌 Creating 3 Pinterest Pins")
    print(f"{'='*60}")
    
    # Get available boards
    available_boards = get_available_boards()
    
    # Select best board using AI
    selected_board_id = select_relevant_board(title, focus_kw, available_boards)
    
    # Generate 3 variations
    variations = generate_pin_variations(title, focus_kw, article_content)
    
    # Article URL
    article_url = f"{BLOG_SITE}/{permalink}"
    
    # Create temp directory for pins
    pins_dir = "temp_pinterest_pins"
    os.makedirs(pins_dir, exist_ok=True)
    
    results = []
    styles = ['modern', 'bold', 'minimal']
    
    for i, variation in enumerate(variations, 1):
        print(f"\n{'='*60}")
        print(f"Creating Pin {i}/3")
        print(f"{'='*60}")
        
        # Create pin image
        pin_path = f"{pins_dir}/pin_{i}_{permalink}.png"
        style = styles[i-1]
        
        create_pinterest_pin(
            featured_image_path,
            variation['hook'],
            pin_path,
            style=style
        )
        
        # Post to Pinterest
        print(f"\n📤 Posting Pin {i} to Pinterest...")
        
        result = post_to_pinterest(
            pin_path,
            title,
            variation['description'],
            variation['hashtags'],
            article_url,
            selected_board_id
        )
        
        result['pin_number'] = i
        result['style'] = style
        result['description'] = variation['description']
        result['hashtags'] = variation['hashtags']
        
        results.append(result)
        
        # Wait between posts to avoid rate limiting
        if i < len(variations):
            print("⏳ Waiting 5 seconds before next pin...")
            time.sleep(5)
    
    # Cleanup temp files
    try:
        for file in os.listdir(pins_dir):
            os.remove(os.path.join(pins_dir, file))
        os.rmdir(pins_dir)
    except:
        pass
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📌 Pinterest Posting Complete")
    print(f"{'='*60}")
    
    successful = sum(1 for r in results if r['success'])
    print(f"✅ Successfully posted: {successful}/3 pins")
    
    for result in results:
        if result['success']:
            print(f"   Pin {result['pin_number']} ({result['style']}): {result['pin_url']}")
        else:
            print(f"   Pin {result['pin_number']} ({result['style']}): Failed - {result.get('error')}")
    
    return results


# Example usage
if __name__ == "__main__":
    # Test with sample data
    test_title = "Cristiano Ronaldo's Training Secrets"
    test_focus_kw = "cristiano ronaldo training"
    test_permalink = "cristiano-ronaldo-training-secrets"
    test_image = "assets/images/featured_cristiano-ronaldo-training-secrets.webp"
    test_content = "Article content here..."
    
    create_and_post_pinterest_pins(
        test_title,
        test_focus_kw,
        test_permalink,
        test_image,
        test_content
    )