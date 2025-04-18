from flask import Flask, request, jsonify
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.Util.Padding import pad, unpad
import base64
import os
#DoS ochrana
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import shutil
from flask import abort
import subprocess
from crypto.secure_logger_server import SecureServerLogger

app = Flask(__name__)
limiter = Limiter(get_remote_address, app=app)

BASE_FILE_PATH = "./server_files/"
PRIVATE_KEY_PATH = "server_private_key.pem"
PUBLIC_KEY_PATH = "server_public_key.pem"

logger = SecureServerLogger("./logs/secure_server_log.txt")

# Funkce pro generování nebo načtení klíčů
def load_or_generate_keys():
    if os.path.exists(PRIVATE_KEY_PATH) and os.path.exists(PUBLIC_KEY_PATH):
        with open(PRIVATE_KEY_PATH, "rb") as private_file:
            private_key = RSA.import_key(private_file.read())
        with open(PUBLIC_KEY_PATH, "rb") as public_file:
            public_key = RSA.import_key(public_file.read())
    else:
        private_key = RSA.generate(2048)
        public_key = private_key.publickey()
        with open(PRIVATE_KEY_PATH, "wb") as private_file:
            private_file.write(private_key.export_key())
        with open(PUBLIC_KEY_PATH, "wb") as public_file:
            public_file.write(public_key.export_key())
    return private_key, public_key

private_key, public_key = load_or_generate_keys()

# Uložení přijatého veřejného klíče klienta
@app.route("/register-public-key", methods=["POST"])
def register_public_key():
    data = request.json
    client_public_key = data.get("public_key")

    if not client_public_key:
        return jsonify({"error": "No public key received"}), 400

    try:
        with open("client_public_key.pem", "w") as f:
            f.write(client_public_key)

        logger.log("info","Client public key received and saved.")
        return jsonify({"status": "Client public key received successfully!"})
    except Exception as e:
        logger.log("error",f"Error saving client public key: {str(e)}")
        return jsonify({"error": "Failed to save public key"}), 500

# Poskytnutí veřejného klíče serveru
@app.route("/public-key", methods=["GET"])
def get_public_key():
    return jsonify({"public_key": public_key.export_key().decode()})

# Obdržení, dešifrování a uložení nahrávaného souboru
@app.route("/upload", methods=["POST"])
@limiter.limit("5 per minute") #DoS
def receive_encrypted_file():
    username = request.headers.get("X-Username")
    if not username:
        abort(401, description="Missing username header")

    data = request.json
    encrypted_aes_key = base64.b64decode(data.get("encrypted_aes_key", ""))
    encrypted_file = base64.b64decode(data.get("encrypted_file", ""))
    iv = base64.b64decode(data.get("iv", ""))
    filename = data.get("filename")

    if not filename:
        abort(400, description="Missing filename")

    user_path = user_dir(username)
    file_path = os.path.abspath(os.path.join(user_path, filename))

    if not is_safe_path(user_path, file_path):
        abort(400, description="Invalid file path")

    try:
        cipher_rsa = PKCS1_OAEP.new(private_key)
        aes_key = cipher_rsa.decrypt(encrypted_aes_key)

        cipher_aes = AES.new(aes_key, AES.MODE_CBC, iv)
        decrypted_file = unpad(cipher_aes.decrypt(encrypted_file), AES.block_size)

        with open(file_path, "wb") as f:
            f.write(decrypted_file)

        return jsonify({"status": "File decrypted and saved successfully!"})

    except Exception as e:
        logger.log("error",f"Decryption error: {str(e)}")
        return jsonify({"error": "Decryption failed."}), 500

