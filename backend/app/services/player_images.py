# backend/app/services/player_images.py
import os
import requests
from typing import Optional, Dict
from urllib.parse import quote
import hashlib
import json
from datetime import datetime, timedelta

class PlayerImageService:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.cx = os.getenv('GOOGLE_CX')  # Custom Search Engine ID
        self.cache_dir = 'backend/cache/player_images'
        self.cache_duration = timedelta(days=30)  # Cache for 30 days
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def _get_cache_key(self, player_name: str, team: str) -> str:
        """Generate cache key for player"""
        return hashlib.md5(f"{player_name}_{team}".encode()).hexdigest()
    
    def _get_cached_image(self, cache_key: str) -> Optional[str]:
        """Check if we have a cached image URL"""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                    
                # Check if cache is still valid
                cached_time = datetime.fromisoformat(cache_data['timestamp'])
                if datetime.now() - cached_time < self.cache_duration:
                    return cache_data['image_url']
            except:
                pass
                
        return None
    
    def _save_to_cache(self, cache_key: str, image_url: str):
        """Save image URL to cache"""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        cache_data = {
            'image_url': image_url,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f)
    
    def search_player_image(self, player_name: str, team: str) -> Optional[str]:
        """
        Search for player image using Google Custom Search API
        Returns the first suitable image URL or None
        """
        # Check cache first
        cache_key = self._get_cache_key(player_name, team)
        cached_url = self._get_cached_image(cache_key)
        if cached_url:
            return cached_url
        
        if not self.api_key or not self.cx:
            print("Google API credentials not configured")
            return None
            
        try:
            # Build search query - optimized for football player headshots
            query = f"{player_name} profile face image TRANSPARENT"
            
            # API endpoint
            url = "https://www.googleapis.com/customsearch/v1"
            
            params = {
                'key': self.api_key,
                'cx': self.cx,
                'q': query,
                'searchType': 'image',
                'num': 5,  # Get top 5 results
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                # Look through results for best match
                if 'items' in data and len(data['items']) > 0:
                    for item in data['items']:
                        image_url = item.get('link')
                        
                        # Basic validation - avoid logos, crests, etc
                        if image_url:
                            # Cache the result
                            self._save_to_cache(cache_key, image_url)
                            return image_url
                            
            else:
                print(f"API Error: {response.status_code}")
                
        except Exception as e:
            print(f"Error fetching player image: {e}")
            
        return None

    
    def get_fallback_image(self, player_name: str) -> str:
        """
        Generate a fallback image URL using a service like UI Avatars
        """
        initials = ''.join([part[0].upper() for part in player_name.split()[:2]])
        
        # Using UI Avatars as fallback
        return f"https://ui-avatars.com/api/?name={quote(player_name)}&background=1a1a1a&color=ff6b6b&size=200"

# Singleton instance
player_image_service = PlayerImageService()