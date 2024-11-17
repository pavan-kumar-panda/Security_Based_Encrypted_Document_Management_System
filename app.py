print("FILE ENCRYPTER..")
from cryptography.fernet import Fernet
from flask import Flask, request, render_template, redirect, url_for,send_from_directory
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Store passwords for sensitive files
passwords = {}


@app.route('/download/<filename>')
def download_file(filename):
    print(f"Request to download file: {filename}")  # Debugging line
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    print(f"File path resolved to: {file_path}")    # Debugging line

    if not os.path.exists(file_path):
        return f"File {filename} not found!", 404

    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/')
def home():
    # Get list of files in the upload folder
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('home.html', files=files)


@app.route('/upload', methods=['POST'])
def upload_file():
    category = request.form['category']
    password = request.form.get('password', None)
    file = request.files['file']

    if file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        
        # Encrypt file only if not in 'work' category
        if category != 'work':
            key = generate_key()
            encrypt_file(file_path, key)

            # Store key and password for personal/sensitive files
            if category in ['personal', 'sensitive'] and password:
                passwords[file.filename] = (key, password)

    return redirect(url_for('home'))


@app.route('/view/<filename>', methods=['GET', 'POST'])
def view_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if request.method == 'POST':
        # For personal and sensitive files, check password
        if filename in passwords:
            key, stored_password = passwords[filename]
            input_password = request.form['password']

            if input_password != stored_password:
                return "Incorrect password! Please try again."

            # Decrypt file for viewing
            decrypt_file(file_path, key)
            with open(file_path, 'r') as f:
                file_contents = f.read()

            # Re-encrypt the file immediately after viewing
            encrypt_file(file_path, key)
            return f"<pre>{file_contents}</pre>"

        # For work files (no password required), no encryption
        else:
            with open(file_path, 'r') as f:
                file_contents = f.read()

            return f"<pre>{file_contents}</pre>"

    # Display password input form if required
    if filename in passwords:
        return render_template('view.html', filename=filename)

    # For work files, display directly without password
    return redirect(url_for('download_file', filename=filename))





# Generate a key for encryption
def generate_key():
    return Fernet.generate_key()

# Encrypt a file
def encrypt_file(file_path, key):
    with open(file_path, 'rb') as f:
        data = f.read()
    encrypted_data = Fernet(key).encrypt(data)
    with open(file_path, 'wb') as f:
        f.write(encrypted_data)

# Decrypt a file
def decrypt_file(file_path, key):
    with open(file_path, 'rb') as f:
        encrypted_data = f.read()
    decrypted_data = Fernet(key).decrypt(encrypted_data)
    with open(file_path, 'wb') as f:
        f.write(decrypted_data)

if __name__ == '__main__':
    app.run(debug=True)