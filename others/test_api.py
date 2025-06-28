import json
import requests

# Lambda URL (replace with your actual Lambda endpoint)
LAMBDA_URL = "https://egy9qthh94.execute-api.ap-southeast-2.amazonaws.com/default/callAgent"
headers = {"Content-Type": "application/json"}

# Load test data from JSON file
with open("test_data.json", "r") as f:
    test_data = json.load(f)

# Send POST request to Lambda with test data
response = requests.post(LAMBDA_URL, json=test_data, headers=headers)

# Print response from Lambda
print("Status Code:", response.status_code)
print("Response Body:", response.text)
