"""Generate article-relevant collage images using Google Custom Search API"""
import os
import random
from PIL import Image, ImageDraw, ImageFont
from config import IMAGE_QUALITY, IMAGE_MAX_WIDTH, IMAGE_MAX_HEIGHT, OPTIMIZE_IMAGE
from article_generator import client, TEXT_MODEL  # Import Gemini client

try:
    from google_image_handler import GoogleImageSearchHandler
    HAS_API_HANDLER = True
except ImportError:
    print("⚠️ google_image_handler not found, collage generation will fail")
    HAS_API_HANDLER = False


def generate_search_queries_from_title(title):
    """Use Gemini AI to generate optimal search queries based on article title
    
    Args:
        title: Article title
        
    Returns:
        List of 2-3 search queries for Google Images
    """
    
    prompt = f"""
Given this blog post title: "{title}"

Generate 2-3 Google Image search queries to find the most relevant photos for this article.

Requirements:
- ALWAYS include "cristiano ronaldo" in queries
- If the title mentions specific people (mother, son, girlfriend, family), include them in the search
- Make queries specific to the article topic
- Keep queries short and focused (3-6 words each)
- Return ONLY the search queries, one per line, nothing else

Examples:
Title: "Cristiano Ronaldo'nun Annesi ile Yapılan Röportajlardan 20 Söz"
cristiano ronaldo with mother
cristiano ronaldo maria dolores
cristiano ronaldo family

Title: "Cristiano Ronaldo's Training Routine"
cristiano ronaldo training
cristiano ronaldo gym workout

Now generate for the given title above. Return ONLY the search queries, one per line:
"""
    
    try:
        response = client.models.generate_content(
            model=TEXT_MODEL,
            contents=prompt
        )
        
        queries = [q.strip() for q in response.text.strip().split('\n') if q.strip()]
        queries = queries[:3]  # Max 3 queries
        
        print(f"🤖 Gemini generated {len(queries)} search queries:")
        for i, q in enumerate(queries, 1):
            print(f"   {i}. {q}")
        
        return queries
        
    except Exception as e:
        print(f"⚠️ Gemini query generation failed: {e}")
        # Fallback to simple query
        return ["cristiano ronaldo"]


def filter_relevant_images_with_gemini(title, image_results):
    """Use Gemini AI to filter and rank images based on article relevance
    
    Args:
        title: Article title
        image_results: List of image result dicts with 'title' and 'url'
        
    Returns:
        List of filtered and ranked image indices
    """
    
    if len(image_results) <= 4:
        # If we have 4 or fewer, use all of them
        return list(range(len(image_results)))
    
    # Prepare image descriptions for Gemini
    image_descriptions = []
    for i, img in enumerate(image_results[:10]):  # Analyze max 10 images
        desc = f"{i}. {img.get('title', 'Untitled')}"
        image_descriptions.append(desc)
    
    descriptions_text = '\n'.join(image_descriptions)
    
    prompt = f"""
Article title: "{title}"

Available images:
{descriptions_text}

Task: Select the 4 most relevant images for this article based on their descriptions.

Requirements:
- Choose images that best match the article topic
- Prioritize images showing people mentioned in the title
- Prefer action/contextual photos over generic portraits
- Return ONLY the numbers (0-9) of the 4 best images, separated by commas

Example response: 0,2,5,7

Your response (only numbers):
"""
    
    try:
        response = client.models.generate_content(
            model=TEXT_MODEL,
            contents=prompt
        )
        
        # Parse response
        selected = response.text.strip()
        indices = [int(x.strip()) for x in selected.split(',') if x.strip().isdigit()]
        indices = [i for i in indices if i < len(image_results)][:4]  # Max 4 images
        
        if len(indices) < 2:
            # If Gemini failed, use first 4
            return list(range(min(4, len(image_results))))
        
        print(f"🤖 Gemini selected {len(indices)} most relevant images: {indices}")
        return indices
        
    except Exception as e:
        print(f"⚠️ Gemini filtering failed: {e}")
        # Fallback: use first 4 images
        return list(range(min(4, len(image_results))))


def generate_image_freepik(prompt, output_path):
    """Generate article-relevant collage using Google Custom Search API + Gemini AI
    
    Uses Gemini to:
    1. Generate optimal search queries based on article title
    2. Filter and rank the most relevant images from search results
    
    Args:
        prompt: Article title
        output_path: Where to save the collage
    
    Returns:
        True if successful, raises exception otherwise
    """
    
    if not HAS_API_HANDLER:
        raise ImportError("google_image_handler module is required for collage generation")
    
    print(f"🎨 Creating AI-powered collage with relevant Cristiano Ronaldo photos")
    print(f"📝 Article Title: {prompt[:100]}...")
    
    # Step 1: Use Gemini to generate search queries
    print(f"\n{'='*50}")
    print("Step 1: AI Query Generation")
    print("="*50)
    search_queries = generate_search_queries_from_title(prompt)
    
    # Step 2: Search Google for images with all queries
    print(f"\n{'='*50}")
    print("Step 2: Searching Google Images")
    print("="*50)
    api_handler = GoogleImageSearchHandler()
    all_image_results = []
    
    for query in search_queries:
        print(f"🔍 Searching: {query}")
        results = api_handler.search_images(query, num_images=6)
        all_image_results.extend(results)
    
    if len(all_image_results) < 2:
        raise Exception(f"❌ Not enough images found. Only got {len(all_image_results)} images from Google. Need at least 2.")
    
    print(f"✅ Found {len(all_image_results)} total images from all searches")
    
    # Step 3: Use Gemini to filter and select best images
    print(f"\n{'='*50}")
    print("Step 3: AI Image Selection")
    print("="*50)
    selected_indices = filter_relevant_images_with_gemini(prompt, all_image_results)
    
    # Determine number of images for collage
    num_images = min(len(selected_indices), random.choice([3, 4]))
    selected_indices = selected_indices[:num_images]
    
    print(f"✅ Selected {len(selected_indices)} most relevant images")
    
    # Step 4: Download selected images
    print(f"\n{'='*50}")
    print("Step 4: Downloading Selected Images")
    print("="*50)
    images = []
    attributions = []
    
    for idx in selected_indices:
        img_info = all_image_results[idx]
        print(f"📥 Downloading: {img_info['title'][:60]}...")
        
        img = api_handler.download_image(img_info['url'])
        if img:
            images.append(img)
            attributions.append({
                'photographer': img_info.get('source', 'Google Search'),
                'photographer_url': img_info['url'],
                'source': 'google'
            })
        
        if len(images) >= num_images:
            break
    
    if len(images) < 2:
        raise Exception(f"❌ Failed to download enough images. Only downloaded {len(images)}. Need at least 2.")
    
    print(f"✅ Successfully downloaded {len(images)} images")
    
    # Step 5: Create collage
    print(f"\n{'='*50}")
    print("Step 5: Creating Collage")
    print("="*50)
    layout = select_optimal_layout(len(images))
    print(f"🎨 Using layout: {layout}")
    
    collage = create_collage_layout(images, layout, prompt)
    collage = add_attribution_watermark(collage, attributions)
    
    # Save with optimization
    collage.save(output_path, 'WEBP', quality=IMAGE_QUALITY, optimize=OPTIMIZE_IMAGE, method=6)
    
    file_size = os.path.getsize(output_path)
    print(f"✅ Collage saved: {output_path}")
    print(f"📊 File size: {file_size / 1024:.1f} KB")
    
    # Log image sources
    print(f"\n📸 Image sources:")
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