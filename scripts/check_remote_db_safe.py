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

log_content = []

# Check DB file size
stdin, stdout, stderr = client.exec_command("ls -lh /root/workspace/drug_icd_mapping/fastapi-medical-app/app/database/medical.db")
size = stdout.read().decode().strip()
log_content.append(f"DB SIZE: {size}")

# Query DB
query_script = """
import sqlite3
import json
conn = sqlite3.connect('/root/workspace/drug_icd_mapping/fastapi-medical-app/app/database/medical.db')
cursor = conn.cursor()
try:
    cursor.execute('SELECT COUNT(*) FROM knowledge_base')
    print(f'Knowledge Base Rows: {cursor.fetchone()[0]}')
    
    print('--- Sample Amoxicillin ---')
    cursor.execute("SELECT drug_name, drug_name_norm, disease_icd FROM knowledge_base WHERE drug_name_norm LIKE '%amoxicillin%' LIMIT 5")
    rows = cursor.fetchall()
    print(json.dumps(rows))
except Exception as e:
    print(f'Error: {e}')
finally:
    conn.close()
"""

stdin, stdout, stderr = client.exec_command(f'python3 -c "{query_script}"')
out = stdout.read().decode().strip()
err = stderr.read().decode().strip()

log_content.append(f"DB OUTPUT:\n{out}")
if err: log_content.append(f"DB STDERR:\n{err}")

client.close()

with open("safe_db_log.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(log_content))
    
print("Log written to safe_db_log.txt")
