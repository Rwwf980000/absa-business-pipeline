"""
Tests for ABSA Gemini Enricher
"""
import pytest
import json
from unittest.mock import Mock, patch
import sys
import os

# Add service to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'absa-gemini-enricher'))


class TestGeminiEnricher:
    """Test suite for Gemini enricher"""
    
    @patch('main.requests.post')
    def test_enricher_success(self, mock_post):
        """Test successful enrichment"""
        from main import gemini_absa_enricher
        
        # Mock Gemini API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'candidates': [{
                'content': {
                    'parts': [{
                        'text': '[{"aspect": "النظافة", "polarity": "إيجابي"}]'
                    }]
                }
            }]
        }
        mock_post.return_value = mock_response
        
        # Create mock request
        mock_request = Mock()
        mock_request.method = 'POST'
        mock_request.get_json.return_value = {
            'normalized_text': 'المكان نظيف'
        }
        
        # Call function
        response, status_code, headers = gemini_absa_enricher(mock_request)
        
        # Verify
        assert status_code == 200
        result = json.loads(response)
        assert isinstance(result, list)
        assert len(result) > 0
        assert 'aspect' in result[0]
        assert 'polarity' in result[0]
    
    def test_enricher_missing_text(self):
        """Test enricher with missing normalized_text"""
        from main import gemini_absa_enricher
        
        mock_request = Mock()
        mock_request.method = 'POST'
        mock_request.get_json.return_value = {}
        
        response, status_code = gemini_absa_enricher(mock_request)
        
        assert status_code == 400
        result = json.loads(response)
        assert 'error' in result
    
    @patch('main.requests.post')
    def test_enricher_handles_api_error(self, mock_post):
        """Test enricher handles API errors gracefully"""
        from main import gemini_absa_enricher
        
        # Mock API error
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_post.return_value = mock_response
        
        mock_request = Mock()
        mock_request.method = 'POST'
        mock_request.get_json.return_value = {
            'normalized_text': 'test text'
        }
        
        response, status_code = gemini_absa_enricher(mock_request)
        
        # Should return system error
        assert status_code == 200  # Still returns 200 with error in body
        result = json.loads(response)
        assert result[0]['aspect'] == 'System'
    
    @patch('main.requests.post')
    def test_enricher_cleans_json_markdown(self, mock_post):
        """Test enricher strips markdown code blocks"""
        from main import gemini_absa_enricher
        
        # Mock response with markdown
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'candidates': [{
                'content': {
                    'parts': [{
                        'text': '```json\n[{"aspect": "النظافة", "polarity": "إيجابي"}]\n```'
                    }]
                }
            }]
        }
        mock_post.return_value = mock_response
        
        mock_request = Mock()
        mock_request.method = 'POST'
        mock_request.get_json.return_value = {'normalized_text': 'test'}
        
        response, status_code, _ = gemini_absa_enricher(mock_request)
        
        # Should parse successfully despite markdown
        result = json.loads(response)
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_options_request_cors(self):
        """Test OPTIONS request returns CORS headers"""
        from main import gemini_absa_enricher
        
        mock_request = Mock()
        mock_request.method = 'OPTIONS'
        
        _, status_code, headers = gemini_absa_enricher(mock_request)
        
        assert status_code == 204
        assert headers['Access-Control-Allow-Origin'] == '*'
    
    @patch('main.requests.post')
    def test_enricher_validates_aspects(self, mock_post):
        """Test enricher validates aspect structure"""
        from main import gemini_absa_enricher
        
        # Mock response with invalid structure
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'candidates': [{
                'content': {
                    'parts': [{
                        'text': '[{"invalid": "structure"}]'
                    }]
                }
            }]
        }
        mock_post.return_value = mock_response
        
        mock_request = Mock()
        mock_request.method = 'POST'
        mock_request.get_json.return_value = {'normalized_text': 'test'}
        
        response, status_code, _ = gemini_absa_enricher(mock_request)
        
        result = json.loads(response)
        # Should return NO_VALID_ASPECTS error
        assert result[0]['polarity'] == 'NO_VALID_ASPECTS'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
