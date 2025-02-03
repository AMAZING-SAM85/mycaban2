# properties/tests/test_geocoding.py
from unittest.mock import patch, Mock
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from properties.utils import GeocodingService
from properties.models import Property
from properties.serializers import PropertySerializer

User = get_user_model()

class GeocodingServiceTests(TestCase):
    def setUp(self):
        self.geocoding_service = GeocodingService()
        self.test_address = "123 Main St, New York, NY 10001"
        self.mock_coordinates = (40.7505, -73.9934)

    @patch('properties.utils.requests.get')
    def test_successful_geocoding(self, mock_get):
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'OK',
            'results': [{
                'geometry': {
                    'location': {
                        'lat': self.mock_coordinates[0],
                        'lng': self.mock_coordinates[1]
                    }
                }
            }]
        }
        mock_get.return_value = mock_response

        coordinates = self.geocoding_service.get_coordinates(self.test_address)
        
        self.assertEqual(coordinates, self.mock_coordinates)
        mock_get.assert_called_once()

    @patch('properties.utils.requests.get')
    def test_failed_geocoding(self, mock_get):
        # Mock failed API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'ZERO_RESULTS',
            'results': []
        }
        mock_get.return_value = mock_response

        coordinates = self.geocoding_service.get_coordinates(self.test_address)
        
        self.assertIsNone(coordinates)

    @patch('properties.utils.requests.get')
    def test_api_error_handling(self, mock_get):
        # Mock API error
        mock_get.side_effect = Exception("API Error")

        coordinates = self.geocoding_service.get_coordinates(self.test_address)
        
        self.assertIsNone(coordinates)

class PropertySerializerTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.property_data = {
            'title': 'Test Property',
            'description': 'A test property',
            'property_type': 'HOUSE',
            'listing_type': 'SALE',
            'price': 250000,
            'size': 150,
            'location': '123 Main St, New York, NY 10001',
            'owner': self.user.id
        }
        self.mock_coordinates = (40.7505, -73.9934)

    @patch('properties.utils.GeocodingService.get_coordinates')
    def test_create_property_with_coordinates(self, mock_get_coordinates):
        # Mock successful geocoding
        mock_get_coordinates.return_value = self.mock_coordinates

        serializer = PropertySerializer(data=self.property_data)
        self.assertTrue(serializer.is_valid())
        
        property_instance = serializer.save(owner=self.user)
        
        self.assertEqual(float(property_instance.latitude), self.mock_coordinates[0])
        self.assertEqual(float(property_instance.longitude), self.mock_coordinates[1])
        mock_get_coordinates.assert_called_once_with(self.property_data['location'])

    @patch('properties.utils.GeocodingService.get_coordinates')
    def test_create_property_without_coordinates(self, mock_get_coordinates):
        # Mock failed geocoding
        mock_get_coordinates.return_value = None

        serializer = PropertySerializer(data=self.property_data)
        self.assertTrue(serializer.is_valid())
        
        property_instance = serializer.save(owner=self.user)
        
        self.assertIsNone(property_instance.latitude)
        self.assertIsNone(property_instance.longitude)
        mock_get_coordinates.assert_called_once_with(self.property_data['location'])

    @patch('properties.utils.GeocodingService.get_coordinates')
    def test_update_property_location(self, mock_get_coordinates):
        # Create initial property
        mock_get_coordinates.return_value = self.mock_coordinates
        property_instance = Property.objects.create(
            owner=self.user,
            **self.property_data
        )

        # Update location
        new_location = "456 Park Ave, New York, NY 10022"
        new_coordinates = (40.7605, -73.9724)
        mock_get_coordinates.return_value = new_coordinates
        
        serializer = PropertySerializer(
            property_instance,
            data={'location': new_location},
            partial=True
        )
        self.assertTrue(serializer.is_valid())
        updated_property = serializer.save()

        self.assertEqual(updated_property.location, new_location)
        self.assertEqual(float(updated_property.latitude), new_coordinates[0])
        self.assertEqual(float(updated_property.longitude), new_coordinates[1])

    def test_location_details_format(self):
        property_instance = Property.objects.create(
            owner=self.user,
            latitude=self.mock_coordinates[0],
            longitude=self.mock_coordinates[1],
            **self.property_data
        )

        serializer = PropertySerializer(property_instance)
        location_details = serializer.data['location_details']

        self.assertEqual(location_details['address'], self.property_data['location'])
        self.assertEqual(
            location_details['coordinates'],
            {'lat': self.mock_coordinates[0], 'lng': self.mock_coordinates[1]}
        )