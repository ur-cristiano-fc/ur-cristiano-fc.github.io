"""Main script to generate blog posts automatically"""
import os
import random
import time
import datetime

# Import all modules
from config import *
from keywords_handler import get_keyword_row, parse_keyword_row, remove_keyword_from_file, get_keywords_count
from article_generator import generate_article, generate_image_prompt
from image_generator import generate_image_freepik
from google_indexing import submit_to_google_indexing, check_indexing_status
from google_sheets_logger import log_to_google_sheets
from webpushr_notifier import send_blog_post_notification, get_subscriber_count


def main():
    print("=" * 60)
    print("🚀 Starting Blog Post Generator")
    print("=" * 60)
    
    # Verify environment variables
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY not found")
        return
    print("✅ GEMINI_API_KEY found")
    
    # Check for API keys (Unsplash/Pexels for collages)
    unsplash_key = os.environ.get("UNSPLASH_ACCESS_KEY")
    pexels_key = os.environ.get("PEXELS_API_KEY")
    
    if not unsplash_key and not pexels_key:
        print("⚠️ Warning: No UNSPLASH_ACCESS_KEY or PEXELS_API_KEY found")
        print("⚠️ Image generation will fail without these keys")
    else:
        if unsplash_key:
            print("✅ UNSPLASH_ACCESS_KEY found")
        if pexels_key:
            print("✅ PEXELS_API_KEY found")
    
    # Show keywords status
    keywords_count = get_keywords_count()
    print(f"\n📊 Posts to generate this run: {POSTS_PER_RUN}")
    print(f"📋 Keywords available: {keywords_count}")
    
    posts_generated = 0
    
    for post_num in range(1, POSTS_PER_RUN + 1):
        print(f"\n{'=' * 60}")
        print(f"📝 Processing Post {post_num}/{POSTS_PER_RUN}")
        print("=" * 60)
        
        # Get next keyword
        row = get_keyword_row()
        if not row:
            print(f"❌ No more keywords left")
            break
        
        print(f"\n📋 Keyword: {row[:80]}...")
        
        # Parse keyword with new format
        keyword_data = parse_keyword_row(row)
        if not keyword_data:
            print(f"❌ Invalid keyword format")
            remove_keyword_from_file()  # Remove invalid keyword
            continue
        
        title = keyword_data['title']
        focus_kw = keyword_data['focus_kw']
        permalink = keyword_data['permalink']
        semantic_kw = keyword_data['semantic_kw']
        affiliate_links = keyword_data['affiliate_links']
        hook_kw = keyword_data.get('hook_kw', '')
        search_kw = keyword_data.get('search_kw', '')
        
        print(f"✅ Parsed: {title[:60]}...")
        
        # Generate file paths
        today = datetime.date.today().isoformat()
        post_path = f"{POSTS_DIR}/{today}-{permalink}.md"
        image_file = f"{IMAGES_DIR}/featured_{permalink}.webp"
        
        # Check if post already exists
        if os.path.exists(post_path):
            print(f"\n⚠️  Post already exists: {post_path}")
            remove_keyword_from_file()  # Remove duplicate
            continue
        
        # Generate content
        try:
            # Step 1: Generate article
            print(f"\n{'=' * 60}")
            print("Step 1: Generating Article")
            print("=" * 60)
            article = generate_article(title, focus_kw, permalink, semantic_kw, affiliate_links, hook_kw, search_kw)
            print(f"✅ Article generated ({len(article)} characters)")
            
            
            # Step 2: Generate image prompt
            print(f"\n{'=' * 60}")
            print("Step 2: Generating Image Prompt")
            print("=" * 60)
            image_prompt = generate_image_prompt(title)
            print(f"✅ Image prompt generated")
            
            
            # Step 3: Create featured image (collage)
            print(f"\n{'=' * 60}")
            print("Step 3: Creating Article-Relevant Collage Image")
            print("=" * 60)
            
            # Use the updated generate_image_freepik (now creates collages)
            try:
                generate_image_freepik(
                    image_prompt,  # Pass title directly for better context detection
                    image_file
                )
                print(f"✅ Featured image created successfully")
            except Exception as img_error:
                print(f"❌ Image creation failed: {img_error}")
                print(f"⚠️ Skipping this post - will retry next run")
                # Don't remove keyword so it can be retried
                continue
            
            # Step 4: Save post
            print(f"\n{'=' * 60}")
            print("Step 4: Saving Post")
            print("=" * 60)
            with open(post_path, "w", encoding="utf-8") as f:
                f.write(article)
            print(f"✅ Post saved: {post_path}")
            
            post_url = f"{SITE_DOMAIN}/{permalink}"
            
            print(f"\n{'=' * 60}")
            print(f"✅ SUCCESS! Post {post_num} Generated")
            print("=" * 60)
            print(f"📰 Title: {title}")
            print(f"🌐 URL: {post_url}")
            
            posts_generated += 1
            
            # Step 5: Additional processing (indexing, logging, etc.)
            if post_num == POSTS_PER_RUN or post_num == posts_generated:
                
                # Uncomment these if you want to enable them
                # print(f"\n{'=' * 60}")
                # print(f"Step 5: Waiting {WAIT_TIME_BEFORE_INDEXING // 60} minutes")
                # print("=" * 60)
                # print("⏳ Allowing GitHub Pages to deploy...")
                
                # Step 6: Log to Sheets
                print(f"\n{'=' * 60}")
                print("Step 6: Logging to Google Sheets")
                print("=" * 60)
                
                indexing_status = "Pending"  # Set default status
                
                try:
                    log_to_google_sheets(
                        title, focus_kw, permalink,
                        image_file, article, indexing_status
                    )
                    print(f"✅ Logged to Google Sheets")
                except Exception as e:
                    print(f"⚠️ Sheets logging failed (non-critical): {e}")
                
                # Step 7: Send Push Notification (optional)
                # try:
                #     send_blog_post_notification(title, permalink, focus_kw)
                #     print(f"✅ Push notification sent")
                # except Exception as e:
                #     print(f"⚠️ Push notification failed (non-critical): {e}")
            
            # Step 8: Remove keyword after success
            print(f"\n{'=' * 60}")
            print("Step 8: Removing Keyword from File")
            print("=" * 60)
            remove_keyword_from_file()
            print(f"✅ Keyword removed - post complete")
            
        except Exception as e:
            print(f"\n{'=' * 60}")
            print(f"❌ FAILED: {e}")
            print("=" * 60)
            print(f"⚠️ Keyword NOT removed - will retry next run")
            import traceback
            traceback.print_exc()
            continue
    
    # Final summary
    print(f"\n{'=' * 60}")
    print("🎉 WORKFLOW COMPLETE")
    print("=" * 60)
    print(f"✅ Posts generated: {posts_generated}")
    print(f"📊 Keywords remaining: {get_keywords_count()}")
    
    if posts_generated == 0:
        print(f"\n⚠️ No posts were generated this run")
        print(f"💡 Check the logs above for errors")


if __name__ == "__main__":
    main()