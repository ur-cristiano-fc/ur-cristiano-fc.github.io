"""Generate article-relevant collage images (replacing Freepik AI)"""
import os
import random
from PIL import Image, ImageDraw, ImageFont
from config import IMAGE_QUALITY, IMAGE_MAX_WIDTH, IMAGE_MAX_HEIGHT, OPTIMIZE_IMAGE

try:
    from image_api_handler import ImageAPIHandler
    HAS_API_HANDLER = True
except ImportError:
    print("⚠️ image_api_handler not found, collage generation will fail")
    HAS_API_HANDLER = False


def extract_search_query_from_title(title):
    """Extract relevant search terms from blog title for image search"""
    
    title_lower = title.lower()
    
    # Always include base term for Ronaldo blog
    base = "cristiano ronaldo"
    
    # Context keywords mapping
    contexts = {
        'training': ['train', 'training', 'workout', 'exercise', 'fitness', 'gym', 'muscle', 'strength', 'antrenman'],
        'soccer': ['soccer', 'football', 'field', 'match', 'game', 'pitch', 'play', 'player', 'futbol', 'maç'],
        'diet': ['diet', 'nutrition', 'food', 'meal', 'eating', 'healthy', 'breakfast', 'lunch', 'dinner', 'beslenme'],
        'celebration': ['goal', 'celebration', 'siuu', 'score', 'celebrating', 'win', 'victory', 'gol'],
        'lifestyle': ['lifestyle', 'life', 'daily', 'routine', 'habits', 'home', 'family', 'yaşam'],
        'career': ['career', 'club', 'team', 'transfer', 'contract', 'trophy', 'award', 'kariyer', 'takım'],
        'skills': ['skills', 'technique', 'dribbling', 'shooting', 'passing', 'speed', 'teknik'],
    }
    
    # Find best matching context
    for context, keywords in contexts.items():
        if any(kw in title_lower for kw in keywords):
            print(f"🎯 Detected context: {context}")
            return f"{base} {context}"
    
    # Default to sports if no match
    return f"{base} sports"


def generate_image_freepik(prompt, output_path, ):
    f"""Generate article-relevant collage (replaces Freepik API)
    
    This function maintains the same interface as the old Freepik generator
    but now creates unique collages from Unsplash/Pexels images.
    
    Args:
        prompt: {prompt}
        output_path: {output_path}
    
    Returns:
        True if successful, raises exception otherwise
    """
    
    if not HAS_API_HANDLER:
        raise ImportError("image_api_handler module is required for collage generation")
    
    print(f"🎨 Creating article-relevant collage instead of AI generation")
    print(f"📝 Prompt/Title: {prompt[:100]}...")
    
    # Extract search query from prompt/title
    search_query = f"{prompt}"
    print(f"🔍 Search query: {search_query}")
    
    # Determine number of images (3 or 4 for variety)
    num_images = random.choice([3, 4])
    
    # Get images from APIs
    api_handler = ImageAPIHandler()
    image_data = api_handler.get_images_for_collage(search_query, num_images)
    
    if len(image_data) < 2:
        raise Exception(f"❌ Not enough images found. Only got {len(image_data)} images from APIs. Need at least 2.")
    
    print(f"✅ Found {len(image_data)} images from APIs")
    
    # Download images
    images = []
    attributions = []
    
    for img_info in image_data:
        img = api_handler.download_image(img_info['url'])
        if img:
            images.append(img)
            attributions.append({
                'photographer': img_info['photographer'],
                'photographer_url': img_info['photographer_url'],
                'source': img_info['source']
            })
    
    if len(images) < 2:
        raise Exception(f"❌ Failed to download enough images. Only downloaded {len(images)}. Need at least 2.")
    
    print(f"✅ Downloaded {len(images)} images successfully")
    
    # Select layout based on number of images
    layout = select_optimal_layout(len(images))
    print(f"🎨 Using layout: {layout}")
    
    # Create collage with article title
    collage = create_collage_layout(images, layout, prompt)
    
    # Add attribution watermark
    collage = add_attribution_watermark(collage, attributions)
    
    # Save with optimization (using config settings)
    collage.save(output_path, 'WEBP', quality=IMAGE_QUALITY, optimize=OPTIMIZE_IMAGE, method=6)
    
    # Get file info
    file_size = os.path.getsize(output_path)
    print(f"✅ Collage saved: {output_path}")
    print(f"📊 File size: {file_size / 1024:.1f} KB")
    
    # Log attributions
    print(f"📸 Image sources:")
    for i, attr in enumerate(attributions, 1):
        print(f"   {i}. Photo by {attr['photographer']} on {attr['source'].capitalize()}")
    
    return True


