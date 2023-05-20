import requests
import json

# Define the TikTok API endpoint
api_url = f"https://www.tiktok.com/api/item/detail/?itemId=7223808384598822171"

# Make an HTTP GET request to the TikTok API endpoint
response = requests.get(api_url)
print(response.raw)

# Parse the JSON response
# data = json.loads(response)
# print(data)