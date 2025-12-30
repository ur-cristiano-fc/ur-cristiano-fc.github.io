"""Generate article-relevant collage images using Google Custom Search API"""
import os
import random
from PIL import Image, ImageDraw, ImageFont
from config import IMAGE_QUALITY, IMAGE_MAX_WIDTH, IMAGE_MAX_HEIGHT, OPTIMIZE_IMAGE

try:
    from google_image_handler import GoogleImageSearchHandler
    HAS_API_HANDLER = True
except ImportError:
    print("⚠️ google_image_handler not found, collage generation will fail")
    HAS_API_HANDLER = False


def extract_search_query_from_title(title):
    """Extract relevant search terms from blog title for image search
    
    Returns specific Cristiano Ronaldo search queries based on article context
    to get REAL photos of him, not generic athlete photos
    """
    
    title_lower = title.lower()
    
    # Always include his full name for real photos
    base = "cristiano ronaldo"
    
    # Context keywords mapping - now returns specific CR7 activities
    contexts = {
        'training': ['train', 'training', 'workout', 'exercise', 'fitness', 'gym', 'muscle', 'strength', 'antrenman'],
        'match': ['soccer', 'football', 'field', 'match', 'game', 'pitch', 'play', 'player', 'futbol', 'maç', 'playing', 'stadium'],
        'diet': ['diet', 'nutrition', 'food', 'meal', 'eating', 'healthy', 'breakfast', 'lunch', 'dinner', 'beslenme'],
        'celebration': ['goal', 'celebration', 'siuu', 'score', 'celebrating', 'win', 'victory', 'gol', 'siuuu'],
        'lifestyle': ['lifestyle', 'life', 'daily', 'routine', 'habits', 'home', 'family', 'yaşam', 'personal'],
        'career': ['career', 'club', 'team', 'transfer', 'contract', 'trophy', 'award', 'kariyer', 'takım', 'juventus', 'real madrid', 'manchester', 'al nassr'],
        'skills': ['skills', 'technique', 'dribbling', 'shooting', 'passing', 'speed', 'teknik', 'dribble', 'free kick'],
        'portrait': ['portrait', 'face', 'look', 'style', 'fashion', 'photoshoot', 'photo'],
        'jersey': ['jersey', 'kit', 'uniform', 'shirt', 'number', '7'],
    }
    
    # Find best matching context
    for context, keywords in contexts.items():
        if any(kw in title_lower for kw in keywords):
            print(f"🎯 Detected context: {context}")
            
            # Return specific Ronaldo queries for each context
            if context == 'training':
                return f"{base} training gym workout"
            elif context == 'match':
                return f"{base} playing football match action"
            elif context == 'diet':
                return f"{base} eating food healthy lifestyle"
            elif context == 'celebration':
                return f"{base} goal celebration siuu"
            elif context == 'lifestyle':
                return f"{base} lifestyle family home"
            elif context == 'career':
                return f"{base} trophy award winning"
            elif context == 'skills':
                return f"{base} skills dribbling technique"
            elif context == 'portrait':
                return f"{base} portrait photo face"
            elif context == 'jersey':
                return f"{base} jersey number 7 shirt"
    
    # Default to action shots if no specific match
    return f"{base} football action"


def generate_image_freepik(prompt, output_path):
    """Generate article-relevant collage using Google Custom Search API
    
    This function maintains the same interface as the old Freepik generator
    but now creates unique collages from Google Images using the official API.
    
    Args:
        prompt: Article title or image prompt
        output_path: Where to save the collage
    
    Returns:
        True if successful, raises exception otherwise
    """
    
    if not HAS_API_HANDLER:
        raise ImportError("google_image_handler module is required for collage generation")
    
    print(f"🎨 Creating article-relevant collage with REAL Cristiano Ronaldo photos from Google")
    print(f"📝 Prompt/Title: {prompt[:100]}...")
    
    # Extract search query from prompt/title
    search_query = extract_search_query_from_title(prompt)
    print(f"🔍 Search query: {search_query}")
    
    # Determine number of images (3 or 4 for variety)
    num_images = random.choice([3, 4])
    
    # Get images from Google Custom Search API
    api_handler = GoogleImageSearchHandler()
    images_data = api_handler.get_images_for_collage(search_query, num_images)
    
    if len(images_data) < 2:
        raise Exception(f"❌ Not enough images found. Only got {len(images_data)} images from Google. Need at least 2.")
    
    print(f"✅ Found {len(images_data)} images from Google")
    
    # Extract PIL images and attributions
    images = []
    attributions = []
    
    for img_data in images_data:
        images.append(img_data['image'])
        attributions.append({
            'photographer': img_data['photographer'],
            'photographer_url': img_data['photographer_url'],
            'source': img_data['source']
        })
    
    print(f"✅ Prepared {len(images)} images for collage")
    
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
        print(f"   {i}. From {attr['source']} via Google Search")
    
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
    
    # Use 1920x1080 for 16:9 aspect ratio
    width = 1920
    height = 1080
    
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
    
    # Optional: Add text overlay with title (currently commented out)
    # canvas = add_text_overlay(canvas, title, width, height)
    
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


def add_attribution_watermark(collage, attributions):
    """Add small attribution watermark in corner"""
    
    if not attributions:
        return collage
    
    draw = ImageDraw.Draw(collage, 'RGBA')
    
    # Get unique sources
    sources = set([attr['source'] for attr in attributions])
    source_text = ', '.join([s.capitalize() for s in sources])
    text = f"Images: Google Search"
    
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
    x = collage.width - text_w - padding * 2 - 10
    y = collage.height - text_h - padding * 2 - 10
    
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
    
    return collage


def get_random_reference_image(reference_folder="assets/images"):
    """Kept for backward compatibility - not used in collage mode"""
    print("ℹ️ Reference images not used in collage mode")
    return None