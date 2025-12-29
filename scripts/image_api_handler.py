"""Fetch images from Unsplash and Pexels APIs"""
import os
import requests
from io import BytesIO
from PIL import Image

# API Keys from environment
UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY")
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")


class ImageAPIHandler:
    """Handle image fetching from multiple free APIs"""
    
    def __init__(self):
        self.unsplash_base = "https://api.unsplash.com"
        self.pexels_base = "https://api.pexels.com/v1"
    
    def search_unsplash(self, query, per_page=5):
        """Search Unsplash for images"""
        
        if not UNSPLASH_ACCESS_KEY:
            print("⚠️ UNSPLASH_ACCESS_KEY not set")
            return []
        
        try:
            url = f"{self.unsplash_base}/search/photos"
            headers = {
                "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"
            }
            params = {
                "query": query,
                "per_page": per_page,
                "orientation": "landscape"
            }
            
            print(f"🔍 Searching Unsplash: {query}")
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for photo in data.get('results', []):
                # Trigger download endpoint (required by Unsplash ToS)
                self._trigger_unsplash_download(photo.get('links', {}).get('download_location'))
                
                results.append({
                    'url': photo['urls']['regular'],
                    'photographer': photo['user']['name'],
                    'photographer_url': photo['user']['links']['html'],
                    'source': 'unsplash',
                    'id': photo['id']
                })
            
            print(f"✅ Found {len(results)} Unsplash images")
            return results
            
        except Exception as e:
            print(f"❌ Unsplash error: {e}")
            return []
    
    def _trigger_unsplash_download(self, download_location):
        """Trigger Unsplash download tracking (REQUIRED by ToS)"""
        if not download_location or not UNSPLASH_ACCESS_KEY:
            return
        
        try:
            headers = {
                "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"
            }
            requests.get(download_location, headers=headers, timeout=5)
        except:
            pass
    
    def search_pexels(self, query, per_page=5):
        """Search Pexels for images"""
        
        if not PEXELS_API_KEY:
            print("⚠️ PEXELS_API_KEY not set")
            return []
        
        try:
            url = f"{self.pexels_base}/search"
            headers = {
                "Authorization": PEXELS_API_KEY
            }
            params = {
                "query": query,
                "per_page": per_page,
                "orientation": "landscape"
            }
            
            print(f"🔍 Searching Pexels: {query}")
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for photo in data.get('photos', []):
                results.append({
                    'url': photo['src']['large'],
                    'photographer': photo['photographer'],
                    'photographer_url': photo['photographer_url'],
                    'source': 'pexels',
                    'id': photo['id']
                })
            
            print(f"✅ Found {len(results)} Pexels images")
            return results
            
        except Exception as e:
            print(f"❌ Pexels error: {e}")
            return []
    
    def get_images_for_collage(self, query, num_images=4):
        """Get images from multiple sources for collage"""
        
        all_images = []
        
        # Try Unsplash first (higher quality)
        unsplash_images = self.search_unsplash(query, per_page=num_images)
        all_images.extend(unsplash_images)
        
        # If not enough, try Pexels
        if len(all_images) < num_images:
            needed = num_images - len(all_images)
            pexels_images = self.search_pexels(query, per_page=needed)
            all_images.extend(pexels_images)
        
        return all_images[:num_images]
    
    def download_image(self, url):
        """Download image from URL and return PIL Image"""
        
        try:
            print(f"📥 Downloading image...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            img = Image.open(BytesIO(response.content)).convert('RGB')
            print(f"✅ Downloaded: {img.size[0]}x{img.size[1]}")
            
            return img
            
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return None