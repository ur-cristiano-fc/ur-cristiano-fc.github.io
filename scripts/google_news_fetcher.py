"""Fetch trending Cristiano Ronaldo topics from Google News"""
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
from article_generator import client, TEXT_MODEL
import time
import random


class GoogleNewsFetcher:
    """Fetch and process trending news about Cristiano Ronaldo"""
    
    def __init__(self):
        self.base_url = "https://news.google.com/rss/search"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def fetch_trending_topics(self, max_results=10):
        """
        Fetch trending news about Cristiano Ronaldo from Google News
        
        Args:
            max_results: Maximum number of news items to fetch
            
        Returns:
            List of news items with title, description, link, and published date
        """
        
        print("📰 Fetching trending Cristiano Ronaldo news from Google News...")
        
        # Search queries for different aspects
        queries = [
            "Cristiano Ronaldo",
            "CR7 news",
            "Ronaldo latest"
        ]
        
        all_news = []
        
        for query in queries:
            try:
                # Google News RSS feed URL
                params = {
                    'q': query,
                    'hl': 'en-US',
                    'gl': 'US',
                    'ceid': 'US:en'
                }
                
                # Build URL
                url = f"{self.base_url}?q={query}&hl=en-US&gl=US&ceid=US:en"
                
                print(f"🔍 Searching: {query}")
                
                response = requests.get(url, headers=self.headers, timeout=15)
                response.raise_for_status()
                
                # Parse RSS feed
                soup = BeautifulSoup(response.content, 'xml')
                items = soup.find_all('item')
                
                for item in items[:max_results]:
                    try:
                        title = item.find('title').text if item.find('title') else None
                        link = item.find('link').text if item.find('link') else None
                        pub_date = item.find('pubDate').text if item.find('pubDate') else None
                        description = item.find('description').text if item.find('description') else ""
                        
                        if title and link:
                            # Check if already in list (avoid duplicates)
                            if not any(news['title'] == title for news in all_news):
                                all_news.append({
                                    'title': title,
                                    'description': description,
                                    'link': link,
                                    'pub_date': pub_date,
                                    'source_query': query
                                })
                    except Exception as e:
                        print(f"⚠️ Error parsing item: {e}")
                        continue
                
                print(f"✅ Found {len(items)} news items for '{query}'")
                
                # Add delay between queries
                time.sleep(random.uniform(1, 2))
                
            except Exception as e:
                print(f"❌ Error fetching news for '{query}': {e}")
                continue
        
        # Sort by recency (most recent first)
        all_news = sorted(all_news, key=lambda x: x['pub_date'] or '', reverse=True)
        
        print(f"✅ Total unique news items fetched: {len(all_news)}")
        
        return all_news[:max_results]
    
    def filter_suitable_topics(self, news_items):
        """
        Use Gemini AI to filter news items that are suitable for blog posts
        
        Args:
            news_items: List of news items
            
        Returns:
            Filtered list of suitable news items
        """
        
        if not news_items:
            return []
        
        print("🤖 Using AI to filter suitable blog topics...")
        
        # Prepare news list for Gemini
        news_list = []
        for i, item in enumerate(news_items[:20]):  # Analyze max 20
            news_list.append(f"{i}. {item['title']}")
        
        news_text = '\n'.join(news_list)
        
        prompt = f"""
You are a blog content strategist for a Cristiano Ronaldo fan website.

Here are recent news headlines about Cristiano Ronaldo:
{news_text}

Task: Select the 5 BEST headlines for creating engaging blog posts.

Criteria for selection:
- Interesting and engaging for fans
- Not too controversial or negative
- Has enough content potential for a 2000+ word article
- Recent and relevant
- Avoids purely speculative rumors
- Good for SEO and social sharing

Return ONLY the numbers (0-19) of the 5 best headlines, separated by commas.
Example response: 0,3,7,12,15

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
            indices = [i for i in indices if i < len(news_items)][:5]
            
            if not indices:
                # Fallback: use first 5
                indices = list(range(min(5, len(news_items))))
            
            filtered_news = [news_items[i] for i in indices]
            
            print(f"✅ AI selected {len(filtered_news)} suitable topics")
            for i, news in enumerate(filtered_news, 1):
                print(f"   {i}. {news['title'][:80]}...")
            
            return filtered_news
            
        except Exception as e:
            print(f"⚠️ AI filtering failed: {e}")
            # Fallback: return first 5
            return news_items[:5]
    
    def generate_blog_metadata_from_news(self, news_item):
        """
        Generate blog post metadata from a news item using Gemini AI
        
        Args:
            news_item: Dictionary with news title, description, link
            
        Returns:
            Dictionary with title, focus_kw, permalink, semantic_kw, hook_kw, search_kw
        """
        
        print(f"🤖 Generating blog metadata for: {news_item['title'][:60]}...")
        
        prompt = f"""