# Funkce pro zašifrování a stažení vyžádaného souboru
@app.route("/get-file", methods=["GET"])
@limiter.limit("5 per minute") #DoS
def get_file():
    username = request.headers.get("X-Username")
    if not username:
        abort(401, description="Missing username header")

    file_path = request.args.get("file_path")
    user_path = user_dir(username)
    full_path = os.path.abspath(os.path.join(user_path, file_path))

    if not is_safe_path(user_path, full_path) or not os.path.exists(full_path):
        return jsonify({"error": "File not found!"}), 404

    try:
        encrypted_file, encrypted_aes_key, iv = encrypt_file(full_path)
        response = {
            "encrypted_file": base64.b64encode(encrypted_file).decode(),
            "encrypted_aes_key": base64.b64encode(encrypted_aes_key).decode(),
            "iv": base64.b64encode(iv).decode()
        }
        return jsonify(response)
    except Exception as e:
        logger.log("error",f"Encryption error: {str(e)}")
        return jsonify({"error": "Encryption failed."}), 500

# Šifrování souborů
def encrypt_file(file_path):
    aes_key = os.urandom(32)  # AES-256 klíč
    cipher_aes = AES.new(aes_key, AES.MODE_CBC)
    
    with open(file_path, "rb") as f:
        file_data = f.read()
    
    encrypted_file = cipher_aes.encrypt(pad(file_data, AES.block_size))
    
    # Zašifrování AES klíče pomocí veřejného klíče klienta
    client_public_key = RSA.import_key(open("client_public_key.pem").read())
    cipher_rsa = PKCS1_OAEP.new(client_public_key)
    encrypted_aes_key = cipher_rsa.encrypt(aes_key)
    
    return encrypted_file, encrypted_aes_key, cipher_aes.iv

# *************************** FILE MANAGER *************************************

# Funkce pro otevření správného adresáře (dle username), případně jeho vytvoření
def user_dir(username):
    path = os.path.abspath(os.path.join(BASE_FILE_PATH, username))
    os.makedirs(path, exist_ok=True)
    return path

# Funkce pro oveření správnosti zadané cesty (musí se nacházet v domovském adresáři base_path)
def is_safe_path(base_path, path):
    return os.path.commonpath([base_path, path]) == base_path

# Vytvoření souboru
@app.route("/create-file", methods=["POST"])
@limiter.limit("5 per minute") #DoS
def create_file():
    username = request.headers.get("X-Username")
    if not username:
        abort(401, description="Missing username header")

    data = request.json
    filename = data.get("filename")
    content = data.get("content", "")

    user_path = user_dir(username)
    file_path = os.path.abspath(os.path.join(user_path, filename))

    if not is_safe_path(user_path, file_path):
        abort(400, description="Invalid file path")

    with open(file_path, "w") as f:
        f.write(content)
    
    logger.log("info",f"{username} created file {filename}")
    return jsonify({"status": "File created", "path": file_path})

# Smazání souboru
@app.route("/delete-file", methods=["POST"])
@limiter.limit("5 per minute") #DoS
def delete_file():
    username = request.headers.get("X-Username")
    if not username:
        abort(401, description="Missing username header")

    data = request.json
    filename = data.get("filename")

    user_path = user_dir(username)
    file_path = os.path.abspath(os.path.join(user_path, filename))

    if not is_safe_path(user_path, file_path) or not os.path.isfile(file_path):
        abort(400, description="Invalid file path")

    os.remove(file_path)
    logger.log("info",f"{username} deleted file {filename}")
    return jsonify({"status": "File deleted"})

# Editace existujícího souboru
@app.route("/edit-file", methods=["POST"])
@limiter.limit("5 per minute") #DoS
def edit_file():
    username = request.headers.get("X-Username")
    if not username:
        abort(401, description="Missing username header")

    data = request.json
    filename = data.get("filename")
    content = data.get("content")

    user_path = user_dir(username)
    file_path = os.path.abspath(os.path.join(user_path, filename))

    if not is_safe_path(user_path, file_path) or not os.path.isfile(file_path):
        abort(400, description="Invalid file path")

    with open(file_path, "w") as f:
        f.write(content)

    logger.log("info",f"{username} edited file {filename}")
    return jsonify({"status": "File edited"})

