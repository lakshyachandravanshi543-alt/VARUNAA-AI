import unittest
import json
from app import app, CLASSES

class VarunaAITestCase(unittest.TestCase):
    def setUp(self):
        # Configure application for testing
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_index_route(self):
        """Test that the index route returns HTTP 200 and loads HTML."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Varuna', response.data)
        self.assertIn(b'River Directory', response.data)

    def test_remediation_route(self):
        """Test that the remediation route returns HTTP 200 and loads HTML."""
        response = self.client.get('/remediation')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Remediation Action Plan', response.data)

    def test_network_state_endpoint(self):
        """Test that the network_state API returns river lists with correct structure."""
        response = self.client.get('/api/network_state')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        
        # Verify first item contains expected keys
        first_river = data[0]
        self.assertIn('id', first_river)
        self.assertIn('name', first_river)
        self.assertIn('raw_sensors', first_river)
        self.assertIn('prediction', first_river)
        
        # Verify specific rivers exist
        river_names = [river['name'] for river in data]
        self.assertIn('Nile River, Egypt', river_names)
        self.assertIn('Rhine River, Europe', river_names)
        self.assertIn('Thames River, UK', river_names)

    def test_predict_endpoint_valid(self):
        """Test /api/predict with standard parameters returns correct format."""
        payload = {
            "ph": 7.2,
            "do": 8.0,
            "turbidity": 5.0,
            "temperature": 22.0
        }
        response = self.client.post(
            '/api/predict',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('pollutant', data)
        self.assertIn('chemical_definition', data)
        self.assertIn('action', data)

    def test_predict_endpoint_invalid(self):
        """Test /api/predict handles invalid/malformed parameters gracefully."""
        payload = {
            "ph": "invalid_ph",
            "do": 8.0
        }
        response = self.client.post(
            '/api/predict',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)

if __name__ == '__main__':
    unittest.main()
