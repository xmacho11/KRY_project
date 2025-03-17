import sqlite3
import bcrypt
import pyotp
import os 
from utils.modules import setup_logging
import logging

setup_logging()

def create_database():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        totp_secret TEXT NOT NULL
                    )''')
    
    conn.commit()
    conn.close()

def register_user(username, password_hash, totp_secret):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    try:
        cursor.execute("INSERT INTO users (username, password_hash, totp_secret) VALUES (?, ?, ?)", 
                       (username, password_hash, totp_secret))
        conn.commit()
        logging.info(f"User {username} succesfully registered!")

    except sqlite3.IntegrityError:
        logging.error("Username already taken!")
    
    conn.close()

def load_user(username):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("SELECT password_hash, totp_secret FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    
    if user:
        stored_hash, totp_secret = user
        return stored_hash, totp_secret
    else:
        return None, None  # Pokud uživatel neexistuje

def check_user_exists(username):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    
    conn.close()
    
    return user is not None
