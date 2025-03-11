import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import requests
import base64
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import unpad
from utils.modules import setup_logging
import logging

setup_logging()

#Pro stahování souborů ze serveru
class Download:
    def __init__(self, server_url):
        self.server_url = server_url
        
    def request_file(self, file_path):
        """ Pošle požadavek na server pro daný soubor """
        # Posíláme GET požadavek se souborem
        response = requests.get(f"{self.server_url}/get-file", params={"file_path": file_path})
        
        if response.status_code == 200:
            # Pokud server vrátí soubor, dekódujeme zašifrované soubory a AES klíč
            encrypted_file = base64.b64decode(response.json()["encrypted_file"])
            encrypted_aes_key = base64.b64decode(response.json()["encrypted_aes_key"])
            iv = base64.b64decode(response.json()["iv"])
            
            # Dešifrujeme AES klíč pomocí RSA
            decrypted_aes_key = self.decrypt_aes_key(encrypted_aes_key)

            # Dešifrujeme soubor pomocí AES
            decrypted_file = self.decrypt_file(decrypted_aes_key, encrypted_file, iv)

            # Uložíme dešifrovaný soubor
            self.save_file(decrypted_file, file_path)
        else:
            logging.error(f"Chyba při získávání souboru: {response.status_code}")

    def decrypt_aes_key(self, encrypted_aes_key):
        """ Dešifruje AES klíč pomocí RSA """
        # Získání soukromého RSA klíče (ve skutečné aplikaci by měl být chráněn)
        private_key = RSA.import_key(open("private_key.pem").read())
        cipher_rsa = PKCS1_OAEP.new(private_key)
        decrypted_aes_key = cipher_rsa.decrypt(encrypted_aes_key)
        return decrypted_aes_key

    def decrypt_file(self, aes_key, encrypted_file, iv):
        """ Dešifruje soubor pomocí AES """
        cipher_aes = AES.new(aes_key, AES.MODE_CBC, iv)
        decrypted_file = unpad(cipher_aes.decrypt(encrypted_file), AES.block_size)
        return decrypted_file

    def save_file(self, file_data, file_path):
        """ Uloží dešifrovaný soubor na disk """
        with open(f"decrypted_{file_path}", "wb") as f:
            f.write(file_data)
        logging.info(f"File {file_path} downloaded as 'decrypted_{file_path}'.")


# Pro testování
if __name__ == "__main__":

    down = Download("http://127.0.0.1:8000")
    down.request_file("sample.txt")