"""Post to LinkedIn automatically"""
import os
import requests
from config import SITE_DOMAIN

# LinkedIn API credentials from environment
LINKEDIN_ACCESS_TOKEN = os.environ.get("LINKEDIN_ACCESS_TOKEN")
LINKEDIN_PERSON_ID = os.environ.get("LINKEDIN_PERSON_ID")


def post_to_linkedin(title, permalink, linkedin_content, affiliate_links=""):
    """
    Post article to LinkedIn
    
    Args:
        title: Article title
        permalink: Article permalink
        linkedin_content: Pre-written LinkedIn post content
        affiliate_links: Optional affiliate links to include
    
    Returns:
        bool: Success status
    """
    
    if not LINKEDIN_ACCESS_TOKEN:
        print("⚠️ LinkedIn access token not found - skipping LinkedIn post")
        return False
    
    if not LINKEDIN_PERSON_ID:
        print("⚠️ LinkedIn person ID not found - skipping LinkedIn post")
        return False
    
    try:
        print(f"💼 Posting to LinkedIn...")
        
        # Construct post URL
        post_url = f"{SITE_DOMAIN}{permalink}"
        
        # Replace [link] placeholder with actual URL
        linkedin_content = linkedin_content.replace("[link]", post_url)
        
        # Add affiliate links if provided
        if affiliate_links:
            linkedin_content += f"\n\n📎 Recommended Resources:\n{affiliate_links}"
        
        # LinkedIn post payload
        headers = {
            "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        
        # LinkedIn API endpoint
        api_url = "https://api.linkedin.com/v2/ugcPosts"
        
        # Prepare post data
        post_data = {
            "author": f"urn:li:person:{LINKEDIN_PERSON_ID}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": linkedin_content
                    },
                    "shareMediaCategory": "ARTICLE",
                    "media": [
                        {
                            "status": "READY",
                            "description": {
                                "text": title
                            },
                            "originalUrl": post_url,
                            "title": {
                                "text": title
                            }
                        }
                    ]
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        
        # Post to LinkedIn
        response = requests.post(api_url, headers=headers, json=post_data)
        
        if response.status_code == 201:
            post_id = response.json().get("id")
            print(f"✅ LinkedIn post created! ID: {post_id}")
            return True
        else:
            print(f"❌ LinkedIn API error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
    except Exception as e:
        print(f"❌ Error posting to LinkedIn: {e}")
        return False


def post_simple_linkedin_text(text_content):
    """
    Post simple text to LinkedIn without article link
    
    Args:
        text_content: Text content to post
    
    Returns:
        bool: Success status
    """
    
    if not LINKEDIN_ACCESS_TOKEN or not LINKEDIN_PERSON_ID:
        print("⚠️ LinkedIn credentials not found")
        return False
    
    try:
        headers = {
            "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        
        api_url = "https://api.linkedin.com/v2/ugcPosts"
        
        post_data = {
            "author": f"urn:li:person:{LINKEDIN_PERSON_ID}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text_content
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        
        response = requests.post(api_url, headers=headers, json=post_data)
        
        if response.status_code == 201:
            print(f"✅ LinkedIn text post created!")
            return True
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def format_linkedin_content(content):
    """
    Format content for LinkedIn
    - LinkedIn allows up to 3000 characters
    - Supports emojis and hashtags
    """
    
    # LinkedIn max length
    max_length = 3000
    
    if len(content) > max_length:
        content = content[:max_length - 50] + "...\n\n[Read full post at link]"
    
    return content


def extract_hashtags(content):
    """Extract hashtags from content"""
    import re
    hashtags = re.findall(r'#\w+', content)
    return hashtags