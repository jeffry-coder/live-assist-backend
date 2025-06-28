import json
import logging
import datetime
from dotenv import load_dotenv

import boto3
from botocore.exceptions import ClientError
from agent_executor import Agent


# SetUp
load_dotenv()
DDB_TABLE = "call-records"
dynamodb_client = boto3.client("dynamodb")

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_call_history(call_id, current_window):
    """Fetch previous windows for this call from DynamoDB"""
    try:
        response = dynamodb_client.query(
            TableName=DDB_TABLE,
            KeyConditionExpression="call_id = :cid AND window_number < :w",
            ExpressionAttributeValues={
                ":cid": {"S": call_id},
                ":w":   {"N": str(current_window)}
            }
        )
        return response.get("Items", [])
    except ClientError as e:
        logger.error(f"Error fetching call history: {e}")
        return []


def lambda_handler(event, context):
    # 1) Parse and validate input
    try:
        payload = json.loads(event.get("body", event))
        call_id = payload["call_id"]
        window_num = int(payload["window_num"])
        turns = payload["turns"]  # list of { speaker, transcript, timestamp? }
    except (KeyError, ValueError, TypeError) as e:
        logger.error(f"Invalid input payload: {e}")
        return {"statusCode": 400, "body": json.dumps({"error": "Bad request: missing or invalid fields"})}

    # 2) Get history for context
    history_items = get_call_history(call_id, window_num)
    call_history = []
    for item in history_items:
        call_history.append({
            "turns": json.loads(item.get("turns", {}).get("S", "[]")),
            "aiTips": json.loads(item.get("aiTips", {}).get("S", "[]")),
            "activityFeed": json.loads(item.get("activityFeed", {}).get("S", "[]"))
        })

    # 3) Build agent input
    agent_input = {
        "current_window": {"turns": turns},
        "call_history": call_history
    }

    # 4) Invoke Bedrock agent
    agent = Agent()
    try:
        ai_tips, tool_calls = agent.analyze_transcript(agent_input)
        logger.info(f"AI tips: {ai_tips}")
        logger.info(f"Tool calls: {tool_calls}")
    except Exception as e:
        logger.error(f"Agent invocation failed: {e}")
        return {"statusCode": 502, "body": json.dumps({"error": "Agent processing error"})}

    # 5) Extract results
    ai_tips = [tip.model_dump() for tip in ai_tips]
    activity_feed = [act.model_dump() for act in tool_calls]

    # 6) Persist to DynamoDB
    try:
        dynamodb_client.put_item(
            TableName=DDB_TABLE,
            Item={
                "call_id": {"S": call_id},
                "window_number": {"N": str(window_num)},
                "turns": {"S": json.dumps(turns)},
                "aiTips": {"S": json.dumps(ai_tips)},
                "activityFeed": {"S": json.dumps(activity_feed)},
                "created_at": {"S": datetime.datetime.now(datetime.UTC).isoformat()}
            }
        )
    except ClientError as e:
        logger.error(f"DynamoDB put error: {e}")

    # 7) Return API response
    body = {"aiTips": ai_tips, "activityFeed": activity_feed}
    return {"statusCode": 200, "body": json.dumps(body)}

if __name__ == "__main__":
    with open("test_data.json", "r") as f:
        test_data = json.load(f)
    response = lambda_handler({"body": json.dumps(test_data)}, None)
    print(response)
