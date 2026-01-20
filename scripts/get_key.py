import os
import paramiko
from dotenv import load_dotenv

ENV_PATH = os.path.join(os.getcwd(), 'fastapi-medical-app', '.env')
load_dotenv(ENV_PATH)

HOST = os.getenv('SSH_HOST')
USER = os.getenv('SSH_USER')
PASS = os.getenv('SSH_PASS')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS)

stdin, stdout, stderr = client.exec_command("cat ~/.ssh/id_rsa.pub")
print(stdout.read().decode().strip())
client.close()
