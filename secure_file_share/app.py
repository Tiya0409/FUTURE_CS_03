from flask import Flask, render_template, request, send_file
from Crypto.Cipher import AES
from dotenv import load_dotenv
import os
import base64

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 🔷 KEY ko .env se load karte hain
load_dotenv()
key_b64 = os.getenv("AES_KEY")
if not key_b64:
    raise Exception("AES_KEY not found in .env file")
KEY = base64.b64decode(key_b64)

def encrypt_file(data):
    cipher = AES.new(KEY, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(data)
    return cipher.nonce + tag + ciphertext

def decrypt_file(data):
    nonce = data[:16]
    tag = data[16:32]
    ciphertext = data[32:]
    cipher = AES.new(KEY, AES.MODE_EAX, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']
        filename = file.filename
        file_data = file.read()

        encrypted_data = encrypt_file(file_data)

        with open(os.path.join(UPLOAD_FOLDER, filename + '.enc'), 'wb') as f:
            f.write(encrypted_data)

        return f"✅ File '{filename}' uploaded & encrypted successfully!"

    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    filename = request.form['filename']
    filepath = os.path.join(UPLOAD_FOLDER, filename + '.enc')

    if not os.path.exists(filepath):
        return "❌ File not found!"

    with open(filepath, 'rb') as f:
        encrypted_data = f.read()

    try:
        decrypted_data = decrypt_file(encrypted_data)
    except:
        return "❌ Decryption failed!"

    temp_path = os.path.join(UPLOAD_FOLDER, 'temp_' + filename)
    with open(temp_path, 'wb') as f:
        f.write(decrypted_data)

    return send_file(temp_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
