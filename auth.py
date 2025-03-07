import bcrypt
import pyotp
import sql as sql
import qrcode
import os

class Authenticator2FA:

    def __init__(self, session, name, issuer_name):
        self.session = session
        self.name = name
        self.issuer_name = issuer_name

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

        print("Please scan opened QR code in your Google Authenticator app.")


    @staticmethod
    def verify_otp(secret, user_code):
        totp = pyotp.TOTP(secret)
        return totp.verify(user_code)

    def authenticate(self, username, password, otp_code):
        stored_hash, secret = sql.load_user(username)

        # 1. Ověření
        if not self.verify_password(stored_hash, password):
            print("spatne heslo")
            return False
        elif not self.verify_otp(secret, otp_code):
            print("spatne totp")
            return False
        else:
            return True
