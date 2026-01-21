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

# 1. Create a local python script file for the remote actions
remote_code = r"""import sqlite3
import json
import os

DB_PATH = '/root/workspace/drug_icd_mapping/fastapi-medical-app/app/database/medical.db'

print(f"Checking DB at: {DB_PATH}")
if not os.path.exists(DB_PATH):
    print("DB FILE NOT FOUND")
    exit(1)

try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM knowledge_base')
    print(f'Knowledge Base Rows: {cursor.fetchone()[0]}')
    
    print('--- Sample Amoxicillin ---')
    cursor.execute("SELECT drug_name, drug_name_norm, disease_icd FROM knowledge_base WHERE drug_name_norm LIKE '%amoxicillin%' LIMIT 5")
    rows = cursor.fetchall()
    print(json.dumps(rows, indent=2))
except Exception as e:
    print(f'Error: {e}')
finally:
    if 'conn' in locals(): conn.close()
"""

# 2. Upload it
sftp = client.open_sftp()
with sftp.file("/root/workspace/db_debug.py", "w") as f:
    f.write(remote_code)
sftp.close()

# 3. Execute it
print("Executing remote script...")
stdin, stdout, stderr = client.exec_command("python3 /root/workspace/db_debug.py")
print("STDOUT:\n" + stdout.read().decode().strip())
err = stderr.read().decode().strip()
if err: print("STDERR:\n" + err)

client.close()
