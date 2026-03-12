import sys
import os
import unittest
import json

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app

class APITestCase(unittest.TestCase):
    def setUp(self):
        """Set up test application client."""
        self.app = create_app()
        self.client = self.app.test_client()

    def test_search_api(self):
        """Test the city search API endpoint."""
        response = self.client.get('/api/search?q=delhi')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('results', data)
        self.assertIsInstance(data['results'], list)

    def test_cities_api(self):
        """Test the cities list API endpoint."""
        response = self.client.get('/api/cities')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('cities', data)
        self.assertIn('total', data)

    def test_states_api(self):
        """Test the states list API endpoint."""
        response = self.client.get('/api/states')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(isinstance(data, dict))

    def test_map_data_api(self):
        """Test the map data API endpoint."""
        response = self.client.get('/api/map-data')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('cities', data)

    def test_top_cities_api(self):
        """Test the top polluted cities API endpoint."""
        response = self.client.get('/api/top-cities')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('cities', data)

    def test_aqi_city_api(self):
        """Test a specific city AQI endpoint."""
        response = self.client.get('/api/aqi/delhi-aqi')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('aqi', data)
        self.assertIn('city', data)

    def test_aqi_invalid_city(self):
        """Test AQI endpoint with invalid city."""
        response = self.client.get('/api/aqi/invalid-fake-city-name')
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
