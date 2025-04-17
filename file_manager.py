import requests
import os
import logging
from utils.modules import setup_logging
import json

setup_logging()

# Třída pro manipulaci se soubory
class ClientFileManager:
    def __init__(self, server_url, username, cert_path="server-cert.crt"):
        self.server_url = server_url.rstrip('/')
        self.username = username
        self.headers = {"X-Username": self.username}
        self.cert_path = cert_path
        self.cwd = ""  # aktuální adresář 

    def change_directory(self, new_dir):
        """ Změní aktuální pracovní adresář pokud existuje """
        path = os.path.normpath(os.path.join(self.cwd, new_dir))
        try:
            if self.check_directory(path):
                self.cwd = path
                return f"Changed directory to: /{self.cwd}" if self.cwd else "Changed to root directory"
            else:
                return f"Error: directory '{path}' doesn't exist"
        except:
            return f"Invalid change directory"
    
    # API funkce (viz server.py)
    def check_directory(self, path):
        """ Ověří zda daný adresář existuje na serveru """
        params = {"path": path}
        response = requests.get(f"{self.server_url}/check-directory", params=params, headers=self.headers, verify=self.cert_path)
        response.raise_for_status()
        result = response.json()
        return result["exists"]

    def list_directory(self, path=""):
        params = {"path": self.cwd}
        response = requests.get(f"{self.server_url}/list-dir", params=params, headers=self.headers, verify=self.cert_path)
        response.raise_for_status()
        return response.json()["content"]

    def read_file(self, file_path):
        full_path = os.path.normpath(os.path.join(self.cwd, file_path))
        params = {"file_path": full_path}
        response = requests.get(f"{self.server_url}/read-file", params=params, headers=self.headers, verify=self.cert_path)
        response.raise_for_status()
        logging.info(f"{file_path}: {json.dumps(response.json(), indent=2)}")
        return response.json()["content"]

    def create_file(self, filename, content=""):
        full_path = os.path.normpath(os.path.join(self.cwd, filename))
        data = {"filename": full_path, "content": content}
        response = requests.post(f"{self.server_url}/create-file", json=data, headers=self.headers, verify=self.cert_path)
        logging.info(f"{filename}: {json.dumps(response.json(), indent=2)}")
        return response.json()

    def delete_file(self, filename):
        full_path = os.path.normpath(os.path.join(self.cwd, filename))
        data = {"filename": full_path}
        response = requests.post(f"{self.server_url}/delete-file", json=data, headers=self.headers, verify=self.cert_path)
        logging.info(f"{filename}: {json.dumps(response.json(), indent=2)}")
        return response.json()

    def edit_file(self, filename, new_content):
        full_path = os.path.normpath(os.path.join(self.cwd, filename))
        data = {"filename": full_path, "content": new_content}
        response = requests.post(f"{self.server_url}/edit-file", json=data, headers=self.headers, verify=self.cert_path)
        logging.info(f"{filename}: {json.dumps(response.json(), indent=2)}")
        return response.json()

    def create_directory(self, dirname):
        full_path = os.path.normpath(os.path.join(self.cwd, dirname))
        data = {"dirname": full_path}
        response = requests.post(f"{self.server_url}/create-directory", json=data, headers=self.headers, verify=self.cert_path)
        logging.info(f"{dirname}: {json.dumps(response.json(), indent=2)}")
        return response.json()

    def delete_directory(self, dirname):
        full_path = os.path.normpath(os.path.join(self.cwd, dirname))
        data = {"dirname": full_path}
        response = requests.post(f"{self.server_url}/delete-directory", json=data, headers=self.headers, verify=self.cert_path)
        logging.info(f"{dirname}: {json.dumps(response.json(), indent=2)}")
        return response.json()

    def rename(self, old_name, new_name):
        old_full_path = os.path.normpath(os.path.join(self.cwd, old_name))
        new_full_path = os.path.normpath(os.path.join(self.cwd, new_name))
        data = {"old_name": old_full_path, "new_name": new_full_path}
        response = requests.post(f"{self.server_url}/rename", json=data, headers=self.headers, verify=self.cert_path)
        logging.info(f"{old_name}: {json.dumps(response.json(), indent=2)}")
        return response.json()