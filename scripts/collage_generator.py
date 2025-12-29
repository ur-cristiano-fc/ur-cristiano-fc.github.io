"""Create unique collage images from Unsplash/Pexels"""
import os
import random
from PIL import Image, ImageDraw, ImageFont
from image_api_handler import ImageAPIHandler


def extract_search_query(title):
    """Extract relevant search terms from blog title"""
    
    title_lower = title.lower()
    
    # Always include base term
    base = "cristiano ronaldo"
    
    # Context keywords
    contexts = {
        'training': ['train', 'training', 'workout', 'exercise', 'fitness', 'gym'],
        'soccer': ['soccer', 'football', 'field', 'match', 'game', 'pitch'],
        'diet': ['diet', 'nutrition', 'food', 'meal', 'eating', 'healthy'],
        'celebration': ['goal', 'celebration', 'siuu', 'score', 'celebrating'],
        'lifestyle': ['lifestyle', 'life', 'daily', 'routine', 'habits'],
    }
    
    # Find matching context
    for context, keywords in contexts.items():
        if any(kw in title_lower for kw in keywords):
            return f"{base} {context}"
    
    # Default
    return f"{base} sports"


def create_blog_collage(title, output_path, num_images=4):
    f"""Create collage using Unsplash/Pexels images
    
    Args:
        title: {title}
        output_path: {output_path}
        num_images: {num_images}
    
    Returns:
        Dictionary with success status and info
    """
    
    print(f"🎨 Creating collage for: {title[:60]}...")
    
    # Extract search terms
    search_query = extract_search_query(title)
    print(f"🔍 Search query: {search_query}")
    
    # Get images from APIs
    api_handler = ImageAPIHandler()
    image_data = api_handler.get_images_for_collage(search_query, num_images)
    
    if len(image_data) < 2:
        print("❌ Not enough images found from APIs")
        return {'success': False, 'error': 'Insufficient images'}
    
    print(f"✅ Got {len(image_data)} images from APIs")
    
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
        print("❌ Failed to download enough images")
        return {'success': False, 'error': 'Download failed'}
    
    # Create collage
    try:
        # Select layout based on number of images
        if len(images) >= 4:
            layout = random.choice(['grid_2x2', 'hero_with_strip'])
        elif len(images) == 3:
            layout = 'featured_plus'
        else:
            layout = 'split_vertical'
        
        print(f"🎨 Using layout: {layout}")
        
        # Create collage
        collage = create_collage_layout(images, layout, title)
        
        # Add attribution watermark
        collage = add_attribution_watermark(collage, attributions)
        
        # Save optimized
        collage.save(output_path, 'WEBP', quality=85, optimize=True, method=6)
        
        file_size = os.path.getsize(output_path)
        print(f"✅ Collage saved: {output_path}")
        print(f"📊 File size: {file_size / 1024:.1f} KB")
        
        return {
            'success': True,
            'path': output_path,
            'attributions': attributions,
            'layout': layout,
            'num_images': len(images)
        }
        
    except Exception as e:
        print(f"❌ Collage creation failed: {e}")
        return {'success': False, 'error': str(e)}


