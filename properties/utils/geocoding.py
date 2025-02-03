import requests
from django.conf import settings
from typing import Optional, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class GeocodingService:
    def __init__(self):
        self.api_key = settings.GOOGLE_MAPS_API_KEY
        self.base_url = "https://maps.googleapis.com/maps/api/geocode/json"

    def get_location_details(self, address: str) -> Optional[Dict[str, Any]]:
        """
        Get full location details including coordinates from Google Geocoding API.
        
        Args:
            address: The address to geocode
            
        Returns:
            Dictionary containing location details or None if geocoding fails
        """
        try:
            params = {
                'address': address,
                'key': self.api_key
            }
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'OK' and data['results']:
                result = data['results'][0]
                location = result['geometry']['location']
                
                return {
                    'latitude': location['lat'],
                    'longitude': location['lng'],
                    'formatted_address': result.get('formatted_address'),
                    'place_id': result.get('place_id'),
                }
            
            logger.warning(f"Geocoding failed for address: {address}. Status: {data['status']}")
            return None
            
        except Exception as e:
            logger.error(f"Geocoding error for address {address}: {str(e)}")
            return None

    def get_coordinates(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Simplified method to just get coordinates.
        """
        details = self.get_location_details(address)
        if details:
            return details['latitude'], details['longitude']
        return None
