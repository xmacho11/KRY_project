import utils.sql as sql
import sys
from auth import Authenticator2FA
from utils.setup import setup_client
from utils.modules import setup_logging
import logging
import pwinput as pw
import socket

setup_logging()

def input_list(input):
    commands = {
        "q": "exit",
        "y": "yes",
        "n": "no"
    }
    return commands.get(input,"none")

def main():
    var = ""
    registered = False
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)

    while input_list(var) != "exit":
        var = input("Enter your username: ")
        username = var
        if sql.check_user_exists(username):
            auth = Authenticator2FA(0,username,hostname,ip_address)
            registered = True
            break

        else:
            var = input("Username doesn't exist! Wish to register? [y] yes [any] cancel [q] quit : ")
            if input_list(var) == "yes":
                auth = Authenticator2FA(0,username,hostname,ip_address)
                var = pw.pwinput("Enter your password: ")
                sql.register_user(username, auth.hash_password(var), auth.keygen())
                registered = True
            
    if registered:
        while True:
            pswd = pw.pwinput("Enter your password: ")
            otp = input("Enter your TOTP code: ")
            if not auth.authenticate(username,pswd,otp):
                break
            else:
                auth.send_public_key("http://127.0.0.1:8000") # zaslání veřejného klíče klienta serveru
                # Předání username serveru pomocí auth.get_username()
                # Tady se spustí file manager klient, který bude pomocí GET a POST požadavků komunikovat se serverem
                print("TODO: file manager")
                break

    sys.exit(logging.info("Exiting client"))

if __name__=="__main__":
    setup_client()
    main()
