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

print("--- WEB CONTAINER STATUS ---")
stdin, stdout, stderr = client.exec_command("docker ps --filter name=web --format '{{.Names}} | {{.Status}} | {{.Image}}'")
output = stdout.read().decode().strip()
print(output if output else "No 'web' container found via filter.")

print("\n--- ALL CONTAINERS (First 5) ---")
stdin, stdout, stderr = client.exec_command("docker ps --format '{{.Names}} | {{.Status}}' | head -n 5")
print(stdout.read().decode().strip())

client.close()
