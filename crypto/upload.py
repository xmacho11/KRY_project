import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import base64
import logging
import requests
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.Util.Padding import pad
from utils.modules import setup_logging


setup_logging()


class Upload:
    def __init__(self, server_url, cert_path="cert.pem"):
        self.server_url = server_url
        self.cert_path = cert_path  # cesta k certifikátu serveru
        self.aes_key = os.urandom(32)  # 256-bit AES key

    def get_server_public_key(self):
        """ Získání veřejného RSA klíče serveru s ověřením certifikátu """
        try:
            response = requests.get(f"{self.server_url}/public-key", verify=self.cert_path)
            response.raise_for_status()
            public_key_data = response.json()["public_key"]
            return RSA.import_key(public_key_data)
        except Exception as e:
            logging.fatal(f"Unable to obtain server public key: {e}")
            return None

    def encrypt_aes(self, file_data):
        """ Šifrování souboru pomocí AES """
        cipher_aes = AES.new(self.aes_key, AES.MODE_CBC)
        ciphertext = cipher_aes.encrypt(pad(file_data, AES.block_size))
        return ciphertext, cipher_aes.iv

    def encrypt_aes_key(self, public_key):
        """ Šifrování AES klíče pomocí veřejného RSA klíče serveru """
        cipher_rsa = PKCS1_OAEP.new(public_key)
        return cipher_rsa.encrypt(self.aes_key)

    def send_file(self, file_path):
        """ Odeslání zašifrovaného souboru a AES klíče na server """
        if not os.path.exists(file_path):
            logging.error(f"File {file_path} not found!")
            return

        with open(file_path, "rb") as f:
            file_data = f.read()

        public_key = self.get_server_public_key()
        if not public_key:
            return

        encrypted_file, iv = self.encrypt_aes(file_data)
        encrypted_aes_key = self.encrypt_aes_key(public_key)

        try:
            response = requests.post(
                f"{self.server_url}/upload",
                json={
                    "encrypted_aes_key": base64.b64encode(encrypted_aes_key).decode(),
                    "encrypted_file": base64.b64encode(encrypted_file).decode(),
                    "iv": base64.b64encode(iv).decode()
                },
                verify=self.cert_path  # Ověření certifikátu serveru
            )
            response.raise_for_status()
            logging.info(response.json())
        except Exception as e:
            logging.error(f"Failed to upload file: {e}")


if __name__ == "__main__":
    uploader = Upload("https://127.0.0.1:8000", cert_path="server-cert.crt")
    uploader.send_file("test.txt")
