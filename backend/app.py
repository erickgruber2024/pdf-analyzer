# backend/app.py
from flask import Flask, jsonify
from flask_cors import CORS
import psycopg2
import os

app = Flask(__name__)
CORS(app)

def get_db_connection():
    print(f"DATABASE_URL from Flask: {os.environ.get('DATABASE_URL')}") #Add this line
    conn = psycopg2.connect("postgresql://postgres@127.0.0.1:5432/postgres")
    return conn

@app.route('/api/v1/health', methods=['GET'])
def health():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT version()')
    db_version = cur.fetchone()
    conn.close()
    return jsonify({'status': 'ok', "database_version": db_version})

@app.route('/api/v1/test_connection', methods=['GET'])
def test_connection():
    return jsonify({'message': 'Backend connection successful!'})

@app.route('/api/v1/upload_pdf', methods=['POST'])
def upload_pdf():
    # Placeholder for PDF upload logic
    return jsonify({'message': 'PDF upload endpoint'})

@app.route('/api/v1/get_data', methods=['GET'])
def get_data():
    # Placeholder for data retrieval logic
    return jsonify({'message': 'Data retrieval endpoint'})

if __name__ == '__main__':
    app.run(debug=True)