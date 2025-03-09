import os
import logging
import ctypes

def setup_logging(log_dir="./logs/"):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logging.basicConfig(
        level=logging.INFO,  
        format="%(asctime)s - %(levelname)s - %(message)s", 
        handlers=[logging.FileHandler(log_dir + "log.txt"), logging.StreamHandler()]
    )

def protect_file(file_path):
    FILE_ATTRIBUTE_READONLY = 0x01
    ctypes.windll.kernel32.SetFileAttributesW(file_path, FILE_ATTRIBUTE_READONLY)