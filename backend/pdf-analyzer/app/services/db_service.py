import psycopg2
import logging
from flask import current_app # Use current_app to access config
from app.utils.exceptions import NotFoundError # Import custom exception

def get_db_connection():
    """Establishes a connection to the PostgreSQL database using app config."""
    conn = None
    db_url = current_app.config['DATABASE_URL']
    if not db_url:
         # This should ideally be caught during config loading, but double-check
         logging.error("DATABASE_URL is not configured.")
         raise ValueError("Database URL not configured.")
    try:
        conn = psycopg2.connect(db_url)
        logging.debug("Database connection established.")
        return conn
    except psycopg2.Error as e:
        logging.error(f"Error connecting to database at {db_url[:db_url.find('@')] + '@...' if '@' in db_url else db_url}: {e}") # Avoid logging password
        raise # Propagate the error

def _get_analysis_data(pdf_id: int):
    """
    Helper function to retrieve filename and component analysis results for a PDF ID.
    Raises NotFoundError if the PDF doesn't exist.
    Returns tuple (pdf_filename, components_list, analysis_type).
    """
    conn = None
    logging.debug(f"Attempting to fetch analysis data for pdf_id: {pdf_id}")
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # 1. Get PDF filename
        cur.execute('SELECT filename FROM pdfs WHERE id = %s', (pdf_id,))
        pdf_record = cur.fetchone()
        if pdf_record is None:
            logging.warning(f"PDF with id {pdf_id} not found in database.")
            raise NotFoundError(f"PDF with id {pdf_id} not found")
        pdf_filename = pdf_record[0]
        logging.info(f"Found PDF: {pdf_filename} (ID: {pdf_id})")

        # 2. Get associated components
        analysis_type = 'component_extraction' # Keep hardcoded for now
        cur.execute(
            """
            SELECT ed.data_value
            FROM extracted_data ed
            JOIN pdf_analyses pa ON ed.analysis_id = pa.id
            WHERE pa.pdf_id = %s AND pa.analysis_type = %s AND ed.data_key = %s
            ORDER BY ed.id ASC
            """,
            (pdf_id, analysis_type, 'component_name')
        )
        results = cur.fetchall()
        components = [row[0] for row in results]
        logging.info(f"Found {len(components)} components for PDF ID {pdf_id}")

        cur.close()
        return pdf_filename, components, analysis_type

    except psycopg2.Error as db_err:
        logging.error(f"Database error fetching analysis data for PDF ID {pdf_id}: {db_err}")
        raise # Re-raise database errors
    finally:
        if conn:
            conn.close()
            logging.debug("Database connection closed.")

# --- Add functions here later for saving analysis data too ---
# def save_analysis_results(pdf_id, analysis_type, components): ...