import os
import requests
from dotenv import load_dotenv

# Load dotenv
base_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(base_dir, ".env"))

HEYGEN_API_KEY = os.getenv("HEYGEN_API_KEY")

def list_avatars():
    if not HEYGEN_API_KEY or HEYGEN_API_KEY == "your_heygen_api_key_here":
        print("[!] HEYGEN_API_KEY not configured in .env.")
        return

    url = "https://api.heygen.com/v3/avatars"
    headers = {
        "x-api-key": HEYGEN_API_KEY,
        "accept": "application/json"
    }

    url = "https://api.heygen.com/v3/avatars/looks"
    headers = {
        "x-api-key": HEYGEN_API_KEY,
        "accept": "application/json"
    }

    print("[*] Fetching HeyGen public avatar looks...")
    try:
        response = requests.get(url, headers=headers, params={"ownership": "public"}, timeout=15)
        response.raise_for_status()
        res_json = response.json()
        print(f"[+] Raw looks response: {str(res_json)[:1000]}")
    except Exception as e:
        print(f"[-] Failed to fetch avatars: {e}")
        # Try fallbacks or print response text if available
        if 'response' in locals() and response is not None:
            print(response.text)

def list_voices():
    if not HEYGEN_API_KEY or HEYGEN_API_KEY == "your_heygen_api_key_here":
        return

    url = "https://api.heygen.com/v3/voices"
    headers = {
        "x-api-key": HEYGEN_API_KEY,
        "accept": "application/json"
    }

    print("\n[*] Fetching HeyGen public stock voices...")
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json().get("data", {})
        voices = data.get("voices", [])

        print(f"\n[+] Found {len(voices)} stock voices (showing top 10 English):")
        english_voices = [v for v in voices if v.get("language") == "English"]
        for i, voice in enumerate(english_voices[:10]):
            print(f"{i+1}. Name: {voice.get('name')} | Gender: {voice.get('gender')} | ID: {voice.get('voice_id')}")
        print("-" * 50)
    except Exception as e:
        print(f"[-] Failed to fetch voices: {e}")
        if 'response' in locals() and response is not None:
            print(response.text)

if __name__ == "__main__":
    list_avatars()
    list_voices()
