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

# Check DB file size
print("--- DB File Size ---")
stdin, stdout, stderr = client.exec_command("ls -lh /root/workspace/drug_icd_mapping/fastapi-medical-app/app/database/medical.db")
print(stdout.read().decode().strip())

# Query DB
print("\n--- DB Counts ---")
query_script = """
import sqlite3
conn = sqlite3.connect('/root/workspace/drug_icd_mapping/fastapi-medical-app/app/database/medical.db')
cursor = conn.cursor()
try:
    cursor.execute('SELECT COUNT(*) FROM knowledge_base')
    print(f'Knowledge Base Rows: {cursor.fetchone()[0]}')
    
    print('--- Sample Amoxicillin ---')
    cursor.execute("SELECT drug_name, drug_name_norm, disease_icd FROM knowledge_base WHERE drug_name_norm LIKE '%amoxicillin%' LIMIT 5")
    for row in cursor.fetchall():
        print(row)
except Exception as e:
    print(f'Error: {e}')
finally:
    conn.close()
"""

stdin, stdout, stderr = client.exec_command(f'python3 -c "{query_script}"')
print(stdout.read().decode().strip())
err = stderr.read().decode().strip()
if err: print(f"STDERR: {err}")

client.close()
