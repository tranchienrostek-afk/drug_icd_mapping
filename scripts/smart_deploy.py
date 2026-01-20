import os
import sys
import paramiko
from dotenv import load_dotenv

# Load env from fastapi-medical-app/.env
ENV_PATH = os.path.join(os.getcwd(), 'fastapi-medical-app', '.env')
load_dotenv(ENV_PATH)

HOST = os.getenv('SSH_HOST')
USER = os.getenv('SSH_USER')
PASS = os.getenv('SSH_PASS')

if not all([HOST, USER, PASS]):
    print("Error: Missing SSH credentials in .env")
    sys.exit(1)

PROJECT_DIR = "/root/workspace/drug_icd_mapping/fastapi-medical-app"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print(f"Connecting to {HOST}...")
    
    deploy_cmd = f"""
    set -e
    cd {PROJECT_DIR}
    
    echo "1. Pulling latest code..."
    git pull origin main
    
    echo "2. Rebuilding Container..."
    # Always rebuild to catch dependency changes in Dockerfile/requirements
    # Docker uses cache so it's fast if no changes.
    cp Dockerfile.prod Dockerfile
    docker-compose up -d --build --no-deps web
    
    echo "3. Pruning old images..."
    docker image prune -f
    
    echo ">>> SMART DEPLOY SUCCESSFUL <<<"
    docker-compose ps
    """
    
    print("> Executing Remote Update...")
    stdin, stdout, stderr = client.exec_command(deploy_cmd)
    
    # Stream output
    while True:
        line = stdout.readline()
        if not line: break
        print(line.strip())
        
    exit_status = stdout.channel.recv_exit_status()
    if exit_status != 0:
        print(f"Error: {stderr.read().decode().strip()}")
        sys.exit(exit_status)
        
    client.close()

if __name__ == "__main__":
    main()
