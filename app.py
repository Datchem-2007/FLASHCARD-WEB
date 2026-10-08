from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
import uuid
import time
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
# Cho phép frontend từ file HTML được phép gọi API (Rất quan trọng khi test ở Local)
CORS(app) 

@app.route("/")
def index():
    return render_template("flashcard.html")
def get_db_connection():
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            port=int(os.getenv("DB_PORT", 3306))
        )
    except Error as e:
        print(f"Lỗi kết nối MySQL: {e}")
        return None

@app.route('/projects', methods=['GET'])
def get_projects():
    user_id = request.args.get('user_id')
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Không thể kết nối đến MySQL. Hãy kiểm tra lại mật khẩu hoặc xem MySQL đã bật chưa."}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM projects WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
        projects = cursor.fetchall()
        conn.close()
        return jsonify(projects)
    except Error as e:
        return jsonify({"error": str(e)}), 500

@app.route('/projects', methods=['POST'])
def create_project():
    data = request.json
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Lỗi kết nối CSDL"}), 500
    try:
        cursor = conn.cursor()
        new_id = str(uuid.uuid4()) # Tạo ID ngẫu nhiên không trùng lặp
        created_at = int(time.time() * 1000)
        cursor.execute("INSERT INTO projects (id, user_id, name, created_at) VALUES (%s, %s, %s, %s)", 
                       (new_id, data['user_id'], data['name'], created_at))
        conn.commit()
        conn.close()
        return jsonify({"id": new_id}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500

@app.route('/projects/<project_id>', methods=['PUT'])
def update_project(project_id):
    data = request.json
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Lỗi kết nối CSDL"}), 500
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE projects SET name = %s WHERE id = %s", (data['name'], project_id))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Error as e:
        return jsonify({"error": str(e)}), 500

@app.route('/projects/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Lỗi kết nối CSDL"}), 500
    try:
        cursor = conn.cursor()
        # Xóa tất cả các thẻ nằm trong project đó trước khi xóa project
        cursor.execute("DELETE FROM cards WHERE project_id = %s", (project_id,)) 
        cursor.execute("DELETE FROM projects WHERE id = %s", (project_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Error as e:
        return jsonify({"error": str(e)}), 500

@app.route('/cards', methods=['GET'])
def get_cards():
    project_id = request.args.get('project_id')
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Lỗi kết nối CSDL"}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM cards WHERE project_id = %s ORDER BY created_at ASC", (project_id,))
        cards = cursor.fetchall()
        conn.close()
        return jsonify(cards)
    except Error as e:
        return jsonify({"error": str(e)}), 500

@app.route('/cards', methods=['POST'])
def create_card():
    data = request.json
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Lỗi kết nối CSDL"}), 500
    try:
        cursor = conn.cursor()
        new_id = str(uuid.uuid4())
        created_at = int(time.time() * 1000)
        cursor.execute("INSERT INTO cards (id, project_id, front, back, created_at) VALUES (%s, %s, %s, %s, %s)", 
                       (new_id, data['project_id'], data['front'], data['back'], created_at))
        conn.commit()
        conn.close()
        return jsonify({"id": new_id}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500

@app.route('/cards/<card_id>', methods=['PUT'])
def update_card(card_id):
    data = request.json
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Lỗi kết nối CSDL"}), 500
    try:
        cursor = conn.cursor()
        updated_at = int(time.time() * 1000)
        cursor.execute("UPDATE cards SET front = %s, back = %s, updated_at = %s WHERE id = %s", 
                       (data['front'], data['back'], updated_at, card_id))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Error as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=True
    )