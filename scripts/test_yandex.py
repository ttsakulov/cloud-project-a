#!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("YC_API_KEY")
folder_id = os.getenv("YC_FOLDER_ID")

print(f"API Key: {api_key[:20]}... (скрыто)")
print(f"Folder ID: {folder_id}")

url = "https://resource-manager.api.cloud.yandex.net/resource-manager/v1/folders"
headers = {"Authorization": f"Api-Key {api_key}"}

response = requests.get(url, headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:200]}")