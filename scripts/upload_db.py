import os
import paramiko
from dotenv import load_dotenv

ENV_PATH = os.path.join(os.getcwd(), 'fastapi-medical-app', '.env')
load_dotenv(ENV_PATH)

HOST = os.getenv('SSH_HOST')
USER = os.getenv('SSH_USER')
PASS = os.getenv('SSH_PASS')

LOCAL_DB = os.path.join(os.getcwd(), 'fastapi-medical-app', 'app', 'database', 'medical.db')
REMOTE_DB = '/root/workspace/drug_icd_mapping/fastapi-medical-app/app/database/medical.db'

if not os.path.exists(LOCAL_DB):
    print(f"Error: Local DB not found at {LOCAL_DB}")
    exit(1)

print(f"Uploading {LOCAL_DB}...")
print(f"To {HOST}:{REMOTE_DB}")

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS)

sftp = client.open_sftp()
try:
    sftp.put(LOCAL_DB, REMOTE_DB)
    print("Upload completed successfully!")
    
    # Verify size
    remote_size = sftp.stat(REMOTE_DB).st_size
    local_size = os.path.getsize(LOCAL_DB)
    print(f"Local Size: {local_size} bytes")
    print(f"Remote Size: {remote_size} bytes")
    
except Exception as e:
    print(f"Upload failed: {e}")

sftp.close()
client.close()
