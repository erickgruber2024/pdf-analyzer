import os
import logging
import psycopg2
import csv
import io
from flask import Blueprint, jsonify, request, make_response, current_app
from werkzeug.utils import secure_filename

# Import helpers, services, exceptions
from app.utils.helpers import allowed_file
from app.services.pdf_service import extract_text_from_pdf, extract_components
from app.services.db_service import get_db_connection, _get_analysis_data
from app.utils.exceptions import NotFoundError

# Define blueprint
pdf_bp = Blueprint('pdf', __name__, url_prefix='/api/v1')

@pdf_bp.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    """Handles PDF file uploads, saves file, and records in DB."""
    # Use current_app.config instead of global variable
    upload_folder = current_app.config['UPLOAD_FOLDER']

    if 'file' not in request.files:
        logging.warning("Upload attempt failed: No file part.")
        return jsonify({'error': 'No file part in the request'}), 400
    file = request.files['file']
    if file.filename == '':
        logging.warning("Upload attempt failed: No selected file.")
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename): # Use helper function
        filename = secure_filename(file.filename)
        filepath = os.path.join(upload_folder, filename)
        conn = None
        try:
            file.save(filepath)
            logging.info(f"File saved successfully: {filepath}")

            conn = get_db_connection() # Use service function
            cur = conn.cursor()
            # Consider checking if filename already exists in DB?
            cur.execute('INSERT INTO pdfs (filename) VALUES (%s) RETURNING id', (filename,))
            pdf_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            logging.info(f"PDF record created in database with ID: {pdf_id}")
            return jsonify({'message': 'PDF uploaded successfully', 'pdf_id': pdf_id}), 201

        except psycopg2.Error as e:
            logging.error(f"Database error during PDF upload for {filename}: {e}")
            # Consider cleaning up saved file if DB fails: if os.path.exists(filepath): os.remove(filepath)
            return jsonify({'error': 'Database error during upload'}), 500
        except Exception as e:
            # Catch file save errors etc.
            logging.error(f"Error during file upload process for {filename}: {e}")
            return jsonify({'error': f'Failed to save or process file: {e}'}), 500
        finally:
            if conn:
                conn.close()
    else:
        logging.warning(f"Upload attempt failed: Invalid file type for {file.filename}.")
        return jsonify({'error': 'Invalid file type. Only PDF allowed.'}), 400


