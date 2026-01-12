import os
import sys
from dotenv import load_dotenv
from openai import AzureOpenAI

# Path to .env file
env_path = os.path.join(os.path.dirname(__file__), '..', 'fastapi-medical-app', '.env')
print(f"Loading .env from: {os.path.abspath(env_path)}")
load_dotenv(env_path)

api_key = os.getenv("AZURE_OPENAI_KEY")
api_version = os.getenv("AZURE_OPENAI_API_VERSION")
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

print("--- Azure OpenAI Configuration ---")
print(f"API Key: {'*' * 5 if api_key else 'Not Found'}")
print(f"API Version: {api_version}")
print(f"Endpoint: {azure_endpoint}")
print(f"Deployment Name: {deployment_name}")
print("--------------------------------")

if not api_key or not azure_endpoint or not deployment_name:
    print("Error: Missing Azure OpenAI configuration.")
    sys.exit(1)

client = AzureOpenAI(
    api_key=api_key,
    api_version=api_version,
    azure_endpoint=azure_endpoint
)

print("\nSending request: '1+1 = ?'...")

try:
    response = client.chat.completions.create(
        model=deployment_name,
        messages=[
            {"role": "user", "content": "1+1 = ?"}
        ]
    )
    
    content = response.choices[0].message.content
    print(f"\nResponse received:\n{content}")
    
    # Save result
    output_file = os.path.join(os.path.dirname(__file__), 'openai_api_test_result.txt')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("Test Date: " + os.getenv('DATE', '') + "\n")
        f.write(f"Model: {deployment_name}\n")
        f.write(f"Input: 1+1 = ?\n")
        f.write(f"Output: {content}\n")
        
    print(f"\nResult saved to: {output_file}")

except Exception as e:
    print(f"\nError occurred: {e}")
    # Save error result
    output_file = os.path.join(os.path.dirname(__file__), 'openai_config_test_error.txt')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Error: {e}\n")
