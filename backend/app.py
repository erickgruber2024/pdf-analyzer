import os
import re
import psycopg2
import logging
import csv  # Added for CSV export
import io   # Added for CSV export (in-memory stream)
from flask import Flask, jsonify, request, make_response # Added make_response for custom headers
from flask_cors import CORS
from werkzeug.utils import secure_filename
import pdfminer.high_level # type: ignore

# --- Flask App Initialization ---
app = Flask(__name__)
CORS(app) # Enable Cross-Origin Resource Sharing

# --- Configuration ---
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
# Configure logging
logging.basicConfig(level=logging.INFO)

# --- Ensure Upload Folder Exists ---
if not os.path.exists(UPLOAD_FOLDER):
    try:
        os.makedirs(UPLOAD_FOLDER)
        logging.info(f"Created upload folder: {UPLOAD_FOLDER}")
    except OSError as e:
        logging.error(f"Error creating upload folder {UPLOAD_FOLDER}: {e}")
        exit(1)

# --- Custom Exception for Not Found ---
class NotFoundError(Exception):
    """Custom exception for cases where PDF or analysis is not found."""
    pass

# --- Database Connection ---
def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    conn = None
    try:
        conn_str = os.environ.get('DATABASE_URL')
        if not conn_str:
            conn_str = "postgresql://postgres@127.0.0.1:5432/postgres"
            logging.warning("DATABASE_URL environment variable not set. Using default local connection.")
        conn = psycopg2.connect(conn_str)
        return conn
    except psycopg2.Error as e:
        logging.error(f"Error connecting to database: {e}")
        raise # Propagate the error

# --- Utility Functions ---
def allowed_file(filename):
    """Checks if the filename has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(pdf_path):
    """Extracts text content from a PDF file using pdfminer."""
    try:
        text = pdfminer.high_level.extract_text(pdf_path)
        return text
    except Exception as e:
        logging.error(f"Error extracting text from {pdf_path}: {e}")
        return ""

def extract_components(text):
    """Extracts predefined components from text using regex."""
    component_patterns = [
        r"spindle\s*([a-zA-Z0-9\-\s]+)",
        r"motor\s*([a-zA-Z0-9\-\s]+)",
        r"axis\s*([a-zA-Z0-9\-\s]+)",
        r"controller\s*([a-zA-Z0-9\-\s]+)",
        r"tool changer\s*([a-zA-Z0-9\-\s]+)",
    ]
    components = []
    for pattern in component_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        components.extend([match.strip() for match in matches])
    return list(set(components))

# --- Helper Function for Data Retrieval ---
def _get_analysis_data(pdf_id: int):
    """
    Helper function to retrieve filename and component analysis results for a PDF ID.
    Raises NotFoundError if the PDF doesn't exist.
    Returns tuple (pdf_filename, components_list).
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # 1. Get PDF filename
        cur.execute('SELECT filename FROM pdfs WHERE id = %s', (pdf_id,))
        pdf_record = cur.fetchone()
        if pdf_record is None:
            raise NotFoundError(f"PDF with id {pdf_id} not found")
        pdf_filename = pdf_record[0]
        logging.info(f"Fetching analysis data for PDF ID: {pdf_id} (File: {pdf_filename})")

        # 2. Get associated components (assuming 'component_extraction' type)
        # Consider making analysis_type dynamic if you add more types later
        analysis_type = 'component_extraction'
        cur.execute(
            """
            SELECT ed.data_value
            FROM extracted_data ed
            JOIN pdf_analyses pa ON ed.analysis_id = pa.id
            WHERE pa.pdf_id = %s
              AND pa.analysis_type = %s
              AND ed.data_key = %s
            ORDER BY ed.id ASC -- Order by insertion order or data_value
            """,
            (pdf_id, analysis_type, 'component_name')
        )
        results = cur.fetchall()
        components = [row[0] for row in results]
        logging.info(f"Found {len(components)} components in database for PDF ID {pdf_id}")

        cur.close()
        return pdf_filename, components, analysis_type # Return type as well

    except psycopg2.Error as db_err:
        logging.error(f"Database error fetching data for PDF ID {pdf_id}: {db_err}")
        raise # Re-raise database errors to be handled by the route
    finally:
        if conn:
            conn.close()

