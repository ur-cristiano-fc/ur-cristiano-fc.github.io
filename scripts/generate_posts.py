"""Main script to generate blog posts automatically"""
import os
import random
import time
import datetime

# Import all modules
from config import *
from keywords_handler import get_keyword_row, parse_keyword_row, remove_keyword_from_file, get_keywords_count
from article_generator import generate_article, generate_image_prompt
from image_generator import generate_image_freepik, get_random_reference_image
from google_indexing import submit_to_google_indexing, check_indexing_status
from google_sheets_logger import log_to_google_sheets
from collage_generator import create_blog_collage
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
    
    if not FREEPIK_API_KEY:
        print("❌ FREEPIK_API_KEY not found")
        return
    print("✅ FREEPIK_API_KEY found")
    
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
        hook_kw = keyword_data['hook_kw']
        search_kw = keyword_data['search_kw']
        
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
            # print(f"\n{'=' * 60}")
            # print("Step 2: Generating Image Prompt")
            # print("=" * 60)
            # image_prompt = generate_image_prompt(title)
            # print(f"✅ Image prompt generated")
            
            # Step 3: Create featured image
            print(f"\n{'=' * 60}")
            print("Step 3: Creating Unique Collage Image")
            print("=" * 60)


            # Create collage with 3-4 images
            num_images = random.choice([3, 4])
            result = create_blog_collage(
                title=title,
                output_path=image_file,
                num_images=num_images
            )

            if result['success']:
                print(f"✅ Collage created successfully")
                print(f"🎨 Layout: {result['layout']}")
                print(f"🖼️ Images used: {result['num_images']}")
                
                # Log attributions
                for i, attr in enumerate(result['attributions'], 1):
                    print(f"   {i}. Photo by {attr['photographer']} on {attr['source'].capitalize()}")
            else:
                print(f"⚠️ Collage creation failed: {result.get('error')}")
                print("📚 Falling back to curated library...")
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
            
            # Step 5: Wait before indexing
            if post_num == POSTS_PER_RUN or post_num == posts_generated:
                print(f"\n{'=' * 60}")
                print(f"Step 5: Waiting {WAIT_TIME_BEFORE_INDEXING // 60} minutes")
                print("=" * 60)
                print("⏳ Allowing GitHub Pages to deploy...")
                
                for remaining in range(WAIT_TIME_BEFORE_INDEXING, 0, -30):
                    minutes = remaining // 60
                    seconds = remaining % 60
                    print(f"⏰ Time remaining: {minutes}m {seconds}s", end='\r')
                    time.sleep(30)
                
                print(f"\n✅ Wait complete!")
                
                # Step 6: Submit to Google
                print(f"\n{'=' * 60}")
                print("Step 6: Submitting to Google")
                print("=" * 60)
                
                indexing_status = "Not Attempted"
                try:
                    success = submit_to_google_indexing(post_url)
                    indexing_status = "Success" if success else "Failed - See Logs"
                except Exception as e:
                    indexing_status = f"Failed - {str(e)[:100]}"
                    print(f"⚠️ Indexing failed (non-critical): {e}")
                
                    # Wait for Google's API to update metadata
                # if success:
                #     print(f"\n⏳ Waiting 50 seconds for Check indexing status...")
                #     for remaining in range(WAIT_TIME_BEFORE_INDEXING, 0, -30):
                #         minutes = remaining // 60
                #         seconds = remaining % 60
                #         print(f"⏰ Time remaining: {minutes}m {seconds}s", end='\r')
                #         time.sleep(30)
                
                # Step 7: Check indexing status
                try:
                    status_result = check_indexing_status(post_url)
                    
                    if status_result is None:
                        print(f"⚠️ Could not verify indexing status - check credentials")
                        indexing_status += " (Status: Unverified)"
                        
                    elif status_result == {} or 'latestUpdate' not in status_result:
                        print(f"ℹ️ No indexing history found (may take a moment to appear)")
                        indexing_status += " (Status: Pending)"
                        
                    elif status_result.get('latestUpdate', {}).get('type') == 'URL_UPDATED':
                        notify_time = status_result['latestUpdate']['notifyTime']
                        print(f"✅ Confirmed in indexing queue at {notify_time}")
                        indexing_status = "Success (Confirmed in Queue)"
                        
                    elif status_result.get('latestUpdate', {}).get('type') == 'URL_DELETED':
                        notify_time = status_result['latestUpdate']['notifyTime']
                        print(f"🗑️ URL marked for deletion at {notify_time}")
                        indexing_status = "Deleted"
                        
                except Exception as e:
                    print(f"⚠️ Error checking indexing status: {e}")
                    indexing_status += " (Verification Failed)"
                
                # Step 8: Log to Sheets
                print(f"\n{'=' * 60}")
                print("Step 7: Logging to Google Sheets")
                print("=" * 60)
                
                try:
                    log_to_google_sheets(
                        title, focus_kw, permalink,
                        image_file, article, indexing_status
                    )
                except Exception as e:
                    print(f"⚠️ Sheets logging failed (non-critical): {e}")
                
                # Step 9: Post to Twitter

                # Step 10: Post to LinkedIn
                    
                # Step 11: Send Push Notification

                # try:
                #     send_blog_post_notification(title, permalink, focus_kw)
                # except Exception as e:
                #     print(f"⚠️ Push notification failed (non-critical): {e}")
            
            print(f"\n{'=' * 60}")
            print("Step 11: Removing Keyword from File")
            print("=" * 60)
            
            # Step 12: Remove keyword after success
            print(f"\n{'=' * 60}")
            print("Step 10: Removing Keyword from File")
            print("=" * 60)
            remove_keyword_from_file()
            
        except Exception as e:
            print(f"\n{'=' * 60}")
            print(f"❌ FAILED: {e}")
            print("=" * 60)
            print(f"⚠️ Keyword NOT removed - will retry next run")
            continue
    
    # Final summary
    print(f"\n{'=' * 60}")
    print("🎉 WORKFLOW COMPLETE")
    print("=" * 60)
    print(f"✅ Posts generated: {posts_generated}")
    print(f"📊 Keywords remaining: {get_keywords_count()}")


if __name__ == "__main__":
    main()