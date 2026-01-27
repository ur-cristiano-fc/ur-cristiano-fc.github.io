"""Main script to generate blog posts from trending Google News topics"""
import os
import datetime

# Import all modules
from config import *
from article_generator import generate_article, generate_description
from image_generator import generate_image_freepik
from webpushr_notifier import send_blog_post_notification
from google_news_fetcher import GoogleNewsFetcher


def main():
    print("=" * 60)
    print("🚀 Starting AI Blog Generator - Google News Mode")
    print("=" * 60)
    
    # Verify environment variables
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY not found")
        return
    print("✅ GEMINI_API_KEY found")
    
    # Check for Google Custom Search API keys (for image generation)
    if not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_ENGINE_ID:
        print("❌ Google Custom Search API credentials not found")
        print("   Required: GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_ENGINE_ID")
        print("   Image generation will fail without these keys")
        return
    print("✅ GOOGLE_SEARCH_API_KEY found")
    print("✅ GOOGLE_SEARCH_ENGINE_ID found")
    
    # Check for Pinterest credentials (optional)
    pinterest_enabled = bool(os.environ.get('PINTEREST_EMAIL') and os.environ.get('PINTEREST_PASSWORD'))
    if pinterest_enabled:
        print("✅ Pinterest credentials found - auto-posting enabled")
    else:
        print("ℹ️ Pinterest credentials not found - skipping Pinterest posts")
    
    print(f"\n📊 Posts to generate this run: {POSTS_PER_RUN}")
    
    posts_generated = 0
    
    # Initialize Google News fetcher
    news_fetcher = GoogleNewsFetcher()
    
    for post_num in range(1, POSTS_PER_RUN + 1):
        print(f"\n{'=' * 60}")
        print(f"📝 Processing Post {post_num}/{POSTS_PER_RUN}")
        print("=" * 60)
        
        # Fetch trending topic from Google News
        print("\n🔥 Fetching trending Cristiano Ronaldo topic from Google News...")
        keyword_data = news_fetcher.get_trending_topic_for_blog()
        
        if not keyword_data:
            print(f"❌ Failed to fetch trending topic")
            continue
        
        title = keyword_data['title']
        focus_kw = keyword_data['focus_kw']
        permalink = keyword_data['permalink']
        semantic_kw = keyword_data['semantic_kw']
        affiliate_links = keyword_data.get('affiliate_links', '')
        hook_kw = keyword_data.get('hook_kw', '')
        search_kw = keyword_data.get('search_kw', '')
        source_link = keyword_data.get('source_link', '')
        
        print(f"✅ Topic selected: {title[:60]}...")
        
        # Generate file paths
        today = datetime.date.today().isoformat()
        post_path = f"{POSTS_DIR}/{today}-{permalink}.md"
        image_file = f"{IMAGES_DIR}/featured_{permalink}.webp"
        
        # Check if post already exists
        if os.path.exists(post_path):
            print(f"\n⚠️ Post already exists: {post_path}")
            print(f"   This topic may have already been covered")
            continue
        
        # Generate content
        try:
            # Step 1: Generate article
            print(f"\n{'=' * 60}")
            print("Step 1: Generating Article")
            print("=" * 60)
            print(f"📰 Source: {source_link}")
            article = generate_article(title, focus_kw, permalink, semantic_kw, affiliate_links, hook_kw, search_kw)
            print(f"✅ Article generated ({len(article)} characters)")
            
            # Step 2: Create featured image
            print(f"\n{'=' * 60}")
            print("Step 2: Creating AI-Powered Collage with Relevant Images")
            print("=" * 60)
            
            try:
                generate_image_freepik(
                    title,
                    image_file
                )
                print(f"✅ Featured image collage created successfully")
                
                # Add image to git
                if os.path.exists(image_file):
                    os.system(f"git add {image_file}")
                    print(f"✅ Image added to git: {image_file}")
                
            except Exception as img_error:
                print(f"❌ Image creation failed: {img_error}")
                print(f"⚠️ Skipping this post - will try a different topic next run")
                import traceback
                traceback.print_exc()
                continue
            
            # Step 3: Save post
            print(f"\n{'=' * 60}")
            print("Step 3: Saving Post")
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
            print(f"📰 Source: {source_link}")
            
            posts_generated += 1
            
            # Step 4: Additional processing (social media, notifications, etc.)
            if post_num == POSTS_PER_RUN or post_num == posts_generated:
                
                # Step 4a: Post to Pinterest (if enabled)
                # if pinterest_enabled:
                #     print(f"\n{'=' * 60}")
                #     print("Step 4a: Creating & Posting Pinterest Pins")
                #     print("=" * 60)

                #     try:
                #         from pinterest_selenium_poster import post_to_pinterest_selenium
                        
                #         description = generate_description(title, focus_kw)
                #         hook_text = hook_kw if hook_kw else f"{focus_kw.title()} Guide"
                        
                #         success = post_to_pinterest_selenium(
                #             title=title,
                #             focus_kw=focus_kw,
                #             permalink=permalink,
                #             featured_image_path=image_file,
                #             description=description,
                #             hook_text=hook_text
                #         )
                        
                #         if success:
                #             print(f"✅ Posted to Pinterest successfully!")
                #         else:
                #             print(f"⚠️ Pinterest posting failed")
                                
                #     except ImportError as e:
                #         print(f"⚠️ Pinterest module not available: {e}")
                #     except Exception as e:
                #         print(f"⚠️ Pinterest posting failed (non-critical): {e}")
                #         import traceback
                #         traceback.print_exc()
                # else:
                #     print(f"\n{'=' * 60}")
                #     print("Step 4a: Pinterest posting skipped (credentials not configured)")
                #     print("=" * 60)
                
                # Step 4b: Send Push Notification
                print(f"\n{'=' * 60}")
                print("Step 4b: Sending Push Notification")
                print("=" * 60)
                
                try:
                    send_blog_post_notification(title, permalink, focus_kw)
                    print(f"✅ Push notification sent")
                except Exception as e:
                    print(f"⚠️ Push notification failed (non-critical): {e}")
            
            print(f"\n{'=' * 60}")
            print("✅ Post Complete!")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n{'=' * 60}")
            print(f"❌ FAILED: {e}")
            print("=" * 60)
            print(f"⚠️ Will try a different topic next run")
            import traceback
            traceback.print_exc()
            continue
    
    # Final summary
    print(f"\n{'=' * 60}")
    print("🎉 WORKFLOW COMPLETE")
    print("=" * 60)
    print(f"✅ Posts generated: {posts_generated}")
    print(f"📰 Source: Google News (Trending Topics)")
    
    if posts_generated == 0:
        print(f"\n⚠️ No posts were generated this run")
        print(f"💡 Check the logs above for errors")


if __name__ == "__main__":
    main()