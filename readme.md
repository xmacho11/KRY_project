## Basic info
Repo for a MPC-KRY project. Client-Server secured data storage with two factor authentication using password and TOTP code. AES data transfer from client to server and vice versa. Asymmetric cryptography (RSA) used for keys transfer. To be finished.
TODO: file explorer for and TLS implementation.

## Linux version Requirements

### Python 3.13.2 
[link](https://www.python.org/downloads/release/python-3132/)

### Virtual enviroment
create
```bash  
python3 -m venv venv
``` 
activate
```bash  
source ./venv/bin/activate
```

### Libraries
```bash
pip install -r requirements.txt
```
### Start server
```bash
python3 server.py
```
### Run client
```bash
python3 client.py
```
