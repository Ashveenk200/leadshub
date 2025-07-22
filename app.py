from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import json
import pandas as pd
from werkzeug.utils import secure_filename
from flask_cors import CORS

# ---------- Configuration ----------
app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads')
FILES_JSON = 'files.json'
CREDENTIALS_FILE = os.path.join(UPLOAD_FOLDER, 'admin_credentials.txt')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload size

# Create necessary folders and files
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(CREDENTIALS_FILE):
    with open(CREDENTIALS_FILE, 'w') as f:
        f.write("ADMIN,ASHveen002@")  # Default credentials

# ---------- Helper Functions ----------
def load_files():
    if os.path.exists(FILES_JSON):
        with open(FILES_JSON, 'r') as f:
            return json.load(f)
    return []

def save_files(files):
    with open(FILES_JSON, 'w') as f:
        json.dump(files, f, indent=2)

# ---------- Frontend Routes ----------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/about_us')
def about_us():
    return render_template('about_us.html')

@app.route('/contactus')
def contactus():
    return render_template('contactus.html')

@app.route('/FAQ')
def FAQ():
    return render_template('FAQ.html')

@app.route('/PrivacyPolicy')
def PrivacyPolicy():
    return render_template('PrivacyPolicy.html')

@app.route('/TermsofService')
def TermsofService():
    return render_template('TermsofService.html')

@app.route('/download')
def download_page():
    filename = request.args.get('file')
    if not filename:
        return render_template('download.html', filename=None, error="No file specified")
    files = load_files()
    file_data = next((f for f in files if f['filename'] == filename), None)
    if file_data:
        return render_template('download.html', filename=filename, file_data=file_data)
    return render_template('download.html', filename=None, error="File not found")

# ---------- File Management Routes ----------
@app.route('/uploads/<path:filename>')
def download_file(filename):
    try:
        files = load_files()
        if any(f['filename'] == filename for f in files):
            return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
        return jsonify({"error": "File not found"}), 404
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404

@app.route('/api/files', methods=['GET', 'POST'])
def handle_files():
    if request.method == 'GET':
        return jsonify(load_files())

    if request.method == 'POST':
        uploaded_file = request.files.get('file')
        if uploaded_file:
            filename = secure_filename(uploaded_file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            uploaded_file.save(filepath)

            file_data = {
                "name": request.form.get("name"),
                "category": request.form.get("category"),
                "country": request.form.get("country"),
                "price": request.form.get("price"),
                "payment_id": request.form.get("payment_id"),
                "description": request.form.get("description"),
                "filename": filename,
                "filepath": f"/uploads/{filename}",
                "downloads": 0
            }

            files = load_files()
            files.append(file_data)
            save_files(files)
            return jsonify({"message": "✅ File uploaded"}), 201

        return jsonify({"error": "No file uploaded"}), 400

    return jsonify({"error": "Invalid request method"}), 405

@app.route('/api/files/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    files = load_files()
    files = [f for f in files if f['filename'] != filename]
    save_files(files)

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({"message": "🗑️ File deleted successfully"}), 200
    else:
        return jsonify({"warning": "File not found on disk, but removed from metadata"}), 200

@app.route('/api/files/edit/<filename>', methods=['PUT'])
def edit_file(filename):
    updated_data = request.json
    files = load_files()
    for f in files:
        if f['filename'] == filename:
            f.update(updated_data)
            break
    else:
        return jsonify({"error": "File not found"}), 404

    save_files(files)
    return jsonify({"message": "✏️ File metadata updated"}), 200

@app.route('/api/preview/<filename>', methods=['GET'])
def preview_file(filename):
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if filename.endswith('.csv'):
            df = pd.read_csv(filepath, nrows=10)
        elif filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(filepath, nrows=10)
        else:
            return jsonify({"error": "Unsupported file type"}), 400
        return jsonify({
            "columns": list(df.columns),
            "rows": df.fillna("").values.tolist()
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/increment-download/<filename>', methods=['POST'])
def increment_download(filename):
    files = load_files()
    for file in files:
        if file['filename'] == filename:
            file['downloads'] = file.get('downloads', 0) + 1
            save_files(files)
            return jsonify({"message": "Download count incremented"}), 200
    return jsonify({"error": "File not found"}), 404

# ---------- Authentication ----------
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    input_id = data.get("admin_id")
    input_password = data.get("admin_password")

    try:
        with open(CREDENTIALS_FILE, 'r') as f:
            stored = f.read().strip().split(',')
            if len(stored) != 2:
                return jsonify({"success": False, "message": "Invalid credentials format."}), 500
            stored_id, stored_pass = stored

        if input_id == stored_id and input_password == stored_pass:
            return jsonify({"success": True}), 200
        else:
            return jsonify({"success": False, "message": "Invalid ID or password."}), 401
    except FileNotFoundError:
        return jsonify({"success": False, "message": "Credentials file not found."}), 500
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ---------- Run Server ----------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8888)