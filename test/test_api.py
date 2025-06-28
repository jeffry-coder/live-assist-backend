import requests

# Lambda URL (replace with your actual Lambda endpoint)
LAMBDA_URL = "https://r1m1mxunle.execute-api.ap-southeast-2.amazonaws.com/default/getCallAnalytics"
headers = {"Content-Type": "application/json"}

test_data = {
    "client_email": "test@example.com",
    "call_id": "test-call-1"
}

# Send POST request to Lambda with test data
response = requests.post(LAMBDA_URL, json=test_data, headers=headers)

# Print response from Lambda
print("Status Code:", response.status_code)
print("Response Body:", response.text)
