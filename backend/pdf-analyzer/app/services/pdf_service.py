import re
import logging
import pdfminer.high_level # type: ignore

def extract_text_from_pdf(pdf_path):
    """Extracts text content from a PDF file using pdfminer."""
    logging.debug(f"Extracting text from: {pdf_path}")
    try:
        text = pdfminer.high_level.extract_text(pdf_path)
        logging.info(f"Text extracted successfully from {pdf_path} (length: {len(text)}).")
        return text
    except Exception as e:
        logging.error(f"Error extracting text from {pdf_path}: {e}")
        return ""

def extract_components(text):
    """Extracts predefined components from text using regex."""
    # Consider making patterns configurable later
    component_patterns = [
        r"spindle\s*([a-zA-Z0-9\-\s]+)",
        r"motor\s*([a-zA-Z0-9\-\s]+)",
        r"axis\s*([a-zA-Z0-9\-\s]+)",
        r"controller\s*([a-zA-Z0-9\-\s]+)",
        r"tool changer\s*([a-zA-Z0-9\-\s]+)",
    ]
    components = []
    logging.debug("Starting component extraction from text.")
    if not text:
        logging.warning("Cannot extract components, input text is empty.")
        return components

    for pattern in component_patterns:
        try:
            matches = re.findall(pattern, text, re.IGNORECASE)
            components.extend([match.strip() for match in matches])
        except Exception as e:
            logging.error(f"Error applying regex pattern '{pattern}': {e}")
            # Decide if you want to continue with other patterns or stop

    unique_components = list(set(components))
    logging.info(f"Component extraction found {len(unique_components)} unique components.")
    logging.debug(f"Extracted components: {unique_components}")
    return unique_components

# --- Add OCR function here later ---
# def get_text_from_pdf_with_ocr(pdf_path): ...