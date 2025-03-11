import bcrypt
import pyotp
import utils.sql as sql
import qrcode
import os
from utils.modules import setup_logging
import logging

setup_logging()
class Authenticator2FA:

    def __init__(self, session, name, issuer_name, ip_addr):
        self.session = session
        self.name = name
        self.issuer_name = issuer_name
        self.ip_addr = ip_addr
        logging.warning(f"User {name} wish to authenticate in session {session} via device {issuer_name} ({ip_addr}).")

    def get_username(self):
        return self.name
    
    def get_ip(self):
        return self.ip_addr
    
    @staticmethod
    def hash_password(password):
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode(), salt).decode("utf-8")

    @staticmethod
    def verify_password(stored_hash, password):
        return bcrypt.checkpw(password.encode(), stored_hash.encode("utf-8"))

    def keygen(self):
        secret = pyotp.random_base32()
        self.qrgen(secret)
        return secret  

    def qrgen(self, secret):
        uri = pyotp.totp.TOTP(secret).provisioning_uri(self.name, self.issuer_name)
        
        qr = qrcode.make(uri)
        
        qr_path = "qrcode.png"
        qr.save(qr_path)
        os.system(qr_path)  

        logging.warning("Please scan opened QR code in your Google Authenticator app.")

    @staticmethod
    def verify_otp(secret, user_code):
        totp = pyotp.TOTP(secret)
        return totp.verify(user_code)

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
