import sys
import os
import unittest
import json

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app

class ChatbotTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test application client."""
        self.app = create_app()
        self.client = self.app.test_client()

    def test_chat_empty_message(self):
        """Test chatbot with empty message."""
        payload = {}
        response = self.client.post(
            '/api/chat',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_chat_valid_message(self):
        """Test chatbot with a standard valid message."""
        payload = {
            "message": "What is the AQI?",
            "context": {
                "city": "TestCity",
                "aqi": 100,
                "category": "Satisfactory"
            }
        }
        response = self.client.post(
            '/api/chat',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Check that it returns either 200 ok (or potentially the "maintenance" message if models aren't loaded locally)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('response', data)
        self.assertIn('tag', data)

if __name__ == '__main__':
    unittest.main()
