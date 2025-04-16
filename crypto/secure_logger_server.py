import os
import hashlib
import datetime
import sys

class SecureServerLogger:
    def __init__(self, log_path="./logs/secure_server_log.txt"):
        self.log_path = log_path
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

        if not os.path.exists(log_path):
            genesis_msg = "GENESIS - INIT - System initialized"
            genesis_hash = self.compute_hash(genesis_msg + "0")
            with open(log_path, "w") as f:
                f.write(f"{genesis_msg} | {genesis_hash}\n")

    def compute_hash(self, data):
        """Vypočítá SHA-256 hash z řetězce"""
        return hashlib.sha256(data.encode()).hexdigest()

    def get_last_hash(self):
        """Načte hash z posledního záznamu"""
        with open(self.log_path, "r") as f:
            lines = f.readlines()
            if not lines:
                return "0"
            return lines[-1].strip().split(" | ")[-1]

    def verify_integrity(self):
        """Ověří integritu celého logu"""
        with open(self.log_path, "r") as f:
            lines = f.readlines()

        prev_hash = "0"
        for line in lines:
            line = line.strip()
            if not line:
                continue
            parts = line.rsplit(" | ", 1)
            if len(parts) != 2:
                raise ValueError("Invalid log format!")
            data_part, hash_part = parts
            computed_hash = self.compute_hash(data_part + prev_hash)
            if computed_hash != hash_part:
                raise ValueError("Log integrity check failed!")
            prev_hash = hash_part

    def log(self, level, message):
        """Zaloguje zprávu s kontrolou integrity"""
        self.verify_integrity()

        timestamp = datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        prev_hash = self.get_last_hash()
        data_part = f"{timestamp} - {level.upper()} - {message}"
        new_hash = self.compute_hash(data_part + prev_hash)

        with open(self.log_path, "a") as f:
            f.write(f"{data_part} | {new_hash}\n")
