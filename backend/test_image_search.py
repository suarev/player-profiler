# backend/test_image_search.py
import os
from dotenv import load_dotenv
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from app.services.player_images import player_image_service

# Test with a known player
player_name = "Erling Haaland"
team = "Manchester City"

print(f"Testing image search for {player_name}...")
image_url = player_image_service.search_player_image(player_name, team)

if image_url:
    print(f"✅ Success! Found image: {image_url}")
else:
    print("❌ No image found. Check your API credentials.")
    print(f"API Key present: {'GOOGLE_API_KEY' in os.environ}")
    print(f"CX present: {'GOOGLE_CX' in os.environ}")