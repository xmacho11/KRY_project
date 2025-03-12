import os
import logging

def setup_logging(log_dir="./logs/"):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logging.basicConfig(
        level=logging.INFO,  
        format="%(asctime)s - %(levelname)s - %(message)s", 
        handlers=[logging.FileHandler(log_dir + "log.txt"), logging.StreamHandler()]
    )