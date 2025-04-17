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
import os

server = "https://127.0.0.1:8000"
certificate = "server-cert.crt"
setup_logging()

def parse_input(input_str):
    parts = input_str.strip().split()
    if not parts:
        return None, []
    return parts[0], parts[1:]


# Hlavní metoda
def main():
    var = ""
    registered = False
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)

    while True:
        user_input = input()
        command, args = parse_input(user_input)

        if command == "exit" or command == "q":
            break

        var = input("Enter your username: ")
        username = var
        if sql.check_user_exists(username): # Volání Query pro ověření existence uživatelského jména v databázi
            auth = Authenticator2FA(username,hostname,ip_address) # Vytvoření objektu autentizátoru
            registered = True
            break

        else:
            var = input("Username doesn't exist! Wish to register? [y] yes [any] quit : ")
            if var == "y":
                auth = Authenticator2FA(username,hostname,ip_address)  # Vytvoření objektu autentizátoru
                var = pw.pwinput("Enter your password: ")
                sql.register_user(username, auth.hash_password(var), auth.keygen()) # Registrace nového uživatele
                registered = True
                break
            else: break
            
            
    if registered: # Přihlašování
        while True:
            pswd = pw.pwinput("Enter your password: ")
            otp = input("Enter your TOTP code: ")
            if not auth.authenticate(username,pswd,otp): # Dvoufázová autentizace
                print("Error : Invalid password or TOTP code.")
                break
            else:
                auth.send_public_key(server) # Zaslání veřejného klíče klienta serveru
                print("Authenticated!")

                
                client = ClientFileManager(server, auth.get_username(), certificate) # Inicializace klienta s předáním username serveru
                show_menu()
                while True: # Loop pro zadávání příkazů
                    user_input = input(f"\n{auth.get_username()}/.{client.cwd} > ")
                    command, args = parse_input(user_input)

                    match command: # Switch příkazů
                        case "touch": # Vytvoření souboru a vložení obsahu
                            if len(args) < 2:
                                print("Usage: create_file <filename> <content>")
                                continue
                            filename, content = args[0], " ".join(args[1:])
                            print(client.create_file(filename, content))

                        case "edit": # Editování souboru
                            if len(args) < 2:
                                print("Usage: edit_file <filename> <new content>")
                                continue
                            filename, content = args[0], " ".join(args[1:])
                            print(client.edit_file(filename, content))

                        case "rmf": # Smazání souboru
                            if len(args) != 1:
                                print("Usage: delete_file <filename>")
                                continue
                            print(client.delete_file(args[0]))

                        case "mkdir": # Vytvoření adresáře
                            if len(args) != 1:
                                print("Usage: create_dir <dirname>")
                                continue
                            print(client.create_directory(args[0]))

                        case "rmd": # Smazání adresáře
                            if len(args) != 1:
                                print("Usage: delete_dir <dirname>")
                                continue
                            print(client.delete_directory(args[0]))

                        case "rename": # Přejmenování souboru nebo adresáře
                            if len(args) != 2:
                                print("Usage: rename <oldname> <newname>")
                                continue
                            print(client.rename(args[0], args[1]))

                        case "down": # Stažení souboru
                            if len(args) != 1:
                                print("Usage: download <filename>")
                                continue
                            downloader = down.Download(server, username, certificate)
                            downloader.request_file(os.path.join(client.cwd, args[0]))

                        case "up": # Nahrání souboru
                            if len(args) != 1:
                                print("Usage: upload <filepath>")
                                continue
                            uploader = up.Upload(server, username, certificate)
                            uploader.send_file(args[0],client.cwd)

                        case "ls": # Zobrazení obsahu adresáře
                            try:
                                content = client.list_directory()
                                print(f"\nContents> {client.cwd or '.'}:")
                                for item in content:
                                    symbol = "[DIR]" if item["type"] == "directory" else "     "
                                    print(f"{symbol} {item['name']}")
                            except Exception as e:
                                print(f"Error: {e}")

                        case "read": # Čtení obsahu souboru
                            if len(args) != 1:
                                print("Usage: read_file <path>")
                                continue
                            try:
                                content = client.read_file(args[0])
                                print("\nContent:")
                                print(content)
                            except Exception as e:
                                print(f"Error: {e}")

                        case "cd": # Pohyb mezi adresáři
                            if len(args) != 1:
                                print("Usage: change_dir <path>")
                                continue
                            result = client.change_directory(args[0])
                            print(result)

                        case "help": # Vypsání nápovědy
                            show_menu()

                        case "exit": # Ukončení klienta
                            break

                        case _:
                            print("Invalid command. Type 'help' for command list.")

                break              

if __name__=="__main__":
    setup_client()
    main()
