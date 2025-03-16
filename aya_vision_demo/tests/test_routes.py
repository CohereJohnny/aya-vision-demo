import io
import pytest
from PIL import Image

def test_index_route(app):
    """Test the index route."""
    response = app.get('/')
    assert response.status_code == 200
    assert b'Upload Images for Flare Detection' in response.data

def test_results_route_redirect(app):
    """Test that the results route redirects to index when no results are available."""
    response = app.get('/results', follow_redirects=True)
    assert response.status_code == 200
    assert b'Upload Images for Flare Detection' in response.data

def test_api_analyze_no_files(app):
    """Test the API analyze endpoint with no files."""
    response = app.post('/api/analyze')
    assert response.status_code == 400
    assert b'No files uploaded' in response.data

def test_api_analyze_invalid_extension(app):
    """Test the API analyze endpoint with an invalid file extension."""
    # Create a text file
    data = {'images': (io.BytesIO(b'This is not an image'), 'test.txt')}
    response = app.post('/api/analyze', data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    assert b'invalid extension' in response.data
