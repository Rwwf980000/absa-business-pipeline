# Tests

Unit tests for all ABSA pipeline services.

## Structure

```
tests/
├── test_collector.py       # Google Maps collector tests
├── test_enricher.py        # Gemini enricher tests
├── test_orchestrator.py    # Orchestrator tests
├── requirements.txt        # Test dependencies
└── README.md              # This file
```

## Setup

```bash
cd tests

# Install test dependencies
pip install -r requirements.txt
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Service Tests

```bash
# Collector tests
pytest test_collector.py

# Enricher tests
pytest test_enricher.py

# Orchestrator tests
pytest test_orchestrator.py
```

### Run with Verbose Output

```bash
pytest -v
```

### Run with Coverage

```bash
pytest --cov=../services --cov-report=html
```

This generates an HTML coverage report in `htmlcov/index.html`

### Run Specific Test

```bash
pytest test_enricher.py::TestGeminiEnricher::test_enricher_success -v
```

## Test Coverage

### test_collector.py
- Text cleaning (newlines, None, empty)
- Successful collection
- No results handling
- CORS headers
- Error handling

### test_enricher.py
- Successful enrichment
- Missing input validation
- API error handling
- JSON markdown cleaning
- CORS headers
- Aspect validation

### test_orchestrator.py
- Arabic text normalization
- Review ID generation (consistency, uniqueness)
- Gemini API calls
- Timeout handling
- BigQuery operations
- CORS headers
- Empty data handling

## Continuous Integration

Add to your CI/CD pipeline:

```yaml
# .github/workflows/tests.yml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          cd tests
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd tests
          pytest --cov=../services --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Writing New Tests

### Template

```python
"""
Tests for [Service Name]
"""
import pytest
from unittest.mock import Mock, patch

class Test[ServiceName]:
    """Test suite for [service]"""
    
    def test_[feature](self):
        """Test [specific feature]"""
        # Arrange
        ...
        
        # Act
        result = function_under_test(...)
        
        # Assert
        assert result == expected
```

### Best Practices

1. **Use descriptive test names** - `test_enricher_handles_api_error` not `test_1`
2. **Mock external services** - Don't call real APIs in tests
3. **Test edge cases** - None, empty, invalid inputs
4. **Test error handling** - What happens when things go wrong?
5. **Keep tests isolated** - Each test should be independent
6. **Use fixtures** - DRY principle for test setup

## Mock Examples

### Mocking HTTP Requests

```python
@patch('main.requests.post')
def test_api_call(self, mock_post):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {...}
    mock_post.return_value = mock_response
```

### Mocking Google Cloud Services

```python
@patch('main.storage.Client')
def test_storage(self, mock_storage):
    mock_client = MagicMock()
    mock_storage.return_value = mock_client
```

### Mocking Flask Request

```python
def test_endpoint(self):
    mock_request = Mock()
    mock_request.method = 'POST'
    mock_request.get_json.return_value = {...}
```

## Environment Variables for Tests

Create a `.env.test` file:

```bash
GOOGLE_MAPS_API_KEY=test_key
GEMINI_API_KEY=test_key
PROJECT_ID=test-project
BUCKET_NAME=test-bucket
```

Load in tests:

```python
from dotenv import load_dotenv
load_dotenv('.env.test')
```

## Troubleshooting

### Import Errors

Make sure service paths are added:

```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'SERVICE_NAME'))
```

### Mock Not Working

Check you're patching the right import path:

```python
# Wrong: @patch('requests.post')
# Right: @patch('main.requests.post')
```

### Tests Pass Locally but Fail in CI

- Check Python version compatibility
- Verify all dependencies in requirements.txt
- Check for environment-specific assumptions

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [unittest.mock guide](https://docs.python.org/3/library/unittest.mock.html)
- [Coverage.py](https://coverage.readthedocs.io/)
