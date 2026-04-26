import google.generativeai as genai
import sys

API_KEY = "AIzaSyDHBVcK5V7owTcHsgLGUbWPupnergiwciA"
genai.configure(api_key=API_KEY, transport="rest")

print("Available models:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)
