import requests

# Lambda URL (replace with your actual Lambda endpoint)
LAMBDA_URL = "https://r1m1mxunle.execute-api.ap-southeast-2.amazonaws.com/default/getCallAnalytics"
headers = {"Content-Type": "application/json"}

test_data = {
    "call_id": "77b7470a-ab14-4563-9fe8-7726188ba180",
    "client_email": "test@example.com"
}

# Send POST request to Lambda with test data
response = requests.post(LAMBDA_URL, json=test_data, headers=headers)

# Print response from Lambda
print("Status Code:", response.status_code)
print("Response Body:", response.text)
