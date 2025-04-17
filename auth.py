import bcrypt
import pyotp
import utils.sql as sql
import qrcode
import os
from utils.modules import setup_logging
import logging
import requests
import subprocess

setup_logging()
class Authenticator2FA:

    def __init__(self, name, issuer_name = "unknown", ip_addr = "unknown"):
        self.name = name
        self.issuer_name = issuer_name
        self.ip_addr = ip_addr
        logging.warning(f"User {name} wish to authenticate via device {issuer_name} ({ip_addr}).")

    # Getter pro username
    def get_username(self):
        return self.name
    
    # Getter pro IP klienta
    def get_ip(self):
        return self.ip_addr
    
    # Hašování
    @staticmethod
    def hash_password(password):
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode(), salt).decode("utf-8")

    # Porovnání hašů
    @staticmethod
    def verify_password(stored_hash, password):
        return bcrypt.checkpw(password.encode(), stored_hash.encode("utf-8"))

    # Generování TOTP klíče formou QR kódu
    def keygen(self):
        secret = pyotp.random_base32()
        self.qrgen(secret)
        return secret  

    # Vytvoření QR kódu
    def qrgen(self, secret):
        uri = pyotp.totp.TOTP(secret).provisioning_uri(self.name, self.issuer_name)
        
        qr = qrcode.make(uri)
        
        qr_path = "qrcode.png"
        qr.save(qr_path)
        os.chmod(qr_path, 0o644)
        subprocess.run(["xdg-open", qr_path])

        logging.warning("Please scan opened QR code in your Google Authenticator app.")

    # Výpočet TOTP kódu
    @staticmethod
    def verify_otp(secret, user_code):
        totp = pyotp.TOTP(secret)
        return totp.verify(user_code)

    # Dvoufázová autentizace
    def authenticate(self, username, password, otp_code):
        stored_hash, secret = sql.load_user(username)

        if not self.verify_password(stored_hash, password):
            logging.error("Log in failed: password incorrect!")
            return False
        elif not self.verify_otp(secret, otp_code):
            logging.error("Log in failed: OTP code incorrect!")
            return False
        else:
            logging.info(f"User {username} logged in.")
            return True
    
    # Zaslání veřejného klíče klienta serveru (pro dohodnutí AES klíče a šifrování souborů)
    @staticmethod
    def send_public_key(server_url):
        """ Pošle veřejný klíč serveru, aby ho mohl použít k šifrování zpráv pro klienta """
        with open("client_public_key.pem", "rb") as public_file:
            public_key = public_file.read()

        try:
            response = requests.post(
                f"{server_url}/register-public-key",
                json={"public_key": public_key.decode()},
                verify="server-cert.crt"  # Ověř serverový certifikát
            )
            response.raise_for_status()  # Vyhodí výjimku pokud nenastane 2xx odpověď
            logging.info(response.json())
        except requests.exceptions.SSLError as ssl_error:
            logging.error(f"SSL verification failed: {ssl_error}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error communicating with server: {e}")

