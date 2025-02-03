# properties/utils.py
import requests
from django.conf import settings
from typing import Optional, Tuple

class GeocodingService:
    def __init__(self):
        # For testing, we'll use a dummy key if the setting isn't configured
        self.api_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', 'dummy_key')
        self.base_url = "https://maps.googleapis.com/maps/api/geocode/json"

    def get_coordinates(self, address: str) -> Optional[Tuple[float, float]]:
        """Convert address to coordinates using Google Geocoding API."""
        try:
            params = {
                'address': address,
                'key': self.api_key
            }
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            if data['status'] == 'OK':
                location = data['results'][0]['geometry']['location']
                return location['lat'], location['lng']
            return None
        except Exception as e:
            print(f"Geocoding error: {str(e)}")
            return None