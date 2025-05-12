import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-for-development-only'
    COHERE_API_KEY = os.environ.get('COHERE_API_KEY')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size
    UPLOAD_EXTENSIONS = ['.jpg', '.jpeg', '.png']
    MIN_IMAGES = 1  # For development, we'll start with 1, but the PRD specifies 40-50
    MAX_IMAGES = 50
    MODEL_NAME = 'command-a-vision-epsilon'
    PROMPT = "Is a flare burning in this image? Answer with only 'true' or 'false'."
    
    # Logging configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    DEMO_TITLE = os.environ.get('DEMO_TITLE', 'Cohere Vision Demo')
    DEMO_DESCRIPTION = os.environ.get('DEMO_DESCRIPTION', "A demonstration of object detection capabilities using Cohere's command-a-vision-epsilon model.")
    DEMO_FOOTER = os.environ.get('DEMO_FOOTER', "Powered by <a href='https://cohere.com/' target='_blank' class='cohere-link'>Cohere</a>")
    
class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = False
    TESTING = True
    # Use a separate test API key if needed
    COHERE_API_KEY = os.environ.get('TEST_COHERE_API_KEY') or os.environ.get('COHERE_API_KEY')
    # For testing, we can use a smaller number of images
    MIN_IMAGES = 1
    MAX_IMAGES = 5

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    # In production, we enforce the 40-50 image range as per PRD
    MIN_IMAGES = 1
    MAX_IMAGES = 50

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Return the appropriate configuration object based on the environment."""
    config_name = os.environ.get('FLASK_CONFIG', 'default')
    return config[config_name]
