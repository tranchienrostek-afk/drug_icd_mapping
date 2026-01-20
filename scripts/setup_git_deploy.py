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
GIT_REPO = "https://github.com/tranchienrostek-afk/drug_icd_mapping.git"
PROJECT_DIR = "/root/workspace/drug_icd_mapping/fastapi-medical-app" # Path inside repo
REPO_ROOT = "/root/workspace/drug_icd_mapping"

def main():
    if not all([HOST, USER, PASS]):
        print("Missing credentials in .env")
        return

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    # 1. Check for SSH Key
    print("1. Checking for SSH Key on Server...")
    stdin, stdout, stderr = client.exec_command("cat ~/.ssh/id_rsa.pub")
    pub_key = stdout.read().decode().strip()
    
    if not pub_key:
        print("Generating new SSH Key...")
        client.exec_command('ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""')
        stdin, stdout, stderr = client.exec_command("cat ~/.ssh/id_rsa.pub")
        pub_key = stdout.read().decode().strip()
    
    print("\n" + "="*60)
    print("ACTION REQUIRED: Add this Deploy Key to GitHub Repo:")
    print("Settings -> Deploy keys -> Add deploy key")
    print("-" * 60)
    print(pub_key)
    print("-" * 60 + "\n")
    
    input("Press Enter AFTER you have added the key to GitHub...")
    
    # 2. Setup Repo
    print("2. Setting up Git Repo on Server...")
    
    # Check if .git exists
    stdin, stdout, stderr = client.exec_command(f"ls -d {REPO_ROOT}/.git")
    if stdout.channel.recv_exit_status() != 0:
        print("Cloning repository...")
        # Backup existing manual upload if needed? Maybe too complex.
        # Just move existing folder and clone fresh.
        cmds = [
            f"mv {REPO_ROOT} {REPO_ROOT}_safety_backup",
            f"git clone {GIT_REPO} {REPO_ROOT}",
            # Restore .env and DB which are gitignored
            f"cp {REPO_ROOT}_safety_backup/fastapi-medical-app/.env {PROJECT_DIR}/.env" if stdout.channel.recv_exit_status() == 0 else "true",
             f"mkdir -p {REPO_ROOT}/data",
            f"cp {REPO_ROOT}_safety_backup/data/medical.db {REPO_ROOT}/data/medical.db"
        ]
        # Actually safer to Clone via SSH URL if Key added.
        # Wait, allow user to confirm URL type.
        GIT_SSH_URL = "git@github.com:tranchienrostek-afk/drug_icd_mapping.git"
        
        setup_script = f"""
        # Ensure git
        apt-get install -y git
        
        # Test connection
        ssh -T git@github.com -o StrictHostKeyChecking=no || true
        
        if [ ! -d "{REPO_ROOT}/.git" ]; then
            echo "Backing up old folder..."
            [ -d "{REPO_ROOT}" ] && mv "{REPO_ROOT}" "{REPO_ROOT}_backup_$(date +%s)"
            
            echo "Cloning..."
            git clone {GIT_SSH_URL} {REPO_ROOT}
            
            # Restore Data
            LAST_BACKUP=$(ls -td {REPO_ROOT}_backup_* | head -1)
            if [ -n "$LAST_BACKUP" ]; then
                echo "Restoring .env and DB from $LAST_BACKUP..."
                cp "$LAST_BACKUP/fastapi-medical-app/.env" "{PROJECT_DIR}/.env"
                mkdir -p "{REPO_ROOT}/data"
                cp "$LAST_BACKUP/data/medical.db" "{REPO_ROOT}/data/medical.db"
            fi
        else
            echo "Repo already exists. Configuring URL..."
            cd {REPO_ROOT}
            git remote set-url origin {GIT_SSH_URL}
            git pull
        fi
        """
        stdin, stdout, stderr = client.exec_command(setup_script)
        while True:
             line = stdout.readline()
             if not line: break
             print(line.strip())
    else:
        print("Repo already exists. Ensuring Remote URL matches...")
        client.exec_command(f"cd {REPO_ROOT} && git remote set-url origin git@github.com:tranchienrostek-afk/drug_icd_mapping.git")

    print("\nDone! Now you can use 'smart_deploy.py' which simply triggers git pull + docker restart.")
    client.close()

if __name__ == "__main__":
    main()
