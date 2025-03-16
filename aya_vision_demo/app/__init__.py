import logging
import os
from flask import Flask
from config import get_config

def create_app(config_name=None):
    """
    Create and configure the Flask application.
    
    Args:
        config_name: The name of the configuration to use
        
    Returns:
        Flask: The configured Flask application
    """
    # Create the Flask app
    app = Flask(__name__)
    
    # Load configuration
    config_obj = get_config()
    app.config.from_object(config_obj)
    
    # Configure logging
    log_level = getattr(logging, app.config['LOG_LEVEL'])
    logging.basicConfig(level=log_level)
    app.logger.setLevel(log_level)
    
    # Check for required configuration
    if not app.config.get('COHERE_API_KEY'):
        app.logger.warning("COHERE_API_KEY is not set. API calls will fail.")
    
    # Register blueprints
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    # Register error handlers
    register_error_handlers(app)
    
    return app

def register_error_handlers(app):
    """Register error handlers for the application."""
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors."""
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        app.logger.error(f"Internal server error: {error}")
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        """Handle 413 errors (request entity too large)."""
        app.logger.warning(f"Request entity too large: {error}")
        return render_template('errors/413.html', error=error), 413

# Import at the bottom to avoid circular imports
from flask import render_template