# --- API Endpoints ---

@app.route('/api/v1/health', methods=['GET'])
def health():
    # (Health check code remains the same as before)
    conn = None
    db_version = None
    status = 'error'
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT version()')
        db_version = cur.fetchone()
        cur.close()
        status = 'ok'
        return jsonify({'status': status, "database_version": db_version})
    except psycopg2.Error as e:
        logging.error(f"Health check database error: {e}")
        return jsonify({'status': status, 'error': 'Database connection failed'}), 500
    except Exception as e:
        logging.error(f"Health check unexpected error: {e}")
        return jsonify({'status': status, 'error': 'An unexpected error occurred'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/v1/test_connection', methods=['GET'])
def test_connection():
    # (Test connection code remains the same)
    return jsonify({'message': 'Backend connection successful!'})

@app.route('/api/v1/upload_pdf', methods=['POST'])
def upload_pdf():
    # (Upload PDF code remains the same)
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        conn = None
        try:
            file.save(filepath)
            logging.info(f"File saved successfully: {filepath}")
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('INSERT INTO pdfs (filename) VALUES (%s) RETURNING id', (filename,))
            pdf_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            logging.info(f"PDF record created in database with ID: {pdf_id}")
            return jsonify({'message': 'PDF uploaded successfully', 'pdf_id': pdf_id}), 201
        except psycopg2.Error as e:
            logging.error(f"Database error during PDF upload for {filename}: {e}")
            return jsonify({'error': 'Database error during upload'}), 500
        except Exception as e:
            logging.error(f"Error saving file {filename}: {e}")
            return jsonify({'error': f'Failed to save file: {e}'}), 500
        finally:
            if conn:
                conn.close()
    else:
        return jsonify({'error': 'Invalid file type. Only PDF allowed.'}), 400


@app.route('/api/v1/analyze_pdf/<int:pdf_id>', methods=['POST'])
def analyze_pdf(pdf_id):
    # (Analyze PDF code remains the same)
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT filename FROM pdfs WHERE id = %s', (pdf_id,))
        pdf_record = cur.fetchone()
        if pdf_record is None:
            logging.warning(f"Analysis requested for non-existent PDF ID: {pdf_id}")
            return jsonify({'error': f'PDF with id {pdf_id} not found'}), 404
        pdf_filename = pdf_record[0]
        pdf_path = os.path.join(UPLOAD_FOLDER, pdf_filename)
        if not os.path.exists(pdf_path):
             logging.error(f"File not found on disk for PDF ID {pdf_id}: {pdf_path}")
             return jsonify({'error': 'PDF file not found on server'}), 404
        logging.info(f"Starting text extraction for: {pdf_path}")
        extracted_text = extract_text_from_pdf(pdf_path)
        if not extracted_text:
            logging.warning(f"No text extracted from PDF ID {pdf_id}: {pdf_path}")
        logging.info(f"Starting component extraction for PDF ID: {pdf_id}")
        components = extract_components(extracted_text)
        logging.info(f"Found {len(components)} components for PDF ID {pdf_id}: {components}")
        cur.execute(
             'INSERT INTO pdf_analyses (pdf_id, analysis_type) VALUES (%s, %s) RETURNING id',
             (pdf_id, 'component_extraction'),
        )
        analysis_id = cur.fetchone()[0]
        logging.info(f"Created analysis record ID {analysis_id} for PDF ID {pdf_id}")
        if components:
            component_data = [(analysis_id, 'component_name', comp) for comp in components]
            cur.executemany(
                'INSERT INTO extracted_data (analysis_id, data_key, data_value) VALUES (%s, %s, %s)',
                component_data
            )
            logging.info(f"Inserted {len(components)} components into extracted_data for analysis ID {analysis_id}")
        else:
            logging.info(f"No components to insert for analysis ID {analysis_id}")
        conn.commit()
        cur.close()
        return jsonify({'message': f'Analysis complete for PDF ID {pdf_id}', 'analysis_id': analysis_id, 'components_found': len(components)})
    except psycopg2.Error as e:
        logging.error(f"Database error during analysis for PDF ID {pdf_id}: {e}")
        if conn: conn.rollback()
        return jsonify({'error': 'Database error during analysis'}), 500
    except FileNotFoundError:
         logging.error(f"File vanished during analysis for PDF ID {pdf_id}: {pdf_path}")
         return jsonify({'error': 'PDF file disappeared during analysis'}), 500
    except Exception as e:
        logging.error(f"Unexpected error during analysis for PDF ID {pdf_id}: {e}")
        if conn: conn.rollback()
        return jsonify({'error': 'An unexpected error occurred during analysis'}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/v1/analysis_results/<int:pdf_id>', methods=['GET'])
def get_analysis_results(pdf_id):
    """Retrieves component extraction analysis results for a given PDF ID (JSON format)."""
    try:
        # Use the helper function to get data
        pdf_filename, components, analysis_type = _get_analysis_data(pdf_id)

        # Format the results into the desired JSON structure
        return jsonify({
            'pdf_id': pdf_id,
            'pdf_filename': pdf_filename, # Include filename for context
            'analysis_type': analysis_type,
            'components': components
        }), 200

    except NotFoundError as e:
        logging.warning(f"NotFound error fetching results for PDF ID {pdf_id}: {e}")
        return jsonify({'error': str(e)}), 404
    except psycopg2.Error as e: # Catch potential DB errors propagated from helper
        logging.error(f"Database error fetching results for PDF ID {pdf_id}: {e}")
        return jsonify({'error': 'Database error occurred while fetching results'}), 500
    except Exception as e:
        logging.error(f"Unexpected error fetching results for PDF ID {pdf_id}: {e}")
        return jsonify({'error': 'An internal server error occurred while fetching results'}), 500


# --- NEW EXPORT ENDPOINT ---
@app.route('/api/v1/analysis_results/<int:pdf_id>/export', methods=['GET'])
def export_analysis_results(pdf_id):
    """Exports analysis results as JSON or CSV file."""
    # Get requested format from query param, default to 'json'
    req_format = request.args.get('format', 'json').lower()

    try:
        # Use the helper function to get data
        pdf_filename, components, analysis_type = _get_analysis_data(pdf_id)

        # Generate JSON format
        if req_format == 'json':
            json_data = {
                'pdf_id': pdf_id,
                'pdf_filename': pdf_filename,
                'analysis_type': analysis_type,
                'components': components
            }
            # Use make_response to set headers for download
            response = make_response(jsonify(json_data))
            response.headers['Content-Disposition'] = f'attachment; filename="analysis_{pdf_id}.json"'
            # Content-Type is automatically set by jsonify, but can be explicit:
            # response.headers['Content-Type'] = 'application/json'
            return response

        # Generate CSV format
        elif req_format == 'csv':
            # Use io.StringIO as an in-memory text buffer
            si = io.StringIO()
            writer = csv.writer(si)

            # Write header row
            writer.writerow(['pdf_id', 'pdf_filename', 'analysis_type', 'component_name'])

            # Write data rows
            if components:
                for component in components:
                    writer.writerow([pdf_id, pdf_filename, analysis_type, component])
            else:
                # Optionally write a row indicating no components if list is empty
                # writer.writerow([pdf_id, pdf_filename, analysis_type, "--- No components found ---"])
                pass # Or just output header only if no components

            output = si.getvalue()
            # Use make_response to set headers for download
            response = make_response(output)
            response.headers['Content-Disposition'] = f'attachment; filename="analysis_{pdf_id}.csv"'
            response.headers['Content-Type'] = 'text/csv'
            return response

        # Handle invalid format request
        else:
            logging.warning(f"Invalid export format requested: {req_format} for PDF ID {pdf_id}")
            return jsonify({'error': f"Unsupported format: {req_format}. Use 'json' or 'csv'."}), 400

    except NotFoundError as e:
        logging.warning(f"NotFound error during export for PDF ID {pdf_id}: {e}")
        return jsonify({'error': str(e)}), 404
    except psycopg2.Error as e:
        logging.error(f"Database error during export for PDF ID {pdf_id}: {e}")
        return jsonify({'error': 'Database error occurred during export'}), 500
    except Exception as e:
        logging.error(f"Unexpected error during export for PDF ID {pdf_id}: {e}")
        return jsonify({'error': 'An internal server error occurred during export'}), 500


# --- Main Execution ---
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)