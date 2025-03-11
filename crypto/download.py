import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import requests
import base64
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import unpad, pad
from utils.modules import setup_logging
import logging

setup_logging()

class Download:
    def __init__(self, server_url):
        self.server_url = server_url

    def request_file(self, file_path):
        response = requests.get(f"{self.server_url}/get-file", params={"file_path": file_path})
        
        if response.status_code == 200:
            encrypted_file = base64.b64decode(response.json()["encrypted_file"])
            encrypted_aes_key = base64.b64decode(response.json()["encrypted_aes_key"])
            iv = base64.b64decode(response.json()["iv"])
            
            decrypted_aes_key = self.decrypt_aes_key(encrypted_aes_key)
            decrypted_file = self.decrypt_file(decrypted_aes_key, encrypted_file, iv)
            self.save_file(decrypted_file, file_path)
        else:
            logging.fatal(f"Unable to obtain: {response.status_code}")

    def decrypt_aes_key(self, encrypted_aes_key):
        private_key = RSA.import_key(open("client_private_key.pem").read())
        cipher_rsa = PKCS1_OAEP.new(private_key)
        return cipher_rsa.decrypt(encrypted_aes_key)

    def decrypt_file(self, aes_key, encrypted_file, iv):
        cipher_aes = AES.new(aes_key, AES.MODE_CBC, iv)
        return unpad(cipher_aes.decrypt(encrypted_file), AES.block_size)

    def save_file(self, file_data, file_path):
        with open(f"decrypted_{file_path}", "wb") as f:
            f.write(file_data)
        logging.info(f"File {file_path} downloaded as 'decrypted_{file_path}'.")

if __name__ == "__main__":
    down = Download("http://127.0.0.1:8000")
    down.request_file("sample.txt")