def create_collage_layout(images, layout, title):
    """Create collage with specified layout"""
    
    width, height = 1920, 1080
    canvas = Image.new('RGB', (width, height), 'white')
    gap = 10
    
    if layout == 'grid_2x2':
        # 2x2 grid (4 images)
        while len(images) < 4:
            images.append(images[0])
        
        img_w = (width - gap) // 2
        img_h = (height - gap) // 2
        
        positions = [(0, 0), (img_w + gap, 0), (0, img_h + gap), (img_w + gap, img_h + gap)]
        
        for i, (x, y) in enumerate(positions[:4]):
            img = resize_and_crop(images[i], img_w, img_h)
            canvas.paste(img, (x, y))
    
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
        # 1 large + 2 small
        while len(images) < 2:
            images.append(images[0])
        
        main_w = int(width * 0.7)
        side_w = width - main_w - gap
        side_h = (height - gap) // 2
        
        main_img = resize_and_crop(images[0], main_w, height)
        canvas.paste(main_img, (0, 0))
        
        img2 = resize_and_crop(images[1], side_w, side_h)
        canvas.paste(img2, (main_w + gap, 0))
        
        img3 = resize_and_crop(images[-1], side_w, side_h)
        canvas.paste(img3, (main_w + gap, side_h + gap))
    
    elif layout == 'hero_with_strip':
        # 1 large + 3 small strip
        while len(images) < 3:
            images.append(images[0])
        
        hero_h = int(height * 0.7)
        strip_h = height - hero_h - gap
        strip_w = (width - 2 * gap) // 3
        
        hero = resize_and_crop(images[0], width, hero_h)
        canvas.paste(hero, (0, 0))
        
        for i in range(3):
            x = i * (strip_w + gap)
            y = hero_h + gap
            idx = min(i + 1, len(images) - 1)
            img = resize_and_crop(images[idx], strip_w, strip_h)
            canvas.paste(img, (x, y))
    
    # Add text overlay
    canvas = add_text_overlay(canvas, title, width, height)
    
    return canvas


def resize_and_crop(img, target_w, target_h):
    """Resize and crop image to exact dimensions"""
    
    img_ratio = img.width / img.height
    target_ratio = target_w / target_h
    
    if img_ratio > target_ratio:
        new_h = target_h
        new_w = int(new_h * img_ratio)
    else:
        new_w = target_w
        new_h = int(new_w / img_ratio)
    
    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    right = left + target_w
    bottom = top + target_h
    
    return img.crop((left, top, right, bottom))


def add_text_overlay(canvas, title, width, height):
    """Add title text with gradient background"""
    
    overlay = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Gradient at bottom
    gradient_h = 200
    for y in range(gradient_h):
        alpha = int((y / gradient_h) * 180)
        draw.rectangle(
            [(0, height - gradient_h + y), (width, height - gradient_h + y + 1)],
            fill=(0, 0, 0, alpha)
        )
    
    # Text
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 50)
    except:
        font = ImageFont.load_default()
    
    # Wrap text
    max_chars = 50
    if len(title) > max_chars:
        words = title.split()
        lines = []
        current = []
        for word in words:
            if len(' '.join(current + [word])) <= max_chars:
                current.append(word)
            else:
                lines.append(' '.join(current))
                current = [word]
        lines.append(' '.join(current))
        title = '\n'.join(lines[:2])  # Max 2 lines
    
    bbox = draw.textbbox((0, 0), title, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    x = (width - text_w) // 2
    y = height - gradient_h // 2 - text_h // 2
    
    # Outline
    for adj_x in range(-2, 3):
        for adj_y in range(-2, 3):
            draw.text((x + adj_x, y + adj_y), title, font=font, fill=(0, 0, 0, 255))
    
    draw.text((x, y), title, font=font, fill=(255, 255, 255, 255))
    
    canvas = canvas.convert('RGBA')
    canvas = Image.alpha_composite(canvas, overlay)
    
    return canvas.convert('RGB')


def add_attribution_watermark(canvas, attributions):
    """Add attribution watermark"""
    
    if not attributions:
        return canvas
    
    draw = ImageDraw.Draw(canvas, 'RGBA')
    
    sources = set([attr['source'] for attr in attributions])
    source_text = ', '.join([s.capitalize() for s in sources])
    text = f"Images: {source_text}"
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except:
        font = ImageFont.load_default()
    
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    x = canvas.width - text_w - 15
    y = canvas.height - text_h - 10
    
    padding = 5
    draw.rectangle(
        [(x - padding, y - padding), (x + text_w + padding, y + text_h + padding)],
        fill=(0, 0, 0, 120)
    )
    
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 200))
    
    return canvas