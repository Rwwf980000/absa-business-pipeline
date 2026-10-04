"""
Tests for Google Maps Multi-Branch Collector
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add service to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'gmaps-multi-collector'))

class TestGmapsCollector:
    """Test suite for gmaps collector"""
    
    def test_clean_text_removes_newlines(self):
        """Test that clean_text removes newlines"""
        from main import clean_text
        
        text = "Line 1\nLine 2\nLine 3"
        result = clean_text(text)
        assert '\n' not in result
        assert result == "Line 1 Line 2 Line 3"
    
    def test_clean_text_handles_none(self):
        """Test clean_text with None input"""
        from main import clean_text
        
        assert clean_text(None) is None
    
    def test_clean_text_handles_empty_string(self):
        """Test clean_text with empty string"""
        from main import clean_text
        
        assert clean_text("") == ""
    
    @patch('main.googlemaps.Client')
    @patch('main.storage.Client')
    def test_collector_success(self, mock_storage, mock_gmaps):
        """Test successful collection"""
        from main import gmaps_multi_collector
        
        # Mock Google Maps API
        mock_gmaps_instance = MagicMock()
        mock_gmaps.return_value = mock_gmaps_instance
        
        # Mock places search
        mock_gmaps_instance.places.return_value = {
            'results': [{
                'place_id': 'test_place_id',
                'name': 'Test Gym'
            }]
        }
        
        # Mock place details
        mock_gmaps_instance.place.return_value = {
            'result': {
                'name': 'Test Gym',
                'formatted_address': '123 Test St',
                'rating': 4.5,
                'user_ratings_total': 100,
                'reviews': [{
                    'author_name': 'Test User',
                    'rating': 5,
                    'text': 'Great gym!',
                    'time': 1234567890,
                    'relative_time_description': '1 month ago'
                }]
            }
        }
        
        # Mock Cloud Storage
        mock_storage_instance = MagicMock()
        mock_storage.return_value = mock_storage_instance
        mock_bucket = MagicMock()
        mock_storage_instance.bucket.return_value = mock_bucket
        
        # Create mock request
        mock_request = Mock()
        mock_request.method = 'GET'
        
        # Call function
        response, status_code = gmaps_multi_collector(mock_request)
        
        # Verify
        assert status_code == 200
        result = json.loads(response)
        assert result['status'] == 'success'
        assert result['reviews_collected'] > 0
    
    @patch('main.googlemaps.Client')
    def test_collector_handles_no_results(self, mock_gmaps):
        """Test collector handles branches with no results"""
        from main import gmaps_multi_collector
        
        # Mock Google Maps to return no results
        mock_gmaps_instance = MagicMock()
        mock_gmaps.return_value = mock_gmaps_instance
        mock_gmaps_instance.places.return_value = {'results': []}
        
        # Create mock request
        mock_request = Mock()
        mock_request.method = 'GET'
        
        # Call function
        response, status_code = gmaps_multi_collector(mock_request)
        
        # Should still return success with 0 reviews
        result = json.loads(response)
        assert result['status'] == 'success'
        assert result['reviews_collected'] == 0
    
    def test_options_request_returns_cors(self):
        """Test OPTIONS request returns CORS headers"""
        from main import gmaps_multi_collector
        
        mock_request = Mock()
        mock_request.method = 'OPTIONS'
        
        response, status_code, headers = gmaps_multi_collector(mock_request)
        
        assert status_code == 204
        assert headers['Access-Control-Allow-Origin'] == '*'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
