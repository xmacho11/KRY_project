import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import requests
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES
from utils.modules import setup_logging
import base64
import logging

setup_logging()

# Pro šifrování souborů odesílaných na server
class Upload:
    def __init__(self, server_url):
        self.server_url = server_url
        self.aes_key = os.urandom(16)  # Vygenerování náhodného AES klíče (16 bajtů)

    def get_public_key(self):
        """ Získání veřejného RSA klíče ze serveru """
        response = requests.get(f"{self.server_url}/public-key")
        public_key_data = response.json()["public_key"]
        return RSA.import_key(public_key_data)

    def encrypt_aes(self, file_data):
        """ Šifrování souboru pomocí AES """
        cipher_aes = AES.new(self.aes_key, AES.MODE_EAX)
        ciphertext, tag = cipher_aes.encrypt_and_digest(file_data)
        return cipher_aes.nonce + ciphertext  # Připojení nonce k zašifrovaným datům

    def encrypt_aes_key(self):
        """ Šifrování AES klíče pomocí veřejného RSA klíče """
        public_key = self.get_public_key()
        cipher_rsa = PKCS1_OAEP.new(public_key)
        return cipher_rsa.encrypt(self.aes_key)

    def send_file(self, file_path):
        """ Odeslání zašifrovaného souboru a AES klíče na server """
        with open(file_path, "rb") as f:
            file_data = f.read()

        encrypted_file = self.encrypt_aes(file_data)
        encrypted_aes_key = self.encrypt_aes_key()

        response = requests.post(
            f"{self.server_url}/upload",
            json={
                "encrypted_aes_key": base64.b64encode(encrypted_aes_key).decode(),
                "encrypted_file": base64.b64encode(encrypted_file).decode()
            }
        )

        logging.info(response.json())

# Pro testování
if __name__ == "__main__":

    up = Upload("http://127.0.0.1:8000")
    up.send_file("test.txt")
