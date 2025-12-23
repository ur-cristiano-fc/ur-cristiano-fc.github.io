"""Submit URLs to Google Search Console for indexing"""
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from config import GOOGLE_SERVICE_ACCOUNT_JSON


def submit_to_google_indexing(url):
    """Submit URL to Google Indexing API"""
    
    if not GOOGLE_SERVICE_ACCOUNT_JSON:
        print("⚠️ GOOGLE_SERVICE_ACCOUNT_JSON not found - skipping indexing")
        return False
    
    try:
        print(f"🔐 Parsing service account credentials...")
        credentials_info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
        
        # Validate required fields
        required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
        missing_fields = [field for field in required_fields if field not in credentials_info]
        
        if missing_fields:
            print(f"❌ Missing fields: {', '.join(missing_fields)}")
            return False
        
        print(f"📝 Service account: {credentials_info.get('client_email')}")
        print(f"🔧 Creating credentials...")
        
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info,
            scopes=['https://www.googleapis.com/auth/indexing']
        )
        
        print(f"🔨 Building Indexing API service...")
        service = build('indexing', 'v3', credentials=credentials)
        
        body = {
            'url': url,
            'type': 'URL_UPDATED'
        }
        
        print(f"📤 Submitting URL: {url}")
        response = service.urlNotifications().publish(body=body).execute()
        
        print(f"✅ Successfully submitted to Google!")
        print(f"📋 Response: {response}")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return False
    except Exception as e:
        print(f"❌ Error submitting to Google: {e}")
        return False
    
def check_indexing_status(url):
    """Check the indexing status of a submitted URL"""
    if not GOOGLE_SERVICE_ACCOUNT_JSON:
        print("⚠️ GOOGLE_SERVICE_ACCOUNT_JSON not found")
        return None
    
    try:
        credentials_info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info,
            scopes=['https://www.googleapis.com/auth/indexing']
        )
        
        service = build('indexing', 'v3', credentials=credentials)
        
        print(f"📊 Checking indexing status for: {url}")
        response = service.urlNotifications().getMetadata(url=url).execute()
        
        if 'latestUpdate' in response:
            latest = response['latestUpdate']
            print(f"✅ Status: {latest.get('type')}")
            print(f"📅 Notify time: {latest.get('notifyTime')}")
        else:
            print(f"ℹ️ No indexing history found for this URL")
        
        return response
        
    except Exception as e:
        print(f"❌ Error checking status: {e}")
        return None