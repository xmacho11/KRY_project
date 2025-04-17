import os
import utils.sql as sql
from utils.modules import setup_logging
from Crypto.PublicKey import RSA
from utils.ui import *
import logging
import os

setup_logging()

# Třída pro inicializaci programu při spuštění
def setup_client(logs_path="./logs/"):

    # Pokud databáze neexistuje, je vytvořena
    try:    
        if not os.path.exists("users.db"):
            logging.warning("Database not found! Creating new users database.")
            sql.create_database()


        log_file_path = os.path.join(logs_path, "log.txt")
        if not os.path.exists(log_file_path):
            os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
        
        # Generování klíčů, pokud neexistují
        if not os.path.exists("client_private_key.pem"):
            generate_keys()
        
    except:
        logging.fatal("Client setup failed!")
    else:
        logging.info("Client setup succesfull!")
        welcome_screen()

def generate_keys():
    """ Generuje pár RSA klíčů pro klienta a uloží je do souborů """
    private_key = RSA.generate(2048)
    public_key = private_key.publickey()

    with open("client_private_key.pem", "wb") as private_file:
        private_file.write(private_key.export_key())

    with open("client_public_key.pem", "wb") as public_file:
        public_file.write(public_key.export_key())

    logging.info("RSA keys generated.")