def select_optimal_layout(num_images):
    """Select best layout based on number of images"""
    
    if num_images >= 4:
        # For 4+ images, randomly choose between grid layouts
        return random.choice(['grid_2x2', 'hero_with_strip'])
    elif num_images == 3:
        # For 3 images, use featured plus or horizontal strip
        return random.choice(['featured_plus', 'grid_1x3'])
    else:
        # For 2 images, split vertically
        return 'split_vertical'


def create_collage_layout(images, layout, title):
    """Create collage with specified layout and title overlay"""
    
    # Use config dimensions or default to 1920x1080
    width = IMAGE_MAX_WIDTH if IMAGE_MAX_WIDTH <= 1920 else 1920
    height = IMAGE_MAX_HEIGHT if IMAGE_MAX_HEIGHT <= 1080 else 1080
    
    canvas = Image.new('RGB', (width, height), (245, 245, 245))  # Light gray background
    gap = 12  # Gap between images
    
    if layout == 'grid_2x2':
        # 2x2 grid layout (4 images)
        while len(images) < 4:
            images.append(images[0])
        
        img_w = (width - gap) // 2
        img_h = (height - gap) // 2
        
        positions = [
            (0, 0),
            (img_w + gap, 0),
            (0, img_h + gap),
            (img_w + gap, img_h + gap)
        ]
        
        for i, (x, y) in enumerate(positions[:4]):
            img = resize_and_crop(images[i], img_w, img_h)
            canvas.paste(img, (x, y))
    
    elif layout == 'grid_1x3':
        # Horizontal 3-image strip
        while len(images) < 3:
            images.append(images[0])
        
        img_w = (width - 2 * gap) // 3
        img_h = height
        
        for i in range(3):
            x = i * (img_w + gap)
            img = resize_and_crop(images[i], img_w, img_h)
            canvas.paste(img, (x, 0))
    
    elif layout == 'split_vertical':
        # 2 images side by side
        while len(images) < 2:
            images.append(images[0])
        
        img_w = (width - gap) // 2
        img_h = height
        
        img1 = resize_and_crop(images[0], img_w, img_h)
        canvas.paste(img1, (0, 0))
        
        img2 = resize_and_crop(images[1], img_w, img_h)
        canvas.paste(img2, (img_w + gap, 0))
    
    elif layout == 'featured_plus':
        # 1 large image + 2 smaller on side
        while len(images) < 2:
            images.append(images[0])
        
        main_w = int(width * 0.68)
        side_w = width - main_w - gap
        side_h = (height - gap) // 2
        
        # Main large image (left)
        main_img = resize_and_crop(images[0], main_w, height)
        canvas.paste(main_img, (0, 0))
        
        # Top right
        img2 = resize_and_crop(images[1], side_w, side_h)
        canvas.paste(img2, (main_w + gap, 0))
        
        # Bottom right (use third image or duplicate)
        img3_idx = 2 if len(images) > 2 else 1
        img3 = resize_and_crop(images[img3_idx], side_w, side_h)
        canvas.paste(img3, (main_w + gap, side_h + gap))
    
    elif layout == 'hero_with_strip':
        # Large hero image with strip of smaller images below
        while len(images) < 3:
            images.append(images[0])
        
        hero_h = int(height * 0.65)
        strip_h = height - hero_h - gap
        strip_w = (width - 2 * gap) // 3
        
        # Hero image (top)
        hero = resize_and_crop(images[0], width, hero_h)
        canvas.paste(hero, (0, 0))
        
        # Bottom strip (3 images)
        for i in range(3):
            x = i * (strip_w + gap)
            y = hero_h + gap
            img_idx = min(i + 1, len(images) - 1)
            img = resize_and_crop(images[img_idx], strip_w, strip_h)
            canvas.paste(img, (x, y))
    
    # Add text overlay with title
    canvas = add_text_overlay(canvas, title, width, height)
    
    return canvas


