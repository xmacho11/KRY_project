import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import requests
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.Util.Padding import pad
import base64
import logging
from utils.modules import setup_logging

setup_logging()

# Pro šifrování souborů odesílaných na server
class Upload:
    def __init__(self, server_url):
        self.server_url = server_url
        self.aes_key = os.urandom(32)  # Použití 256bitového AES klíče

    def get_server_public_key(self):
        """ Získání veřejného RSA klíče serveru """
        response = requests.get(f"{self.server_url}/public-key")
        if response.status_code == 200:
            public_key_data = response.json()["public_key"]
            return RSA.import_key(public_key_data)
        else:
            logging.fatal("Unable to obtain server public key!")
            return None

    def encrypt_aes(self, file_data):
        """ Šifrování souboru pomocí AES """
        cipher_aes = AES.new(self.aes_key, AES.MODE_CBC)
        ciphertext = cipher_aes.encrypt(pad(file_data, AES.block_size))
        return ciphertext, cipher_aes.iv  # Vrátí šifrovaná data a IV

    def encrypt_aes_key(self, public_key):
        """ Šifrování AES klíče pomocí veřejného RSA klíče serveru """
        cipher_rsa = PKCS1_OAEP.new(public_key)
        return cipher_rsa.encrypt(self.aes_key)

    def send_file(self, file_path):
        """ Odeslání zašifrovaného souboru a AES klíče na server """
        with open(file_path, "rb") as f:
            file_data = f.read()
        
        public_key = self.get_server_public_key()
        if not public_key:
            return

        encrypted_file, iv = self.encrypt_aes(file_data)
        encrypted_aes_key = self.encrypt_aes_key(public_key)

        response = requests.post(
            f"{self.server_url}/upload",
            json={
                "encrypted_aes_key": base64.b64encode(encrypted_aes_key).decode(),
                "encrypted_file": base64.b64encode(encrypted_file).decode(),
                "iv": base64.b64encode(iv).decode()
            }
        )

        logging.info(response.json())

# Pro testování
if __name__ == "__main__":
    up = Upload("http://127.0.0.1:8000")
    up.send_file("test.txt")