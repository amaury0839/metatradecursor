import requests
import json

print("Checking API...")
try:
    r = requests.get("http://127.0.0.1:8003/api/account", timeout=2)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print("Data received:", json.dumps(data, indent=2)[:200])
except Exception as e:
    print(f"Error: {e}")

print("\nChecking UI...")
try:
    r = requests.get("http://localhost:8505", timeout=2)
    print(f"Streamlit: {r.status_code}")
except Exception as e:
    print(f"Error: {e}")