def resize_and_crop(img, target_w, target_h):
    """Resize and center-crop image to exact dimensions"""
    
    # Calculate ratios
    img_ratio = img.width / img.height
    target_ratio = target_w / target_h
    
    # Resize to cover target area
    if img_ratio > target_ratio:
        # Image is wider - fit height
        new_h = target_h
        new_w = int(new_h * img_ratio)
    else:
        # Image is taller - fit width
        new_w = target_w
        new_h = int(new_w / img_ratio)
    
    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # Center crop
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    right = left + target_w
    bottom = top + target_h
    
    return img.crop((left, top, right, bottom))


def add_text_overlay(canvas, title, width, height):
    """Add title text with gradient background overlay"""
    
    # Create RGBA overlay for transparency
    overlay = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Add gradient background at bottom
    gradient_h = 220
    for y in range(gradient_h):
        # Smooth gradient from transparent to semi-opaque
        alpha = int((y / gradient_h) * 200)
        draw.rectangle(
            [(0, height - gradient_h + y), (width, height - gradient_h + y + 1)],
            fill=(0, 0, 0, alpha)
        )
    
    # Load font
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 56)
    except:
        try:
            font = ImageFont.truetype("arial.ttf", 56)
        except:
            font = ImageFont.load_default()
    
    # Wrap text if too long
    max_chars = 45
    if len(title) > max_chars:
        words = title.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            if len(test_line) <= max_chars:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Limit to 2 lines
        title = '\n'.join(lines[:2])
    
    # Calculate text position (centered at bottom)
    bbox = draw.textbbox((0, 0), title, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    x = (width - text_w) // 2
    y = height - gradient_h // 2 - text_h // 2
    
    # Draw text outline for better visibility
    outline_range = 3
    for adj_x in range(-outline_range, outline_range + 1):
        for adj_y in range(-outline_range, outline_range + 1):
            if adj_x != 0 or adj_y != 0:
                draw.text((x + adj_x, y + adj_y), title, font=font, fill=(0, 0, 0, 255))
    
    # Draw main text
    draw.text((x, y), title, font=font, fill=(255, 255, 255, 255))
    
    # Composite overlay onto canvas
    canvas = canvas.convert('RGBA')
    canvas = Image.alpha_composite(canvas, overlay)
    
    return canvas.convert('RGB')


def add_attribution_watermark(canvas, attributions):
    """Add small attribution watermark in corner"""
    
    if not attributions:
        return canvas
    
    draw = ImageDraw.Draw(canvas, 'RGBA')
    
    # Get unique sources
    sources = set([attr['source'] for attr in attributions])
    source_text = ', '.join([s.capitalize() for s in sources])
    text = f"Photos: {source_text}"
    
    # Load small font
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except:
        font = ImageFont.load_default()
    
    # Calculate position (bottom right)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    padding = 8
    x = canvas.width - text_w - padding * 2 - 10
    y = canvas.height - text_h - padding * 2 - 10
    
    # Draw semi-transparent background
    draw.rectangle(
        [
            (x - padding, y - padding),
            (x + text_w + padding, y + text_h + padding)
        ],
        fill=(0, 0, 0, 140)
    )
    
    # Draw white text
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 220))
    
    return canvas


def get_random_reference_image(reference_folder="assets/images"):
    """Kept for backward compatibility - not used in collage mode"""
    print("ℹ️ Reference images not used in collage mode")
    return None