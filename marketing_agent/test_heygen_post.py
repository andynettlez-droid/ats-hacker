import os
import requests
from dotenv import load_dotenv

# Load env
base_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(base_dir, ".env"))

HEYGEN_API_KEY = os.getenv("HEYGEN_API_KEY")

def test_post():
    url = "https://api.heygen.com/v3/videos"
    headers = {
        "x-api-key": HEYGEN_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "type": "avatar",
        "avatar_id": "74dd6e182f0d415ab740c1097d49304b", # Maya
        "script": "Hello, this is a test from the programmatic pipeline.",
        "voice_id": "16a09e4706f74997ba4ed05ea11470f6", # Cassidy
        "aspect_ratio": "9:16",
        "resolution": "1080p"
    }

    print("[*] Submitting test post to v3/videos...")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_post()
