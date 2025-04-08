import logging
import psycopg2
from flask import Blueprint, jsonify, current_app
from app.services.db_service import get_db_connection # Import from service

# Define blueprint
general_bp = Blueprint('general', __name__, url_prefix='/api/v1')

@general_bp.route('/health', methods=['GET'])
def health():
    """Checks database connectivity."""
    conn = None
    status = 'error'
    db_version = None
    try:
        # Use the db_service function to get connection
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT version()')
        db_version = cur.fetchone()
        cur.close()
        status = 'ok'
        logging.info("Health check successful.")
        return jsonify({'status': status, "database_version": db_version})
    except (psycopg2.Error, ValueError) as e: # Catch DB errors or config errors
        logging.error(f"Health check failed: {e}")
        # Ensure status remains 'error'
        return jsonify({'status': 'error', 'error': 'Service unavailable or database connection failed'}), 503 # 503 Service Unavailable
    except Exception as e:
        logging.error(f"Health check unexpected error: {e}")
        return jsonify({'status': 'error', 'error': 'An unexpected error occurred'}), 500
    finally:
        if conn:
            conn.close()

@general_bp.route('/test_connection', methods=['GET'])
def test_connection():
    """Simple endpoint to confirm backend is running."""
    logging.debug("Test connection endpoint called.")
    return jsonify({'message': 'Backend connection successful!'})