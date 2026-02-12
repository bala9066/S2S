import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

client_id = os.environ.get('DIGIKEY_CLIENT_ID')
client_secret = os.environ.get('DIGIKEY_CLIENT_SECRET')

print(f"Client ID: {client_id[:12]}...")
print(f"Client Secret: {client_secret[:5]}...")

def test_client_credentials():
    print("\nTesting Client Credentials Flow (2-legged)...")
    token_url = 'https://api.digikey.com/v1/oauth2/token'
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials',
    }
    
    resp = requests.post(token_url, data=data, timeout=15)
    print(f"Status Code: {resp.status_code}")
    if resp.status_code == 200:
        token_data = resp.json()
        token = token_data.get('access_token')
        print(f"Token obtained: {token[:20]}...")
        return token
    else:
        print(f"Error: {resp.text}")
        return None

def test_search(token):
    print("\nTesting Search with obtained token...")
    url = 'https://api.digikey.com/Search/v3/Products/Keyword'
    headers = {
        'Authorization': f'Bearer {token}',
        'X-DIGIKEY-Client-Id': client_id,
        'Content-Type': 'application/json'
    }
    payload = {
        'Keywords': 'STM32F4',
        'RecordCount': 1
    }
    
    resp = requests.post(url, json=payload, headers=headers, timeout=10)
    print(f"Search Status Code: {resp.status_code}")
    if resp.status_code != 200:
        print(f"Search Error: {resp.text}")
    else:
        print("Search Success!")

if __name__ == "__main__":
    token = test_client_credentials()
    if token:
        test_search(token)
    else:
        print("\nCould not get token via Client Credentials.")
