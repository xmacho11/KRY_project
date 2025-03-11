from flask import Flask, request, jsonify
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.Util.Padding import pad
import base64
import os

app = Flask(__name__)

# Funkce pro uložení klíče do souboru
def save_keys():
    private_key = RSA.generate(2048)
    public_key = private_key.publickey()

    # Uložení soukromého klíče
    with open("private_key.pem", "wb") as private_file:
        private_file.write(private_key.export_key())

    # Uložení veřejného klíče
    with open("public_key.pem", "wb") as public_file:
        public_file.write(public_key.export_key())

    return private_key, public_key

# Funkce pro načtení soukromého klíče
def load_private_key():
    with open("private_key.pem", "rb") as private_file:
        private_key = RSA.import_key(private_file.read())
    return private_key

# Funkce pro načtení veřejného klíče
def load_public_key():
    with open("public_key.pem", "rb") as public_file:
        public_key = RSA.import_key(public_file.read())
    return public_key

# Při spuštění aplikace
if not os.path.exists("private_key.pem"):
    private_key, public_key = save_keys()
else:
    private_key = load_private_key()
    public_key = load_public_key()

# Cesta k souborům, které může server poskytovat
BASE_FILE_PATH = "./server_files/"

@app.route("/public-key", methods=["GET"])
def get_public_key():
    """ Vrátí veřejný klíč pro šifrování AES klíče """
    return jsonify({"public_key": public_key.export_key().decode()})

@app.route("/upload", methods=["POST"])
def receive_encrypted_file():
    """ Přijme zašifrovaný AES klíč a soubor, dešifruje ho a uloží """
    data = request.json
    encrypted_aes_key = base64.b64decode(data["encrypted_aes_key"])
    encrypted_file = base64.b64decode(data["encrypted_file"])

    # Dešifrování AES klíče pomocí RSA
    cipher_rsa = PKCS1_OAEP.new(private_key)
    aes_key = cipher_rsa.decrypt(encrypted_aes_key)

    # Dešifrování souboru AES
    nonce, ciphertext = encrypted_file[:16], encrypted_file[16:]
    cipher_aes = AES.new(aes_key, AES.MODE_EAX, nonce=nonce)
    decrypted_file = cipher_aes.decrypt(ciphertext)

    # Uložení souboru
    with open("received_decrypted_file.txt", "wb") as f:
        f.write(decrypted_file)

    return jsonify({"status": "File decrypted and saved successfully!"})

@app.route("/get-file", methods=["GET"])
def get_file():
    """ Odeslání zašifrovaného souboru klientovi """
    # Získání cesty k souboru z parametru URL
    file_path = request.args.get("file_path")
    
    if file_path and os.path.exists(os.path.join(BASE_FILE_PATH, file_path)):
        # Pokud soubor existuje, zašifrujeme ho a pošleme klientovi
        encrypted_file, encrypted_aes_key, iv = encrypt_file(os.path.join(BASE_FILE_PATH, file_path))
        
        # Sestavení odpovědi
        response = {
            "encrypted_file": base64.b64encode(encrypted_file).decode(),
            "encrypted_aes_key": base64.b64encode(encrypted_aes_key).decode(),
            "iv": base64.b64encode(iv).decode()
        }
        
        return response
    else:
        return {"error": "Soubor nebyl nalezen!"}, 404

def encrypt_file(file_path):
    # Generování AES klíče
    aes_key = os.urandom(32)  # AES-256 klíč
    cipher_aes = AES.new(aes_key, AES.MODE_CBC)
    
    with open(file_path, "rb") as f:
        file_data = f.read()
    
    # Zašifrování souboru
    encrypted_file = cipher_aes.encrypt(pad(file_data, AES.block_size))
    
    # Šifrování AES klíče pomocí RSA
    cipher_rsa = PKCS1_OAEP.new(public_key)
    encrypted_aes_key = cipher_rsa.encrypt(aes_key)
    
    # Vrátí šifrovaný soubor a šifrovaný AES klíč
    return encrypted_file, encrypted_aes_key, cipher_aes.iv

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)
