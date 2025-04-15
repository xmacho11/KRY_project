import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import base64
import logging
import requests
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import unpad
from utils.modules import setup_logging
setup_logging()


class Download:
    def __init__(self, server_url, username, cert_path="server-cert.crt"):
        self.server_url = server_url
        self.username = username
        self.cert_path = cert_path  # Cesta k certifikátu serveru

    def request_file(self, file_path):
        """ Požádá server o soubor a ověří certifikát """
        try:
            headers = {"X-Username": self.username}
            response = requests.get(
                f"{self.server_url}/get-file",
                params={"file_path": file_path},
                headers=headers,               
                verify=self.cert_path          # Ověření certifikátu serveru
            )
            response.raise_for_status()

            data = response.json()
            encrypted_file = base64.b64decode(data["encrypted_file"])
            encrypted_aes_key = base64.b64decode(data["encrypted_aes_key"])
            iv = base64.b64decode(data["iv"])

            decrypted_aes_key = self.decrypt_aes_key(encrypted_aes_key)
            decrypted_file = self.decrypt_file(decrypted_aes_key, encrypted_file, iv)
            self.save_file(decrypted_file, file_path)

        except Exception as e:
            logging.fatal(f"Unable to download file: {e}")

    def decrypt_aes_key(self, encrypted_aes_key):
        """ Dešifrování AES klíče pomocí soukromého RSA klíče klienta """
        private_key = RSA.import_key(open("client_private_key.pem").read())
        cipher_rsa = PKCS1_OAEP.new(private_key)
        return cipher_rsa.decrypt(encrypted_aes_key)

    def decrypt_file(self, aes_key, encrypted_file, iv):
        """ Dešifrování souboru pomocí AES """
        cipher_aes = AES.new(aes_key, AES.MODE_CBC, iv)
        return unpad(cipher_aes.decrypt(encrypted_file), AES.block_size)

    def save_file(self, file_data, file_path):
        """ Uložení dešifrovaného souboru """
        output_path = f"{file_path}"
        with open(output_path, "wb") as f:
            f.write(file_data)
        logging.info(f"File {file_path} downloaded and saved as '{output_path}'.")


if __name__ == "__main__":
    username = input("Zadej username: ")  # interaktivní nebo předej z autentizace
    downloader = Download("https://127.0.0.1:8000", username, cert_path="server-cert.crt")
    downloader.request_file("sample.txt")