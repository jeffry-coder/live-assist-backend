import json
import logging
import datetime
from dotenv import load_dotenv

import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
from agent_executor import Agent

# Load env vars
load_dotenv()

# Setup logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# DynamoDB resource + table definitions
dynamodb = boto3.resource("dynamodb")
call_records_table = dynamodb.Table("call-records")
call_analytics_table = dynamodb.Table("call-analytics")


def get_call_history(call_id, current_window):
    """Fetch previous windows for this call"""
    try:
        response = call_records_table.query(
            KeyConditionExpression=Key("call_id").eq(call_id) & Key("window_number").lt(current_window)
        )
        return response.get("Items", [])
    except ClientError as e:
        logger.error(f"Error fetching call history: {e}")
        return []


def get_past_call_summary(client_email):
    """Get the most recent memory blob from past calls for this client"""
    try:
        response = call_analytics_table.query(
            KeyConditionExpression=Key("client_email").eq(client_email),
            ScanIndexForward=False,
            Limit=1
        )
        items = response.get("Items", [])
        return items[0].get("memory", {}) if items else {}
    except ClientError as e:
        logger.error(f"Error fetching past call summary: {e}")
        return {}


def lambda_handler(event, context):
    # 1) Parse input
    try:
        payload = json.loads(event.get("body", event))
        call_id = payload["call_id"]
        window_num = int(payload["window_num"])
        turns = payload["turns"]
        client_email = payload["client_email"]
    except (KeyError, ValueError, TypeError) as e:
        logger.error(f"Invalid input payload: {e}")
        return {"statusCode": 400, "body": json.dumps({"error": "Bad request: missing or invalid fields"})}

    # 2) Get historical context
    history_items = get_call_history(call_id, window_num)
    call_history = [
        {
            "turns": json.loads(item.get("turns", "[]")),
            "aiTips": json.loads(item.get("aiTips", "[]")),
            "activityFeed": json.loads(item.get("activityFeed", "[]"))
        }
        for item in history_items
    ]

    # 3) Get prior call memory
    past_call_summary = get_past_call_summary(client_email)
    print(f"Past call summary: {past_call_summary}")

    # 4) Build agent input
    agent_input = {
        "current_window": {"turns": turns},
        "call_history": call_history,
        "past_call_summary": past_call_summary
    }

    # 5) Run agent
    agent = Agent()
    try:
        ai_tips, tool_calls = agent.analyze_transcript(agent_input)
        logger.info(f"AI tips: {ai_tips}")
        logger.info(f"Tool calls: {tool_calls}")
    except Exception as e:
        logger.error(f"Agent invocation failed: {e}")
        return {"statusCode": 502, "body": json.dumps({"error": "Agent processing error"})}

    # 6) Convert results
    ai_tips_out = [tip.model_dump() for tip in ai_tips]
    activity_feed_out = [act.model_dump() for act in tool_calls]

    # 7) Save to DynamoDB
    try:
        call_records_table.put_item(
            Item={
                "call_id": call_id,
                "window_number": window_num,
                "turns": json.dumps(turns),
                "aiTips": json.dumps(ai_tips_out),
                "activityFeed": json.dumps(activity_feed_out),
                "created_at": datetime.datetime.now(datetime.UTC).isoformat()
            }
        )
    except ClientError as e:
        logger.error(f"DynamoDB put error: {e}")

    # 8) Respond
    return {
        "statusCode": 200,
        "body": json.dumps({
            "aiTips": [tip for item in call_history for tip in item["aiTips"]] + ai_tips_out,
            "activityFeed": [act for item in call_history for act in item["activityFeed"]] + activity_feed_out
        })
    }


# Local test runner
if __name__ == "__main__":
    with open("test/test_data.json", "r") as f:
        test_data = json.load(f)
    response = lambda_handler({"body": json.dumps(test_data)}, None)
    if response["statusCode"] == 200:
        print(json.loads(response['body']))
    else:
        print(f"Error: {response}")