# Vytvoření adresáře
@app.route("/create-directory", methods=["POST"])
@limiter.limit("5 per minute") #DoS
def create_directory():
    username = request.headers.get("X-Username")
    if not username:
        abort(401, description="Missing username header")

    data = request.json
    dirname = data.get("dirname")

    user_path = user_dir(username)
    dir_path = os.path.abspath(os.path.join(user_path, dirname))

    if not is_safe_path(user_path, dir_path):
        abort(400, description="Invalid directory path")

    os.makedirs(dir_path, exist_ok=True)

    logger.log("info",f"{username} created directory {dirname}")
    return jsonify({"status": "Directory created", "path": dir_path})

# Smazání adresáře
@app.route("/delete-directory", methods=["POST"])
@limiter.limit("5 per minute") #DoS
def delete_directory():
    username = request.headers.get("X-Username")
    if not username:
        abort(401, description="Missing username header")

    data = request.json
    dirname = data.get("dirname")

    user_path = user_dir(username)
    dir_path = os.path.abspath(os.path.join(user_path, dirname))

    if not is_safe_path(user_path, dir_path) or not os.path.isdir(dir_path):
        abort(400, description="Invalid directory path")

    shutil.rmtree(dir_path)
    logger.log("info",f"{username} deleted directory {dirname}")
    return jsonify({"status": "Directory deleted"})

# Přejmenování souboru nebo adresáře
@app.route("/rename", methods=["POST"])
@limiter.limit("5 per minute") #DoS
def rename():
    username = request.headers.get("X-Username")
    if not username:
        abort(401, description="Missing username header")

    data = request.json
    old_name = data.get("old_name")
    new_name = data.get("new_name")

    user_path = user_dir(username)
    old_path = os.path.abspath(os.path.join(user_path, old_name))
    new_path = os.path.abspath(os.path.join(user_path, new_name))

    if not is_safe_path(user_path, old_path) or not is_safe_path(user_path, new_path):
        abort(400, description="Invalid path")

    os.rename(old_path, new_path)
    logger.log("info",f"{username} renamed file {old_name} to {new_name}")
    return jsonify({"status": "Renamed", "from": old_path, "to": new_path})

# Vypsání obsahu adresáře
@app.route("/list-dir", methods=["GET"])
@limiter.limit("5 per minute") #DoS
def list_dir():
    username = request.headers.get("X-Username")
    if not username:
        abort(401, description="Missing username header")

    rel_path = request.args.get("path", "")
    user_path = user_dir(username)
    target_path = os.path.abspath(os.path.join(user_path, rel_path))

    if not is_safe_path(user_path, target_path) or not os.path.isdir(target_path):
        abort(400, description="Invalid directory path")

    items = []
    for item in os.listdir(target_path):
        item_path = os.path.abspath(os.path.join(target_path, item))
        if os.path.isdir(item_path):
            item_type = "directory"
        elif os.path.isfile(item_path):
            item_type = "file"
        else:
            item_type = "other"  
        items.append({"name": item, "type": item_type})

    return jsonify({"content": items})

# Čtení obsahu souboru
@app.route("/read-file", methods=["GET"])
@limiter.limit("5 per minute") #DoS
def read_file():
    username = request.headers.get("X-Username")
    if not username:
        abort(401, description="Missing username header")

    rel_path = request.args.get("file_path")
    user_path = user_dir(username)
    file_path = os.path.abspath(os.path.join(user_path, rel_path))

    if not is_safe_path(user_path, file_path) or not os.path.isfile(file_path):
        abort(400, description="Invalid file path")

    with open(file_path, "r") as f:
        content = f.read()
    
    logger.log("info",f"{username} read file {file_path}")

    return jsonify({"content": content})

# Funkce pro ověřování existence adresářů
@app.route("/check-directory", methods=["GET"])
def check_directory():
    username = request.headers.get("X-Username")
    if not username:
        abort(401, description="Missing username header")

    rel_path = request.args.get("path", "")
    user_path = user_dir(username)
    target_path = os.path.abspath(os.path.join(user_path, rel_path))

    if not is_safe_path(user_path, target_path):
        abort(400, description="Invalid path")

    exists = os.path.isdir(target_path)
    return jsonify({"exists": exists})

if __name__ == "__main__":
    app.run(ssl_context=('server-cert.crt', 'privkey.pem'), host='127.0.0.1', port=8000) # Spuštení serveru s platným TLS certifikátem