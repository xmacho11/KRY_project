import os
import logging

# Nastavení formátu logování (pro klienta)
def setup_logging(log_dir="./logs/"):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logging.basicConfig(
        level=logging.INFO,  
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%m/%d/%Y %H:%M:%S", 
        handlers=[logging.FileHandler(log_dir + "client_log.txt")]
    )