You are creating a blog post for a Cristiano Ronaldo fan website.

News Headline: {news_item['title']}
News Description: {news_item.get('description', 'N/A')}
Source: {news_item.get('link', 'N/A')}

Generate the following for a blog post:

1. Blog Title (engaging, SEO-friendly, 60-70 characters, must include "Cristiano Ronaldo" or "CR7")
2. Focus Keyword (main SEO keyword, 2-5 words)
3. URL Permalink (lowercase, hyphens, no special chars, descriptive)
4. Semantic Keywords (5-8 LSI keywords, comma-separated)
5. Hook Keyword (catchy phrase for social media, 3-6 words)
6. Search Intent Keywords (what users search for, comma-separated)

Format your response EXACTLY like this (one per line, no extra text):
TITLE: Your blog title here
FOCUS_KW: your focus keyword
PERMALINK: your-url-permalink
SEMANTIC_KW: keyword1, keyword2, keyword3, keyword4, keyword5
HOOK_KW: Your catchy hook here
SEARCH_KW: search term1, search term2, search term3

Return ONLY these 6 lines, nothing else.
"""
        
        try:
            response = client.models.generate_content(
                model=TEXT_MODEL,
                contents=prompt
            )
            
            # Parse response
            lines = response.text.strip().split('\n')
            metadata = {}
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower().replace('_', '')
                    value = value.strip()
                    
                    if key == 'title':
                        metadata['title'] = value
                    elif key == 'focuskw':
                        metadata['focus_kw'] = value
                    elif key == 'permalink':
                        metadata['permalink'] = value
                    elif key == 'semantickw':
                        metadata['semantic_kw'] = value
                    elif key == 'hookkw':
                        metadata['hook_kw'] = value
                    elif key == 'searchkw':
                        metadata['search_kw'] = value
            
            # Validate required fields
            required = ['title', 'focus_kw', 'permalink', 'semantic_kw']
            if not all(k in metadata for k in required):
                raise ValueError(f"Missing required fields. Got: {list(metadata.keys())}")
            
            # Ensure permalink is clean
            metadata['permalink'] = self._clean_permalink(metadata['permalink'])
            
            # Add empty affiliate_links
            metadata['affiliate_links'] = ""
            
            # Add source link for reference
            metadata['source_link'] = news_item.get('link', '')
            
            print(f"✅ Generated metadata:")
            print(f"   Title: {metadata['title'][:70]}...")
            print(f"   Focus KW: {metadata['focus_kw']}")
            print(f"   Permalink: {metadata['permalink']}")
            
            return metadata
            
        except Exception as e:
            print(f"❌ Metadata generation failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _clean_permalink(self, permalink):
        """Clean permalink to ensure it's URL-safe"""
        # Remove any remaining special characters
        permalink = re.sub(r'[^a-z0-9\-]', '', permalink.lower())
        # Remove multiple consecutive hyphens
        permalink = re.sub(r'-+', '-', permalink)
        # Remove leading/trailing hyphens
        permalink = permalink.strip('-')
        return permalink
    
    def get_trending_topic_for_blog(self):
        """
        Main method: Fetch trending news and return one topic ready for blog generation
        
        Returns:
            Dictionary with all metadata needed for blog generation, or None if failed
        """
        
        print("=" * 60)
        print("🔥 FETCHING TRENDING CRISTIANO RONALDO TOPIC")
        print("=" * 60)
        
        # Step 1: Fetch news
        news_items = self.fetch_trending_topics(max_results=15)
        
        if not news_items:
            print("❌ No news items found")
            return None
        
        # Step 2: Filter suitable topics
        suitable_topics = self.filter_suitable_topics(news_items)
        
        if not suitable_topics:
            print("❌ No suitable topics found")
            return None
        
        # Step 3: Select the best one (first from filtered list)
        selected_news = suitable_topics[0]
        
        print(f"\n✅ Selected trending topic:")
        print(f"   {selected_news['title']}")
        print(f"   Published: {selected_news.get('pub_date', 'Unknown')}")
        
        # Step 4: Generate blog metadata
        metadata = self.generate_blog_metadata_from_news(selected_news)
        
        if not metadata:
            print("❌ Failed to generate metadata")
            return None
        
        print(f"\n✅ Topic ready for blog generation!")
        
        return metadata


def test_fetcher():
    """Test the Google News fetcher"""
    
    fetcher = GoogleNewsFetcher()
    
    # Get a trending topic
    topic = fetcher.get_trending_topic_for_blog()
    
    if topic:
        print("\n" + "=" * 60)
        print("📋 GENERATED TOPIC METADATA")
        print("=" * 60)
        for key, value in topic.items():
            print(f"{key}: {value}")
    else:
        print("❌ Failed to fetch trending topic")


if __name__ == "__main__":
    test_fetcher()