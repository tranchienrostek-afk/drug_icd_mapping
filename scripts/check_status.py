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

print("--- DOCKER PS (ALL) ---")
# limit output width to avoid truncation mess
stdin, stdout, stderr = client.exec_command("docker ps -a --format 'table {{.ID}}\t{{.Image}}\t{{.Status}}\t{{.Names}}'")
print(stdout.read().decode().strip())

print("\n--- ACTIVE BUILD PROCESSES ---")
stdin, stdout, stderr = client.exec_command("ps aux | grep 'docker build' | grep -v grep")
out = stdout.read().decode().strip()
print(out if out else "No build process running.")

client.close()
