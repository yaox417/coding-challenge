"""Address validation utility using Google Maps API."""

import os
import googlemaps
from typing import Dict, Optional, Tuple
from loguru import logger


class AddressValidator:
    """Handles address validation using Google Maps API."""
    
    def __init__(self):
        """Initialize the Google Maps client."""
        api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_MAPS_API_KEY environment variable is required")
        
        self.gmaps = googlemaps.Client(key=api_key)
    
    def validate_address(self, address: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Validate an address using Google Maps Geocoding API.
        
        Args:
            address: The address string to validate
            
        Returns:
            Tuple of (is_valid, formatted_address_data, error_message)
        """
        try:
            # Use geocoding to validate the address
            geocode_result = self.gmaps.geocode(address)
            
            if not geocode_result:
                return False, None, "Address not found. Please provide a more specific address."
            
            # Get the first (best) result
            result = geocode_result[0]
            
            # Extract address components
            components = result.get('address_components', [])
            formatted_address = result.get('formatted_address', '')
            
            # Check if we have essential components
            has_street_number = any(
                'street_number' in comp.get('types', []) 
                for comp in components
            )
            has_route = any(
                'route' in comp.get('types', []) 
                for comp in components
            )
            has_locality = any(
                'locality' in comp.get('types', []) or 'administrative_area_level_1' in comp.get('types', [])
                for comp in components
            )
            
            # Determine validation quality
            geometry = result.get('geometry', {})
            location_type = geometry.get('location_type', '')
            
            # Consider address valid if it has basic components and good location accuracy
            is_precise = location_type in ['ROOFTOP', 'RANGE_INTERPOLATED']
            has_basic_components = has_route and has_locality
            
            if not has_basic_components:
                return False, None, "Please provide a complete address with street, city, and state."
            
            if not is_precise and not has_street_number:
                return False, {
                    'formatted_address': formatted_address,
                    'components': components,
                    'location_type': location_type
                }, "The address seems incomplete. Please provide the full street address including house number."
            
            # Address is valid
            address_data = {
                'formatted_address': formatted_address,
                'components': components,
                'location': geometry.get('location', {}),
                'location_type': location_type,
                'place_id': result.get('place_id', ''),
                'has_street_number': has_street_number,
                'has_route': has_route,
                'has_locality': has_locality
            }
            
            return True, address_data, None
            
        except googlemaps.exceptions.ApiError as e:
            logger.error(f"Google Maps API error: {e}")
            return False, None, "Unable to validate address due to service error. Please try again."
        except Exception as e:
            logger.error(f"Address validation error: {e}")
            return False, None, "Unable to validate address. Please try again."
    
    def get_address_suggestions(self, partial_address: str) -> list:
        """
        Get address suggestions for partial addresses using Places API.
        
        Args:
            partial_address: Partial address string
            
        Returns:
            List of suggested addresses
        """
        try:
            # Use places autocomplete for suggestions
            predictions = self.gmaps.places_autocomplete(
                input_text=partial_address,
                types=['address']
            )
            
            suggestions = []
            for prediction in predictions[:5]:  # Limit to 5 suggestions
                suggestions.append({
                    'description': prediction.get('description', ''),
                    'place_id': prediction.get('place_id', '')
                })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting address suggestions: {e}")
            return []
    
    def format_address_for_speech(self, address_data: Dict) -> str:
        """
        Format address data for speech output.
        
        Args:
            address_data: Address data from validation
            
        Returns:
            Speech-friendly address string
        """
        if not address_data:
            return ""
        
        formatted = address_data.get('formatted_address', '')
        
        # Make it more speech-friendly by adding pauses and clarifications
        # Replace commas with brief pauses
        speech_address = formatted.replace(',', ', ')
        
        return speech_address
