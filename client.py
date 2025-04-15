import utils.sql as sql
import sys
from auth import Authenticator2FA
from utils.setup import setup_client
from utils.modules import setup_logging
import logging
import pwinput as pw
import socket
from file_manager import ClientFileManager
from utils.ui import show_menu
import crypto.download as down
import crypto.upload as up

server = "https://127.0.0.1:8000"
certificate = "server-cert.crt"
setup_logging()

def input_list(input):
    commands = {
        "q": "exit",
        "y": "yes",
        "n": "no",
        "cf": "create_file",
        "e": "edit_file",
        "df": "delete_file",
        "cd": "create_dir",
        "dd": "delete_dir",
        "r": "rename",
        "up": "upload",
        "dw": "download",
        "ls": "list_dir",
        "show": "read_file",
        "md": "change_dir",
        "help": "help"
    }
    return commands.get(input, "none")


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
                break
            
    if registered:
        while True:
            pswd = pw.pwinput("Enter your password: ")
            otp = input("Enter your TOTP code: ")
            if not auth.authenticate(username,pswd,otp):
                break
            else:
                auth.send_public_key(server)
                print("Authenticated!")

                # Inicializace klienta s předáním username
                client = ClientFileManager(server, auth.get_username(), certificate)
                show_menu()
                while True:
                    var = input(f"\n./{client.cwd} > ")
                    command = input_list(var)

                    match command:
                        case "create_file":
                            filename = input("Filename: ")
                            content = input("Content: ")
                            print(client.create_file(filename, content))

                        case "edit_file":
                            filename = input("Filename: ")
                            content = input("Nový obsah: ")
                            print(client.edit_file(filename, content))

                        case "delete_file":
                            filename = input("Filename: ")
                            print(client.delete_file(filename))

                        case "create_dir":
                            dirname = input("Directory: ")
                            print(client.create_directory(dirname))

                        case "delete_dir":
                            dirname = input("Directory: ")
                            print(client.delete_directory(dirname))

                        case "rename":
                            old_name = input("Filename: ")
                            new_name = input("New Filename: ")
                            print(client.rename(old_name, new_name))
                        
                        case "download":
                            filename = input("File name: ")
                            downloader = down.Download(server, username, certificate)
                            downloader.request_file(filename)

                        case "upload":
                            filepath = input("Filepath: ")  # interaktivní nebo předej z autentizace
                            uploader = up.Upload(server, username, certificate)
                            uploader.send_file(filepath)

                        case "list_dir":
                            try:
                                content = client.list_directory()
                                print(f"\nContents> /{client.cwd or '.'}:")
                                for item in content:
                                    symbol = "[DIR]" if item["type"] == "directory" else "     "
                                    print(f"{symbol} {item['name']}")
                            except Exception as e:
                                print(f"Error: {e}")

                        case "read_file":
                            file_path = input("Path (relative): ")
                            try:
                                content = client.read_file(file_path)
                                print("\nContent:")
                                print(content)
                            except Exception as e:
                                print(f"Error:: {e}")

                        case "change_dir":
                            new_dir = input("Path (relative): ")
                            result = client.change_directory(new_dir)
                            print(result)
                        
                        case "help":
                            show_menu()

                        case "exit":
                            break

                        case _:
                            print("Invalid Command")
                break              
    sys.exit(logging.info("Exitting client"))

if __name__=="__main__":
    setup_client()
    main()
