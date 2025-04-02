-- Create the pdfs table
CREATE TABLE pdfs (
    id SERIAL PRIMARY KEY,
    filename TEXT,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create the pdf_analyses table
CREATE TABLE pdf_analyses (
    id SERIAL PRIMARY KEY,
    pdf_id INTEGER REFERENCES pdfs(id),
    analysis_type TEXT,
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create the extracted_data table
CREATE TABLE extracted_data (
    id SERIAL PRIMARY KEY,
    analysis_id INTEGER REFERENCES pdf_analyses(id),
    data_key TEXT,
    data_value TEXT
);