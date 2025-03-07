import sql as sql
import sys
from auth import Authenticator2FA

var = ""
registered = False

def input_list(input):
    commands = {
        "q": "exit",
        "y": "yes",
        "n": "no"
    }
    return commands.get(input,"NaN")

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
        pswd = input("Enter your password: ")
        otp = input("Enter your TOTP code: ")
        if auth.authenticate(username,pswd,otp):
            print("Logging in ... ")
            break
        else:
            print("Authentication failed! Exiting ... ")
            break

sys.exit()
