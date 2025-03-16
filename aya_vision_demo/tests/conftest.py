import os
import pytest
from app import create_app

@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    # Set the testing configuration
    os.environ['FLASK_CONFIG'] = 'testing'
    
    # Create the app with the testing configuration
    app = create_app()
    
    # Create a test client using the app
    with app.test_client() as client:
        # Establish an application context
        with app.app_context():
            yield client
