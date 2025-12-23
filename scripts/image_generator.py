"""Generate and compress images using Freepik AI"""
import os
import time
import requests
from io import BytesIO
from PIL import Image
from config import (
    FREEPIK_API_KEY, FREEPIK_ENDPOINT,
    IMAGE_QUALITY, IMAGE_MAX_WIDTH, IMAGE_MAX_HEIGHT, OPTIMIZE_IMAGE
)


def generate_image_freepik(prompt, output_path):
    """Generate image using Freepik AI with polling and compression"""
    
    if not FREEPIK_API_KEY:
        raise ValueError("❌ FREEPIK_API_KEY environment variable is not set")
    
    print(f"🔑 API Key length: {len(FREEPIK_API_KEY)} chars")
    
    headers = {
        "x-freepik-api-key": FREEPIK_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "prompt": prompt,
        "num_images": 1,
        "image": {"size": "1920x1080"},
        "aspect_ratio": "widescreen_16_9"
    }
    
    print(f"📤 Sending request to Freepik API...")
    print(f"📝 Prompt: {prompt[:100]}...")
    
    try:
        # Submit generation request
        response = requests.post(
            FREEPIK_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=60
        )
        
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code == 401:
            raise Exception("Invalid Freepik API key")
        if response.status_code == 402:
            raise Exception("Freepik API credits exhausted")
        
        response.raise_for_status()
        data = response.json()
        
        # Extract task_id
        task_id = data.get("data", {}).get("task_id")
        if not task_id:
            raise Exception(f"No task_id in response: {data}")
        
        print(f"🎫 Task ID: {task_id}")
        print(f"⏳ Polling for result...")
        
        # Poll for result
        image_url = poll_for_image(task_id, headers)
        
        # Download and compress image
        download_and_compress_image(image_url, output_path)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise


def poll_for_image(task_id, headers, max_attempts=40):
    """Poll Freepik API until image is ready"""
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        time.sleep(5)
        
        print(f"🔄 Polling attempt {attempt}/{max_attempts}...")
        
        status_url = f"https://api.freepik.com/v1/ai/text-to-image/flux-dev/{task_id}"
        status_response = requests.get(status_url, headers=headers, timeout=30)
        status_response.raise_for_status()
        
        status_data = status_response.json()
        status = status_data.get("data", {}).get("status")
        
        print(f"📊 Status: {status}")
        
        if status == "COMPLETED":
            generated = status_data["data"].get("generated", [])
            
            if isinstance(generated, list) and len(generated) > 0:
                image_url = generated[0] if isinstance(generated[0], str) else generated[0].get("url")
                if image_url:
                    return image_url
            
            raise Exception("No URL in completed response")
        
        elif status == "FAILED":
            error_msg = status_data["data"].get("error", "Unknown error")
            raise Exception(f"Generation failed: {error_msg}")
        
        elif status in ["CREATED", "PROCESSING"]:
            continue
    
    raise Exception(f"Generation timeout after {max_attempts * 5} seconds")


def download_and_compress_image(image_url, output_path):
    """Download image and compress it"""
    print(f"✅ Generation complete!")
    print(f"🖼️ Image URL: {image_url[:60]}...")
    print(f"📥 Downloading image...")
    
    img_response = requests.get(image_url, timeout=60)
    img_response.raise_for_status()
    
    print(f"💾 Processing and compressing image...")
    
    # Open and convert image
    img = Image.open(BytesIO(img_response.content)).convert("RGB")
    
    # Get original size
    original_size = len(img_response.content)
    original_width, original_height = img.size
    print(f"📊 Original: {original_width}x{original_height}, {original_size / 1024:.1f} KB")
    
    # Resize if needed (maintain aspect ratio)
    if original_width > IMAGE_MAX_WIDTH or original_height > IMAGE_MAX_HEIGHT:
        print(f"🔧 Resizing to fit {IMAGE_MAX_WIDTH}x{IMAGE_MAX_HEIGHT}...")
        img.thumbnail((IMAGE_MAX_WIDTH, IMAGE_MAX_HEIGHT), Image.Resampling.LANCZOS)
        new_width, new_height = img.size
        print(f"✅ Resized to: {new_width}x{new_height}")
    
    # Save with compression
    if OPTIMIZE_IMAGE:
        img.save(
            output_path,
            "WEBP",
            quality=IMAGE_QUALITY,
            method=6,
            optimize=True
        )
    else:
        img.save(output_path, "WEBP", quality=IMAGE_QUALITY)
    
    # Get compressed size
    compressed_size = os.path.getsize(output_path)
    compression_ratio = (1 - compressed_size / original_size) * 100
    
    print(f"📊 Compressed: {compressed_size / 1024:.1f} KB (saved {compression_ratio:.1f}%)")
    print(f"✅ Image saved: {output_path}")