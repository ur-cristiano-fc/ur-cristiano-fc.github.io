"""Configuration settings for the blog post generator"""
import os

# File paths
KEYWORDS_FILE = "keywords.txt"
POSTS_DIR = "_posts"
IMAGES_DIR = "assets/images"

# Site settings
SITE_DOMAIN = "https://ecommercemart.github.io"

# AI Models
TEXT_MODEL = "gemini-2.5-flash"
FREEPIK_ENDPOINT = "https://api.freepik.com/v1/ai/text-to-image/flux-dev"

# Generation settings
POSTS_PER_RUN = 1  # How many posts to generate per run

# Image settings
IMAGE_QUALITY = 80  # 1-100 (80 = good balance)
IMAGE_MAX_WIDTH = 1920
IMAGE_MAX_HEIGHT = 1080
OPTIMIZE_IMAGE = True

# Timing
WAIT_TIME_BEFORE_INDEXING = 180  # seconds (3 minutes)

# API Keys (from environment)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
FREEPIK_API_KEY = os.environ.get("FREEPIK_API_KEY")
GOOGLE_SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
GOOGLE_SPREADSHEET_ID = os.environ.get("GOOGLE_SPREADSHEET_ID")

# Create directories
os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)