@pdf_bp.route('/analyze_pdf/<int:pdf_id>', methods=['POST'])
def analyze_pdf(pdf_id):
    """Triggers text extraction and component analysis for a given PDF ID."""
    upload_folder = current_app.config['UPLOAD_FOLDER']
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # 1. Find filename (check existence)
        cur.execute('SELECT filename FROM pdfs WHERE id = %s', (pdf_id,))
        pdf_record = cur.fetchone()
        if pdf_record is None:
             raise NotFoundError(f"PDF with id {pdf_id} not found for analysis.") # Use custom exception
        pdf_filename = pdf_record[0]
        pdf_path = os.path.join(upload_folder, pdf_filename)

        # 2. Check file exists on disk
        if not os.path.exists(pdf_path):
            logging.error(f"File not found on disk for analysis: {pdf_path}")
            # Maybe DB record exists but file deleted?
            return jsonify({'error': 'PDF file consistency error - file not found on server'}), 404 # Or 500?

        # 3. Extract text (using pdf_service)
        # Future: Replace with get_text_from_pdf_with_ocr from pdf_service
        extracted_text = extract_text_from_pdf(pdf_path)
        if not extracted_text:
            logging.warning(f"No text extracted from PDF ID {pdf_id}: {pdf_path}. Analysis may yield no results.")

        # 4. Extract components (using pdf_service)
        components = extract_components(extracted_text)

        # 5. Insert analysis metadata
        analysis_type = 'component_extraction'
        cur.execute(
            'INSERT INTO pdf_analyses (pdf_id, analysis_type) VALUES (%s, %s) RETURNING id',
            (pdf_id, analysis_type),
        )
        analysis_id = cur.fetchone()[0]
        logging.info(f"Created analysis record ID {analysis_id} for PDF ID {pdf_id}")

        # 6. Insert extracted components
        if components:
            # Consider moving this DB logic to db_service.py later
            component_data = [(analysis_id, 'component_name', comp) for comp in components]
            cur.executemany(
                'INSERT INTO extracted_data (analysis_id, data_key, data_value) VALUES (%s, %s, %s)',
                component_data
            )
            logging.info(f"Inserted {len(components)} components into extracted_data for analysis ID {analysis_id}")
        else:
            logging.info(f"No components to insert for analysis ID {analysis_id}")

        # 7. Commit transaction
        conn.commit()
        cur.close()
        return jsonify({'message': f'Analysis complete for PDF ID {pdf_id}', 'analysis_id': analysis_id, 'components_found': len(components)})

    except NotFoundError as e:
        logging.warning(f"NotFound error during analysis for PDF ID {pdf_id}: {e}")
        # No rollback needed as nothing was likely done yet
        return jsonify({'error': str(e)}), 404
    except psycopg2.Error as e:
        logging.error(f"Database error during analysis for PDF ID {pdf_id}: {e}")
        if conn: conn.rollback()
        return jsonify({'error': 'Database error during analysis'}), 500
    except FileNotFoundError: # Should be caught by os.path.exists, but belt-and-suspenders
         logging.error(f"File vanished during analysis for PDF ID {pdf_id}: {pdf_path}")
         return jsonify({'error': 'PDF file disappeared during analysis'}), 500
    except Exception as e:
        logging.error(f"Unexpected error during analysis for PDF ID {pdf_id}: {e}")
        if conn: conn.rollback()
        return jsonify({'error': 'An unexpected error occurred during analysis'}), 500
    finally:
        if conn:
            conn.close()


@pdf_bp.route('/analysis_results/<int:pdf_id>', methods=['GET'])
def get_analysis_results(pdf_id):
    """Retrieves component extraction analysis results for a given PDF ID (JSON format)."""
    try:
        # Use the helper function from db_service
        pdf_filename, components, analysis_type = _get_analysis_data(pdf_id)
        return jsonify({
            'pdf_id': pdf_id,
            'pdf_filename': pdf_filename,
            'analysis_type': analysis_type,
            'components': components
        }), 200
    except NotFoundError as e:
        logging.warning(f"NotFound error fetching results for PDF ID {pdf_id}: {e}")
        return jsonify({'error': str(e)}), 404
    except psycopg2.Error as e: # Catch DB errors propagated from helper
        logging.error(f"Database error fetching results for PDF ID {pdf_id}: {e}")
        return jsonify({'error': 'Database error occurred while fetching results'}), 500
    except Exception as e:
        logging.error(f"Unexpected error fetching results for PDF ID {pdf_id}: {e}")
        return jsonify({'error': 'An internal server error occurred while fetching results'}), 500


@pdf_bp.route('/analysis_results/<int:pdf_id>/export', methods=['GET'])
def export_analysis_results(pdf_id):
    """Exports analysis results as JSON or CSV file."""
    req_format = request.args.get('format', 'json').lower()
    try:
        pdf_filename, components, analysis_type = _get_analysis_data(pdf_id) # Use helper

        if req_format == 'json':
            json_data = {
                'pdf_id': pdf_id, 'pdf_filename': pdf_filename,
                'analysis_type': analysis_type, 'components': components
            }
            response = make_response(jsonify(json_data))
            response.headers['Content-Disposition'] = f'attachment; filename="analysis_{pdf_id}.json"'
            return response

        elif req_format == 'csv':
            si = io.StringIO()
            writer = csv.writer(si)
            writer.writerow(['pdf_id', 'pdf_filename', 'analysis_type', 'component_name'])
            if components:
                for component in components:
                    writer.writerow([pdf_id, pdf_filename, analysis_type, component])
            output = si.getvalue()
            response = make_response(output)
            response.headers['Content-Disposition'] = f'attachment; filename="analysis_{pdf_id}.csv"'
            response.headers['Content-Type'] = 'text/csv'
            return response
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