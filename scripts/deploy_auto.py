import os
import sys
import paramiko
import zipfile
import shutil
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

REMOTE_DIR = "/root/workspace/drug_icd_mapping"
LOCAL_APP_DIR = "fastapi-medical-app"
LOCAL_DB_PATH = os.path.join(LOCAL_APP_DIR, "app", "database", "medical.db")
ZIP_NAME = "deploy_package.zip"

def create_ssh_client():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    return client

def run_command(client, cmd):
    print(f"> Remote: {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd)
    
    # Live output streaming
    while True:
        line = stdout.readline()
        if not line: break
        print(line.strip())
        
    exit_status = stdout.channel.recv_exit_status()
    if exit_status != 0:
        err = stderr.read().decode().strip()
        print(f"Error: {err}")
        print(f"Command failed with status {exit_status}")
        sys.exit(exit_status)

def zip_source_code():
    print("Zipping source code...")
    if os.path.exists(ZIP_NAME):
        os.remove(ZIP_NAME)
        
    local_path = os.path.abspath(LOCAL_APP_DIR)
    
    with zipfile.ZipFile(ZIP_NAME, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(local_path):
            # Exclude heavy/unwanted dirs
            dirs[:] = [d for d in dirs if d not in ('.git', '.venv', '__pycache__', 'venv', 'node_modules', '.idea', '.vscode')]
            
            for file in files:
                if file in ('.env.production', '.env', 'medical.db-shm', 'medical.db-wal', ZIP_NAME): continue
                # Skip DB in zip (upload separately)
                if file == 'medical.db': continue
                
                # Path handling
                abs_file = os.path.join(root, file)
                rel_path = os.path.relpath(abs_file, local_path)
                zipf.write(abs_file, rel_path)
    
    size_mb = os.path.getsize(ZIP_NAME) / (1024*1024)
    print(f"Created {ZIP_NAME} ({size_mb:.2f} MB)")

def main():
    print(f"Connecting to {HOST} as {USER}...")
    client = create_ssh_client()
    sftp = client.open_sftp()
    
    # 1. Zip
    zip_source_code()
    
    remote_app_path = f"{REMOTE_DIR}/{LOCAL_APP_DIR}"
    remote_zip_path = f"{REMOTE_DIR}/{ZIP_NAME}"
    
    print("2. Preparing Remote Directories...")
    run_command(client, f"mkdir -p {REMOTE_DIR}/data {remote_app_path}")
    
    # 2. Upload Zip
    print(f"3. Uploading Code ({ZIP_NAME})...")
    sftp.put(ZIP_NAME, remote_zip_path)
    
    # Upload DB
    print("4. Uploading Database...")
    remote_db_path = f"{REMOTE_DIR}/data/medical.db"
    print(f"> PUT {LOCAL_DB_PATH} -> {remote_db_path}")
    sftp.put(LOCAL_DB_PATH, remote_db_path)
    
    # Upload Env
    print("5. Uploading Environment Config...")
    local_env_prod = os.path.join(LOCAL_APP_DIR, ".env.production")
    remote_env = f"{remote_app_path}/.env"
    sftp.put(local_env_prod, remote_env)
    
    # 3. Unzip and Build
    print("6. Executing Remote Build & Start...")
    
    build_script = f"""
    set -e
    
    # Install unzip if missing (requires root? USER is root)
    if ! command -v unzip &> /dev/null; then
        apt-get update && apt-get install -y unzip
    fi
    
    echo "Unzipping..."
    unzip -o {remote_zip_path} -d {remote_app_path}
    rm {remote_zip_path}
    
    cd {remote_app_path}
    # Ensure correct permissions
    mkdir -p ../data
    chmod -R 777 ../data
    cp Dockerfile.prod Dockerfile
    
    export COMPOSE_PROJECT_NAME=drug_icd_mapping
    export HOST_PORT=8006
    
    echo 'Building & Starting...'
    docker-compose up -d --build --no-deps web
    
    docker-compose ps
    """
    run_command(client, build_script)
    
    sftp.close()
    client.close()
    
    # Cleanup local zip
    if os.path.exists(ZIP_NAME):
        os.remove(ZIP_NAME)
        
    print(">>> DEPLOYMENT SUCCESSFUL <<<")

if __name__ == "__main__":
    main()
