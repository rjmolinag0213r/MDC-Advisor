import os
import requests
from dotenv import load_dotenv

# Load environment
load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "anthropic/claude-3.5-sonnet"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

print(f"API Key: {API_KEY[:15]}...{API_KEY[-4:]}")
print(f"Model: {MODEL}")
print(f"URL: {API_URL}")

# Test direct API call
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "model": MODEL,
    "messages": [{"role": "user", "content": "Say hello"}],
    "temperature": 0.7
}

print("\nSending request...")
try:
    response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        content = data['choices'][0]['message']['content']
        print(f"\n✓ SUCCESS!")
        print(f"Response: {content}")
    else:
        print(f"\n✗ FAILED!")
        print(f"Response: {response.text}")
except Exception as e:
    print(f"\n✗ ERROR: {e}")
