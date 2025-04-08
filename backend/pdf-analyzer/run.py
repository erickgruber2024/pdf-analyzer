import os
from app import create_app

# Load environment variables if using a .env file (optional)
# from dotenv import load_dotenv
# load_dotenv()

# Create the Flask app instance using the factory
app = create_app(os.getenv('FLASK_CONFIG') or 'default')

if __name__ == '__main__':
    # Get host and port from config, default to 0.0.0.0:5000
    # Get debug flag from config (important for production!)
    host = app.config.get('HOST', '0.0.0.0')
    port = app.config.get('PORT', 5000)
    debug = app.config.get('DEBUG', True) # Default to True for dev, should be False in prod
    app.run(host=host, port=port, debug=debug)