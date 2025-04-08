# PDF Analyzer Application Setup

This document outlines the steps taken to set up the backend (Flask), PostgreSQL database, and Angular frontend for the PDF Analyzer application.

## Backend (Flask) Setup

1.  **Project Initialization:**
    * Created a new Flask project directory.
    * Initialized a virtual environment: `python -m venv venv`
    * Activated the virtual environment:
        * Windows (Command Prompt): `venv\Scripts\activate`
        * Windows (PowerShell): `venv\Scripts\Activate.ps1`
        * macOS/Linux: `source venv/bin/activate`
    * Installed Flask and psycopg2-binary: `pip install Flask psycopg2-binary flask-cors`
2.  **Database Connection:**
    * Installed PostgreSQL.
    * Configured the `DATABASE_URL` environment variable:
        * Initially, faced connection issues due to incorrect password and environment variable discrepancies.
        * Corrected the `DATABASE_URL` to: `postgresql://postgres@127.0.0.1:5432/postgres`
        * Modified `pg_hba.conf` to allow `trust` connections from localhost for initial development.
    * Created a `get_db_connection()` function in `app.py` to establish database connections.
    * Created a health check endpoint `/api/v1/health` to verify database connectivity.
3.  **API Endpoints:**
    * Created basic API endpoints for:
        * `/api/v1/test_connection` (to test connectivity from the frontend).
        * `/api/v1/upload_pdf` (placeholder for PDF upload).
        * `/api/v1/get_data` (placeholder for data retrieval).
4.  **Database Schema:**
    * Created `pdfs` and `extracted_data` tables in PostgreSQL:
        * `pdfs`: stores PDF file information and content.
        * `extracted_data`: stores extracted data points from PDFs.

## PostgreSQL Setup

1.  **Installation:**
    * Installed PostgreSQL on the local machine.
2.  **Database Creation:**
    * Used `psql` to create the `postgres` database.
3.  **User and Permissions:**
    * Used the default `postgres` user for local development.
    * Configured `pg_hba.conf` to allow trust connections from localhost.
4.  **Table Creation:**
    * Created the `pdfs` and `extracted_data` tables using SQL commands.

## Frontend (Angular) Setup

1.  **Project Initialization:**
    * Created a new Angular project using the Angular CLI: `ng new frontend --standalone`
2.  **HTTP Client:**
    * Configured `HttpClient` in `app.config.ts` using `provideHttpClient()`.
3.  **API Service:**
    * Created an `ApiService` to handle HTTP requests to the Flask backend.
4.  **Component Integration:**
    * Modified `app.component.ts` to call the `/api/v1/test_connection` endpoint and display the response.
    * Imported CommonModule and HttpClientModule to the component.
5.  **CORS Configuration:**
    * Enabled CORS in the Flask backend using the `flask-cors` library to allow cross-origin requests from the Angular frontend.

## Git Setup

1.  **Initial Git Configuration Issues:**
    * Encountered an error due to an invalid character in the Git configuration path (`C:\Users?rick`).
    * Corrected the issue by verifying the Windows username and setting the `HOME` environment variable.
2.  **VS Code Git Integration:**
    * Ensured Git was properly installed and configured for VS Code.
    * Verified that the correct repository was open in VS Code.
    * Checked the VS Code Source Control tab for uncommitted changes.

## Next Steps

* Implement PDF upload functionality in Flask and Angular.
* Integrate PDF processing using a Python library (e.g., `PyPDF2`, `pdfminer.six`).
* Store extracted data in the PostgreSQL database.
* Implement data retrieval API endpoints.
* Develop Angular components to display the extracted data.
