import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_azure_connection():
    """Test Azure OpenAI connection and get deployments"""
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "").rstrip("/")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
    
    if not endpoint or not api_key:
        print("❌ Missing environment variables")
        return None, []
    
    url = f"{endpoint}/openai/deployments?api-version={api_version}"
    headers = {"api-key": api_key}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            deployments = data.get("data", [])
            print(f"✅ Found {len(deployments)} deployment(s)")
            return api_version, deployments
        else:
            print(f"❌ Error: {response.status_code}")
            return None, []
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return None, []

if __name__ == "__main__":
    print("🚀 Azure OpenAI Connection Test")
    working_version, deployments = test_azure_connection()
    
    if working_version:
        print(f"✅ Working API version: {working_version}")
    else:
        print("❌ Connection failed")