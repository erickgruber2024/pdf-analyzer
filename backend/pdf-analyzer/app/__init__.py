import os
import logging
from flask import Flask
from flask_cors import CORS
from .config import config # Import the config dictionary

# Import blueprints
from .routes.general_routes import general_bp
from .routes.pdf_routes import pdf_bp

def create_app(config_name='default'):
    """Application factory function."""
    app = Flask(__name__)

    # Load configuration from config.py based on config_name
    app.config.from_object(config[config_name])

    # Initialize extensions
    CORS(app) # Enable CORS

    # Configure logging
    logging.basicConfig(level=logging.INFO if not app.config['DEBUG'] else logging.DEBUG)

    # Ensure upload folder exists
    try:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        logging.info(f"Upload folder checked/created: {app.config['UPLOAD_FOLDER']}")
    except OSError as e:
        logging.error(f"Error creating upload folder {app.config['UPLOAD_FOLDER']}: {e}")
        # Handle error appropriately - maybe raise it?

    # Register Blueprints
    app.register_blueprint(general_bp)
    app.register_blueprint(pdf_bp)

    logging.info(f"Flask App created with config: {config_name}")
    return app