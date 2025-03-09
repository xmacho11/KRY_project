import os
import utils.sql as sql
from utils.modules import setup_logging, protect_file
from utils.ui import *
import logging

setup_logging()

def setup_client(logs_path="./logs/"):

    try:    
        if not os.path.exists("users.db"):
            logging.warning("Database not found!")
            sql.create_database()


        log_file_path = os.path.join(logs_path, "log.txt")
        if not os.path.exists(log_file_path):
            os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
    except:
        logging.fatal("Client setup failed!")
    else:
        logging.info("Client setup succesful!")
        welcome_screen()