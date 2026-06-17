import os
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv()
base_url = os.environ.get("OLLAMA_CLOUD_BASE_URL", "http://localhost:11434")
api_key = os.environ.get("OLLAMA_CLOUD_API_KEY", "")

url = f"{base_url}/api/embed"
print("Testing URL:", url)

data = b'{"model": "nomic-embed-text", "input": "test"}'
req = urllib.request.Request(url, data=data, headers={
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json'
})

try:
    res = urllib.request.urlopen(req)
    print("Success:", res.read())
except urllib.error.HTTPError as e:
    print("HTTPError:", e.code, e.reason)
    print("Response Body:", e.read().decode('utf-8', errors='ignore'))
except Exception as e:
    print("Exception:", e)
