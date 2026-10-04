"""
Tests for ABSA Orchestrator
"""
import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add service to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'absa-orchestrator'))


class TestOrchestrator:
    """Test suite for orchestrator"""
    
    def test_normalize_arabic(self):
        """Test Arabic text normalization"""
        from main import normalize_arabic
        
        # Test hamza normalization
        text = "إأآا"
        result = normalize_arabic(text)
        assert result == "اااا"
        
        # Test ya normalization
        text = "ىي"
        result = normalize_arabic(text)
        assert result == "يي"
        
        # Test ta marbuta normalization
        text = "ة"
        result = normalize_arabic(text)
        assert result == "ه"
    
    def test_normalize_arabic_handles_none(self):
        """Test normalize_arabic with None"""
        from main import normalize_arabic
        
        assert normalize_arabic(None) == ""
    
    def test_create_review_id(self):
        """Test review ID generation"""
        from main import create_review_id
        
        # Create test row
        row = pd.Series({
            'data_source': 'gmaps',
            'raw_review': 'Test review',
            'author_name': 'Test User',
            'time': '1234567890'
        })
        
        review_id = create_review_id(row)
        
        # Should be MD5 hash (32 chars)
        assert len(review_id) == 32
        assert isinstance(review_id, str)
    
    def test_create_review_id_consistent(self):
        """Test review ID is consistent for same data"""
        from main import create_review_id
        
        row = pd.Series({
            'data_source': 'gmaps',
            'raw_review': 'Test review',
            'author_name': 'Test User',
            'time': '1234567890'
        })
        
        id1 = create_review_id(row)
        id2 = create_review_id(row)
        
        assert id1 == id2
    
    def test_create_review_id_unique(self):
        """Test different reviews get different IDs"""
        from main import create_review_id
        
        row1 = pd.Series({
            'data_source': 'gmaps',
            'raw_review': 'Review 1',
            'author_name': 'User 1',
            'time': '1'
        })
        
        row2 = pd.Series({
            'data_source': 'gmaps',
            'raw_review': 'Review 2',
            'author_name': 'User 2',
            'time': '2'
        })
        
        id1 = create_review_id(row1)
        id2 = create_review_id(row2)
        
        assert id1 != id2
    
    @patch('main.requests.post')
    def test_call_gemini_api_single(self, mock_post):
        """Test single Gemini API call"""
        from main import call_gemini_api_single
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '[{"aspect": "النظافة", "polarity": "إيجابي"}]'
        mock_post.return_value = mock_response
        
        index, result = call_gemini_api_single("test text", 0)
        
        assert index == 0
        assert isinstance(result, str)
    
    @patch('main.requests.post')
    def test_call_gemini_api_timeout(self, mock_post):
        """Test Gemini API timeout handling"""
        from main import call_gemini_api_single
        import requests
        
        # Mock timeout
        mock_post.side_effect = requests.exceptions.Timeout()
        
        index, result = call_gemini_api_single("test text", 0)
        
        assert "TIMEOUT" in result
    
    @patch('main.bigquery.Client')
    def test_get_processed_review_ids(self, mock_bq):
        """Test getting processed review IDs"""
        from main import get_processed_review_ids
        
        # Mock BigQuery response
        mock_client = MagicMock()
        mock_result = [
            Mock(review_id='id1'),
            Mock(review_id='id2'),
            Mock(review_id='id3')
        ]
        mock_client.query.return_value.result.return_value = mock_result
        
        result = get_processed_review_ids(mock_client, 'project', 'dataset', 'table')
        
        assert isinstance(result, set)
        assert len(result) == 3
        assert 'id1' in result
    
    @patch('main.bigquery.Client')
    def test_get_processed_review_ids_error(self, mock_bq):
        """Test get_processed_review_ids handles errors"""
        from main import get_processed_review_ids
        
        # Mock error
        mock_client = MagicMock()
        mock_client.query.side_effect = Exception("DB error")
        
        result = get_processed_review_ids(mock_client, 'project', 'dataset', 'table')
        
        # Should return empty set on error
        assert isinstance(result, set)
        assert len(result) == 0
    
    def test_options_request(self):
        """Test OPTIONS request"""
        from main import absa_orchestrator
        
        mock_request = Mock()
        mock_request.method = 'OPTIONS'
        
        _, status_code, headers = absa_orchestrator(mock_request)
        
        assert status_code == 204
        assert headers['Access-Control-Allow-Origin'] == '*'
    
    @patch('main.storage.Client')
    @patch('main.bigquery.Client')
    def test_orchestrator_no_new_data(self, mock_bq, mock_storage):
        """Test orchestrator with no new data"""
        from main import absa_orchestrator
        
        # Mock empty bucket
        mock_storage_instance = MagicMock()
        mock_storage.return_value = mock_storage_instance
        mock_bucket = MagicMock()
        mock_storage_instance.bucket.return_value = mock_bucket
        mock_bucket.list_blobs.return_value = []
        
        # Mock BigQuery
        mock_bq_instance = MagicMock()
        mock_bq.return_value = mock_bq_instance
        
        mock_request = Mock()
        mock_request.method = 'GET'
        mock_request.args.get.return_value = 'all'
        
        response, status_code = absa_orchestrator(mock_request)
        
        result = json.loads(response)
        assert result['status'] == 'success'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
