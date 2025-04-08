import os

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a_very_secret_key' # Add a secret key!
    DEBUG = False
    HOST = '0.0.0.0'
    PORT = 5000

    # Database configuration
    DATABASE_URL = os.environ.get('DATABASE_URL') or \
                   "postgresql://postgres@127.0.0.1:5432/postgres"

    # Application specific config
    UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'uploads')) # Path relative to project root
    ALLOWED_EXTENSIONS = {'pdf'}

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    # You might override DATABASE_URL here for dev if needed

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    # Ensure DATABASE_URL and SECRET_KEY are set via environment variables in production

# Dictionary to access config classes by name
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}