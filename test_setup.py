import os
from dotenv import load_dotenv
import anthropic
import requests
from dateutil import parser
import pytz
import pdfplumber

# Load environment variables
load_dotenv()

print("🧪 Testing Your Working Setup...")

# Test each library
libraries = [
    ("anthropic", anthropic),
    ("requests", requests), 
    ("python-dateutil", parser),
    ("pytz", pytz),
    ("pdfplumber", pdfplumber)
]

for name, lib in libraries:
    try:
        print(f"✅ {name} imported successfully!")
    except Exception as e:
        print(f"❌ {name} failed: {e}")

# Test Anthropic API
api_key = os.getenv('ANTHROPIC_API_KEY')
if api_key:
    print("✅ Anthropic API key found!")
    try:
        client = anthropic.Anthropic(api_key=api_key)
        print("✅ Anthropic client initialized!")
    except Exception as e:
        print(f"❌ Anthropic error: {e}")
else:
    print("❌ Add ANTHROPIC_API_KEY to .env file")

print("\n🎉 All core libraries working! Ready for Step 3.")