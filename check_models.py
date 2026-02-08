import google.generativeai as genai
import os

API_KEY = "AIzaSyCDERQtL2Ho-wBgjMJRaUEpY6HgEPq3vJE"
genai.configure(api_key=API_KEY)

print("Listing available models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Name: {m.name}")
except Exception as e:
    print(f"Error listing models: {e}")
