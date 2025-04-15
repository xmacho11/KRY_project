import requests
import os

class ClientFileManager:
    def __init__(self, server_url, username, cert_path="server-cert.crt"):
        self.server_url = server_url.rstrip('/')
        self.username = username
        self.headers = {"X-Username": self.username}
        self.cert_path = cert_path
        self.cwd = ""  # aktuální pracovní adresář (relativní k uživatelskému rootu)

    def change_directory(self, new_dir):
        """ Změní aktuální pracovní adresář pokud existuje """
        try:
            path = os.path.normpath(os.path.join(self.cwd, new_dir))
            content = self.list_directory(path)  # ověření existence
            self.cwd = path
            return f"Changed directory to: /{self.cwd}" if self.cwd else "Changed to root directory"
        except Exception as e:
            return f"Chyba: {e}"

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
        return response.json()["content"]

    def create_file(self, filename, content=""):
        full_path = os.path.normpath(os.path.join(self.cwd, filename))
        data = {"filename": full_path, "content": content}
        response = requests.post(f"{self.server_url}/create-file", json=data, headers=self.headers, verify=self.cert_path)
        return response.json()

    def delete_file(self, filename):
        full_path = os.path.normpath(os.path.join(self.cwd, filename))
        data = {"filename": full_path}
        response = requests.post(f"{self.server_url}/delete-file", json=data, headers=self.headers, verify=self.cert_path)
        return response.json()

    def edit_file(self, filename, new_content):
        full_path = os.path.normpath(os.path.join(self.cwd, filename))
        data = {"filename": full_path, "content": new_content}
        response = requests.post(f"{self.server_url}/edit-file", json=data, headers=self.headers, verify=self.cert_path)
        return response.json()

    def create_directory(self, dirname):
        full_path = os.path.normpath(os.path.join(self.cwd, dirname))
        data = {"dirname": full_path}
        response = requests.post(f"{self.server_url}/create-directory", json=data, headers=self.headers, verify=self.cert_path)
        return response.json()

    def delete_directory(self, dirname):
        full_path = os.path.normpath(os.path.join(self.cwd, dirname))
        data = {"dirname": full_path}
        response = requests.post(f"{self.server_url}/delete-directory", json=data, headers=self.headers, verify=self.cert_path)
        return response.json()

    def rename(self, old_name, new_name):
        old_full_path = os.path.normpath(os.path.join(self.cwd, old_name))
        new_full_path = os.path.normpath(os.path.join(self.cwd, new_name))
        data = {"old_name": old_full_path, "new_name": new_full_path}
        response = requests.post(f"{self.server_url}/rename", json=data, headers=self.headers, verify=self.cert_path)
        return response.json()
