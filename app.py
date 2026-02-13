from flask import Flask, request, jsonify, send_from_directory, render_template_string
import mysql.connector
from mysql.connector import Error
import sqlite3
import os

app = Flask(__name__, static_folder='.', static_url_path='')

# Database Configuration
DB_TYPE = "MYSQL" # Options: "MYSQL", "SQLITE"
DB_NAME_SQLITE = "database.db"
DB_CONFIG_MYSQL = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Rohit',
    'database': 'primeeducation'
}

def get_db_connection():
    # Try MySQL first if configured
    if DB_TYPE == "MYSQL":
        try:
            conn = mysql.connector.connect(**DB_CONFIG_MYSQL)
            return conn, "MYSQL"
        except Error as e:
            print(f"MySQL Connection failed: {e}. Falling back to SQLite.")
    
    # Fallback to SQLite
    try:
        conn = sqlite3.connect(DB_NAME_SQLITE, timeout=20)
        conn.row_factory = sqlite3.Row
        return conn, "SQLITE"
    except Exception as e:
        print(f"SQLite Connection failed: {e}")
        return None, None

def init_db():
    conn, type = get_db_connection()
    if not conn:
        print("Failed to initialize any database.")
        return

    try:
        cursor = conn.cursor()
        if type == "MYSQL":
            # Create database if not exists (needs separate connection to mysql server)
            try:
                temp_conn = mysql.connector.connect(
                    host=DB_CONFIG_MYSQL['host'],
                    user=DB_CONFIG_MYSQL['user'],
                    password=DB_CONFIG_MYSQL['password']
                )
                temp_cursor = temp_conn.cursor()
                temp_cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG_MYSQL['database']}")
                temp_conn.close()
            except:
                pass # Already handled by fallback if this fails
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS inquiries (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    child_name VARCHAR(255),
                    class_grade VARCHAR(100) NOT NULL,
                    phone VARCHAR(20) NOT NULL,
                    message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        else: # SQLITE
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS inquiries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    child_name TEXT,
                    class_grade TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        conn.commit()
    except Exception as e:
        print(f"Error initializing table: {e}")
    finally:
        conn.close()

# Initialize Database
init_db()

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

@app.route('/api/contact', methods=['POST'])
def save_contact():
    data = request.json
    conn, type = get_db_connection()
    if not conn:
        return jsonify({"status": "error", "message": "Database connection failed"}), 500
    
    try:
        cursor = conn.cursor()
        if type == "MYSQL":
            cursor.execute('''
                INSERT INTO inquiries (name, child_name, class_grade, phone, message)
                VALUES (%s, %s, %s, %s, %s)
            ''', (data.get('name'), data.get('child_name'), data.get('class_grade'), data.get('phone'), data.get('message')))
        else: # SQLITE
            cursor.execute('''
                INSERT INTO inquiries (name, child_name, class_grade, phone, message)
                VALUES (?, ?, ?, ?, ?)
            ''', (data.get('name'), data.get('child_name'), data.get('class_grade'), data.get('phone'), data.get('message')))
        conn.commit()
        return jsonify({"status": "success", "message": f"Inquiry saved successfully! (via {type})"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        conn.close()

@app.route('/admin/inquiries', methods=['GET'])
def view_inquiries():
    conn, type = get_db_connection()
    if not conn:
        return "Database connection failed", 500
    
    try:
        if type == "MYSQL":
            cursor = conn.cursor(dictionary=True)
        else:
            cursor = conn.cursor()
            
        cursor.execute('SELECT * FROM inquiries ORDER BY created_at DESC')
        rows = cursor.fetchall()
    finally:
        conn.close()
    
    # Simple HTML table to view data
    html = '''
    <!DOCTYPE html>
    <html>
    <head><title>Inquiries</title>
    <style>
        table { border-collapse: collapse; width: 100%; font-family: sans-serif; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #0A2351; color: white; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        .meta { margin-bottom: 20px; font-weight: bold; color: #0A2351; }
    </style>
    </head>
    <body>
        <h2>Prime Education Centre - Submitted Inquiries</h2>
        <div class="meta">Current Database: {{ db_type }}</div>
        <table>
            <tr>
                <th>ID</th><th>Name</th><th>Student</th><th>Class</th><th>Phone</th><th>Message</th><th>Date</th>
            </tr>
            {% for row in rows %}
            <tr>
                <td>{{ row['id'] }}</td>
                <td>{{ row['name'] }}</td>
                <td>{{ row['child_name'] }}</td>
                <td>{{ row['class_grade'] }}</td>
                <td>{{ row['phone'] }}</td>
                <td>{{ row['message'] }}</td>
                <td>{{ row['created_at'] }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    '''
    return render_template_string(html, rows=rows, db_type=type)

if __name__ == '__main__':
    print(f"Server running on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
