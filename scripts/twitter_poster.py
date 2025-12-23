"""Post to Twitter/X automatically"""
import os
import tweepy
from config import SITE_DOMAIN

# Twitter API credentials from environment
TWITTER_API_KEY = os.environ.get("TWITTER_API_KEY")
TWITTER_API_SECRET = os.environ.get("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.environ.get("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")
TWITTER_BEARER_TOKEN = os.environ.get("TWITTER_BEARER_TOKEN")


def post_to_twitter(title, permalink, twitter_content, affiliate_links=""):
    """
    Post article to Twitter/X
    
    Args:
        title: Article title
        permalink: Article permalink
        twitter_content: Pre-written Twitter thread content
        affiliate_links: Optional affiliate links to include
    
    Returns:
        bool: Success status
    """
    
    if not all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET]):
        print("⚠️ Twitter API credentials not found - skipping Twitter post")
        return False
    
    try:
        print(f"🐦 Posting to Twitter...")
        
        # Initialize Twitter API v2 client
        client = tweepy.Client(
            bearer_token=TWITTER_BEARER_TOKEN,
            consumer_key=TWITTER_API_KEY,
            consumer_secret=TWITTER_API_SECRET,
            access_token=TWITTER_ACCESS_TOKEN,
            access_token_secret=TWITTER_ACCESS_TOKEN_SECRET
        )
        
        # Construct post URL
        post_url = f"{SITE_DOMAIN}{permalink}"
        
        # Replace [link] placeholder with actual URL
        twitter_content = twitter_content.replace("[link]", post_url)
        
        # Add affiliate links if provided
        if affiliate_links:
            twitter_content += f"\n\n📎 Resources:\n{affiliate_links[:100]}..."
        
        # Split thread content by [1/10], [2/10] pattern for threads
        if "[1/" in twitter_content and "/" in twitter_content:
            # This is a thread - split into individual tweets
            tweets = split_twitter_thread(twitter_content)
            post_twitter_thread(client, tweets)
        else:
            # Single tweet
            # Twitter limit is 280 characters
            if len(twitter_content) > 280:
                twitter_content = twitter_content[:270] + "... " + post_url
            
            response = client.create_tweet(text=twitter_content)
            print(f"✅ Tweet posted! ID: {response.data['id']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error posting to Twitter: {e}")
        return False


def split_twitter_thread(thread_content):
    """Split thread content into individual tweets"""
    import re
    
    # Split by tweet numbers like [1/10], [2/10], etc.
    # Pattern: [number/total]
    pattern = r'\[(\d+)/\d+\]'
    
    # Find all tweet markers
    markers = list(re.finditer(pattern, thread_content))
    
    tweets = []
    for i, marker in enumerate(markers):
        start = marker.start()
        # End is the start of next marker, or end of content
        end = markers[i + 1].start() if i + 1 < len(markers) else len(thread_content)
        
        tweet_text = thread_content[start:end].strip()
        tweets.append(tweet_text)
    
    # If no markers found, split by length
    if not tweets:
        tweets = split_by_length(thread_content)
    
    return tweets


def split_by_length(content, max_length=280):
    """Split long content into tweets by length"""
    tweets = []
    current_tweet = ""
    
    sentences = content.split(". ")
    
    for sentence in sentences:
        if len(current_tweet) + len(sentence) + 2 < max_length:
            current_tweet += sentence + ". "
        else:
            if current_tweet:
                tweets.append(current_tweet.strip())
            current_tweet = sentence + ". "
    
    if current_tweet:
        tweets.append(current_tweet.strip())
    
    return tweets


def post_twitter_thread(client, tweets):
    """Post a Twitter thread"""
    print(f"🧵 Posting thread with {len(tweets)} tweets...")
    
    previous_tweet_id = None
    
    for i, tweet_text in enumerate(tweets, 1):
        try:
            # Ensure tweet is under 280 characters
            if len(tweet_text) > 280:
                tweet_text = tweet_text[:277] + "..."
            
            # Post tweet (reply to previous if it's a thread)
            if previous_tweet_id:
                response = client.create_tweet(
                    text=tweet_text,
                    in_reply_to_tweet_id=previous_tweet_id
                )
            else:
                response = client.create_tweet(text=tweet_text)
            
            previous_tweet_id = response.data['id']
            print(f"✅ Tweet {i}/{len(tweets)} posted")
            
            # Small delay between tweets to avoid rate limits
            import time
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Error posting tweet {i}: {e}")
            break
    
    print(f"✅ Thread completed!")


def get_twitter_post_link(tweet_id):
    """Generate Twitter post link"""
    # You'll need to get your Twitter username
    username = os.environ.get("TWITTER_USERNAME", "yourusername")
    return f"https://twitter.com/{username}/status/{tweet_id}"