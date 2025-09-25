import os
import requests
from dotenv import load_dotenv

load_dotenv()

def list_azure_deployments():
    """List deployments using Azure REST API"""
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT").rstrip("/")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
    
    url = f"{endpoint}/openai/deployments?api-version={api_version}"
    headers = {"api-key": api_key}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        deployments = response.json()
        print("Available deployments:")
        print("=" * 50)
        
        if "data" in deployments:
            for deployment in deployments["data"]:
                name = deployment.get("id", "Unknown")
                model = deployment.get("model", "Unknown")
                status = deployment.get("status", "Unknown")
                print(f"Deployment Name: {name}")
                print(f"Model: {model}")
                print(f"Status: {status}")
                print("-" * 30)
        else:
            print("No deployments found or unexpected response format")
            print(f"Response: {deployments}")
            
    except requests.exceptions.RequestException as e:
        print(f"Error listing deployments: {e}")

if __name__ == "__main__":
    list_azure_deployments()