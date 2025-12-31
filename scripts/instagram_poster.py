"""Post to Instagram automatically with AI-generated content"""
import os
import time
from instagrapi import Client
from instagrapi.exceptions import LoginRequired
from article_generator import client, TEXT_MODEL


def generate_instagram_caption(title, focus_kw, article_excerpt):
    """Use Gemini AI to generate SEO-optimized Instagram caption
    
    Args:
        title: Article title
        focus_kw: Focus keyword
        article_excerpt: First 200 chars of article
        
    Returns:
        Dict with caption, hashtags, and cta
    """
    
    prompt = f"""
Create an Instagram post caption for this blog article:

Title: {title}
Focus Keyword: {focus_kw}
Article Preview: {article_excerpt[:200]}...

Requirements:
- Write engaging caption (150-200 characters max)
- Include a hook that makes people want to read more
- Add relevant hashtags (15-20 hashtags)
- Include call-to-action (CTA) to visit link in bio
- Use emojis naturally
- Make it engaging and clickable

Format your response EXACTLY like this:
CAPTION: [your engaging caption here with emojis]
HASHTAGS: #cristiano #ronaldo #cr7 #football #soccer [more hashtags]
CTA: [call to action text]

Generate the Instagram post:
"""
    
    try:
        response = client.models.generate_content(
            model=TEXT_MODEL,
            contents=prompt
        )
        
        content = response.text.strip()
        
        # Parse response
        caption_line = ""
        hashtags_line = ""
        cta_line = ""
        
        for line in content.split('\n'):
            if line.startswith('CAPTION:'):
                caption_line = line.replace('CAPTION:', '').strip()
            elif line.startswith('HASHTAGS:'):
                hashtags_line = line.replace('HASHTAGS:', '').strip()
            elif line.startswith('CTA:'):
                cta_line = line.replace('CTA:', '').strip()
        
        # Combine into final caption
        full_caption = f"{caption_line}\n\n{cta_line}\n\n{hashtags_line}"
        
        print(f"✅ Generated Instagram caption ({len(full_caption)} chars)")
        print(f"📝 Preview: {caption_line[:60]}...")
        
        return {
            'caption': caption_line,
            'hashtags': hashtags_line,
            'cta': cta_line,
            'full_caption': full_caption
        }
        
    except Exception as e:
        print(f"❌ Failed to generate Instagram caption: {e}")
        
        # Fallback caption
        return {
            'caption': f"⚽ {title[:100]}",
            'hashtags': "#cristiano #ronaldo #cr7 #football #soccer #cristianoronaldo",
            'cta': "🔗 Link in bio for full article!",
            'full_caption': f"⚽ {title[:100]}\n\n🔗 Link in bio for full article!\n\n#cristiano #ronaldo #cr7 #football"
        }


def post_to_instagram(image_path, caption_data, permalink):
    """Post image and caption to Instagram
    
    Args:
        image_path: Path to image file
        caption_data: Dict with caption info
        permalink: Article permalink for tracking
        
    Returns:
        Dict with success status and post URL
    """
    
    # Get Instagram credentials from environment
    username = os.environ.get('INSTAGRAM_USERNAME')
    password = os.environ.get('INSTAGRAM_PASSWORD')
    
    if not username or not password:
        raise ValueError(
            "Instagram credentials not found!\n"
            "Please set INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD in GitHub Secrets"
        )
    
    print(f"📸 Posting to Instagram...")
    print(f"   Username: {username}")
    print(f"   Image: {image_path}")
    
    try:
        # Initialize Instagram client
        cl = Client()
        
        # Try to load session if it exists
        session_file = "/tmp/instagram_session.json"
        
        try:
            if os.path.exists(session_file):
                cl.load_settings(session_file)
                cl.login(username, password)
                print("✅ Logged in using saved session")
            else:
                cl.login(username, password)
                cl.dump_settings(session_file)
                print("✅ Logged in and saved session")
        except LoginRequired:
            print("⚠️ Session expired, logging in fresh...")
            cl.login(username, password)
            cl.dump_settings(session_file)
        
        # Verify image exists
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Upload photo with caption
        media = cl.photo_upload(
            path=image_path,
            caption=caption_data['full_caption']
        )
        
        post_url = f"https://www.instagram.com/p/{media.code}/"
        
        print(f"✅ Posted to Instagram successfully!")
        print(f"🔗 Post URL: {post_url}")
        
        return {
            'success': True,
            'post_url': post_url,
            'media_id': media.pk,
            'permalink': permalink
        }
        
    except Exception as e:
        print(f"❌ Instagram posting failed: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'success': False,
            'error': str(e),
            'permalink': permalink
        }


def post_article_to_instagram(title, focus_kw, article, image_path, permalink):
    """Complete Instagram posting workflow
    
    Args:
        title: Article title
        focus_kw: Focus keyword
        article: Full article text
        image_path: Path to featured image
        permalink: Article permalink
        
    Returns:
        Dict with posting result
    """
    
    print(f"\n{'='*60}")
    print("📸 Instagram Posting Workflow")
    print("="*60)
    
    # Step 1: Generate caption with Gemini AI
    print("\n🤖 Step 1: Generating Instagram caption with AI...")
    
    # Get article excerpt (first 200 chars after front matter)
    article_lines = article.split('\n')
    content_started = False
    excerpt = ""
    
    for line in article_lines:
        if content_started:
            excerpt += line + " "
            if len(excerpt) > 200:
                break
        elif line.strip() == '---' and content_started:
            content_started = False
        elif line.strip() == '---':
            content_started = True
    
    caption_data = generate_instagram_caption(title, focus_kw, excerpt)
    
    # Step 2: Post to Instagram
    print("\n📤 Step 2: Posting to Instagram...")
    result = post_to_instagram(image_path, caption_data, permalink)
    
    if result['success']:
        print(f"\n✅ Instagram post successful!")
        print(f"🔗 View post: {result['post_url']}")
    else:
        print(f"\n❌ Instagram post failed: {result.get('error')}")
    
    return result


# Example usage
if __name__ == "__main__":
    # Test with sample data
    result = post_article_to_instagram(
        title="Cristiano Ronaldo's Training Routine",
        focus_kw="cristiano ronaldo training",
        article="Sample article content...",
        image_path="assets/images/test.webp",
        permalink="ronaldo-training"
    )
    
    print(f"\nResult: {result}")