"""
SkillMatch – Gemini API Key Validator & Diagnostic Tool
Run with:
    python tools/validate_gemini_key.py [OPTIONAL_API_KEY]

If no key is passed, checks .streamlit/secrets.toml and environment variables.
"""

import sys
import os
import requests
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRETS_PATH = os.path.join(ROOT, ".streamlit", "secrets.toml")

def load_key_from_sources(cli_arg: str = None) -> tuple[str, str]:
    if cli_arg and cli_arg.strip():
        return cli_arg.strip(), "Command-line argument"

    # Check .streamlit/secrets.toml
    if os.path.exists(SECRETS_PATH):
        try:
            with open(SECRETS_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GEMINI_API_KEY") or line.startswith("GOOGLE_API_KEY"):
                        parts = line.split("=", 1)
                        if len(parts) == 2:
                            val = parts[1].strip().strip('"').strip("'")
                            if val:
                                return val, ".streamlit/secrets.toml"
        except Exception:
            pass

    # Check environment variables
    env_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if env_key and env_key.strip():
        return env_key.strip(), "Environment variable"

    return "", "None"


def validate_gemini_key(api_key: str):
    print("=" * 65)
    print("🎯 SKILLMATCH GEMINI API DIAGNOSTIC TOOL")
    print("=" * 65)

    if not api_key:
        print("❌ No Gemini API key detected.")
        print("\n💡 HOW TO CONFIGURE A FREE GEMINI API KEY:")
        print("1. Go to Google AI Studio: https://aistudio.google.com/app/apikey")
        print("2. Sign in with your Google account and click 'Create API Key'.")
        print("3. Test it with: python tools/validate_gemini_key.py AIzaSyYourActualKey")
        print("4. Or save it in .streamlit/secrets.toml:")
        print("   GEMINI_API_KEY = \"AIzaSyYourActualKey\"")
        print("=" * 65)
        return False

    masked = api_key[:7] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
    print(f"🔑 Testing API Key: {masked}")

    models_to_test = ["gemini-1.5-flash", "gemini-2.0-flash"]
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": "Reply in exactly 5 words: Gemini AI connection is working."}]}],
        "generationConfig": {"maxOutputTokens": 30, "temperature": 0.2}
    }

    for model_name in models_to_test:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        try:
            print(f"📡 Probing Google AI Studio endpoint ({model_name})...")
            resp = requests.post(url, headers=headers, json=payload, timeout=15)
            
            if resp.status_code == 200:
                data = resp.json()
                parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])
                reply = parts[0].get("text", "").strip() if parts else "OK"
                print("\n✅ SUCCESS: Your Gemini API Key is ACTIVE and VALID!")
                print(f"   Model: {model_name}")
                print(f"   Response from Google AI: \"{reply}\"")
                print("=" * 65)
                return True

            elif resp.status_code in (400, 403):
                print(f"\n❌ ERROR (HTTP {resp.status_code}): API key is invalid, unauthorized, or not found.")
                try:
                    err_details = resp.json().get("error", {}).get("message", resp.text)
                    print(f"   Google response: {err_details}")
                except Exception:
                    pass
                print("\n💡 Solution: Ensure you copied the active key from https://aistudio.google.com/app/apikey")
                print("   Valid Gemini keys typically begin with 'AIzaSy' and are 39 characters.")
                print("=" * 65)
                return False

            elif resp.status_code == 429:
                print("\n⚠️ NOTICE (HTTP 429): Key is valid, but rate limit or quota exceeded.")
                print("   Free tier permits 15 requests per minute. Wait a few moments and retry.")
                print("=" * 65)
                return False

            else:
                print(f"\n⚠️ HTTP {resp.status_code}: {resp.text[:100]}")

        except Exception as e:
            print(f"⚠️ Connection error: {e}")

    print("=" * 65)
    return False


if __name__ == "__main__":
    cli_arg = sys.argv[1] if len(sys.argv) > 1 else None
    key, src = load_key_from_sources(cli_arg)
    print(f"📁 Source: {src}")
    validate_gemini_key(key)
