"""Log published posts to Google Sheets"""
import os
import re
import json
import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from config import GOOGLE_SERVICE_ACCOUNT_JSON, GOOGLE_SPREADSHEET_ID, SITE_DOMAIN


def log_to_google_sheets(title, focus_kw, permalink, image_path, article_content, indexing_status):
    """Log post data to Google Sheets"""
    
    if not GOOGLE_SERVICE_ACCOUNT_JSON:
        print("⚠️ GOOGLE_SERVICE_ACCOUNT_JSON not found - skipping logging")
        return False
    
    if not GOOGLE_SPREADSHEET_ID:
        print("⚠️ GOOGLE_SPREADSHEET_ID not found - skipping logging")
        return False
    
    try:
        print(f"📊 Logging to Google Sheets...")
        
        # Parse credentials
        credentials_info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
        
        # Create credentials with Sheets scope
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        
        # Build Sheets service
        service = build('sheets', 'v4', credentials=credentials)
        
        # Extract description (first 200 chars, removing markdown)
        clean_content = re.sub(r'[#*`\[\]]', '', article_content)
        description = ' '.join(clean_content.split())[:200] + "..."
        
        # Prepare row data
        timestamp = datetime.datetime.now().isoformat()
        row_data = [
            timestamp,
            title,
            focus_kw,
            permalink,
            f"{SITE_DOMAIN}/{permalink}/",
            f"{SITE_DOMAIN}/images/{os.path.basename(image_path)}",
            description,
            indexing_status,
            article_content
        ]
        
        # Append to sheet
        body = {'values': [row_data]}
        
        result = service.spreadsheets().values().append(
            spreadsheetId=GOOGLE_SPREADSHEET_ID,
            range='Sheet1!A:I',
            valueInputOption='RAW',
            body=body
        ).execute()
        
        print(f"✅ Successfully logged to Google Sheets!")
        print(f"📊 Added row: {result.get('updates', {}).get('updatedRows', 0)}")
        return True
        
    except Exception as e:
        print(f"❌ Error logging to Google Sheets: {e}")
        return False