import os
import sys
import paramiko
from dotenv import load_dotenv

# Load env
ENV_PATH = os.path.join(os.getcwd(), 'fastapi-medical-app', '.env')
load_dotenv(ENV_PATH)

HOST = os.getenv('SSH_HOST')
USER = os.getenv('SSH_USER')
PASS = os.getenv('SSH_PASS')

REMOTE_DIR = "/root/workspace/drug_icd_mapping/fastapi-medical-app"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print(f"Checking remote state at {REMOTE_DIR}...")
    
    cmds = [
        f"cd {REMOTE_DIR} && ls -la",
        f"cd {REMOTE_DIR} && cat .env", # concise check
        f"cd {REMOTE_DIR} && docker-compose config", # Validate config
        f"cd {REMOTE_DIR} && docker-compose up -d --build app_medical_intel" # Try run
    ]
    
    for cmd in cmds:
        print(f"\n> Running: {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        if out: print("STDOUT:", out)
        if err: print("STDERR:", err)

    client.close()

if __name__ == "__main__":
    main()
