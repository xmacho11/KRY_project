import utils.sql as sql
import sys
from auth import Authenticator2FA
from utils.setup import setup_client
from utils.modules import setup_logging
import logging
import pwinput as pw

setup_logging()

def input_list(input):
    commands = {
        "q": "exit",
        "y": "yes",
        "n": "no"
    }
    return commands.get(input,"NaN")

def main():
    var = ""
    registered = False

    while input_list(var) != "exit":
        var = input("Enter your username: ")
        username = var
        if sql.check_user_exists(username):
            auth = Authenticator2FA(0,username,__name__)
            registered = True
            break

        else:
            var = input("Username doesnt exist! Wish to register? [y] yes [any] cancel [q] quit : ")
            if input_list(var) == "yes":
                auth = Authenticator2FA(0,username,__name__)
                var = input("Enter your password: ")
                sql.register_user(username, auth.hash_password(var), auth.keygen())
                registered = True
                break
            
    if registered:
        while True:
            pswd = pw.pwinput("Enter your password: ")
            otp = input("Enter your TOTP code: ")
            if not auth.authenticate(username,pswd,otp):
                break
            break # tady bude volání serveru

    sys.exit(logging.info("Exiting ..."))

if __name__=="__main__":
    setup_client()
    main()
