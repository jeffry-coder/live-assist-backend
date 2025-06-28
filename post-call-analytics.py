import json
import datetime
import logging
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from models import AnalyticsOutput

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Dynamo setup
dynamodb = boto3.resource('dynamodb')
call_table = dynamodb.Table('call-records')
analytics_table = dynamodb.Table('call-analytics')

# LLM + parser setup
llm = ChatOpenAI(model_name="gpt-4o-2024-08-06", temperature=0)
parser = PydanticOutputParser(pydantic_object=AnalyticsOutput)

with open("prompt.txt", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

def lambda_handler(event, context):
    try:
        # 1) get call_id and client_email
        body = json.loads(event.get("body", "{}"))
        call_id = body.get("call_id")
        client_email = body.get("client_email")

        # 2) fetch call windows
        resp = call_table.query(
            KeyConditionExpression=Key("call_id").eq(call_id),
            ScanIndexForward=True
        )
        windows = resp.get("Items", [])

        payload = [
            {
                "activityFeed": json.loads(win.get("activityFeed", "[]")),
                "aiTips":       json.loads(win.get("aiTips",       "[]")),
                "turns":        json.loads(win.get("turns",        "[]")),
            }
            for win in windows
        ]

        # 3) build LLM messages
        messages = [
            ("system", SYSTEM_PROMPT),
            ("human", json.dumps(payload))
        ]

        # 4) invoke LLM + parse
        chain = llm | parser
        analytics = chain.invoke(messages)

        # 5) save post-call analytics with client_email as primary key
        analytics_table.put_item(Item={
            "client_email": client_email,
            "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
            "call_id": call_id,
            **analytics.model_dump()
        })

        # 6) return for API Gateway/Electron
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": analytics.model_dump_json()
        }
        
    except (KeyError, ValueError, TypeError) as e:
        logger.error(f"Invalid input payload: {e}")
        return {"statusCode": 400, "body": json.dumps({"error": "Bad request: missing or invalid fields"})}
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Database operation failed"})
        }
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"})
        }

if __name__ == "__main__":
    response = lambda_handler({
        "body": json.dumps({
            "call_id": "test-call-1",
            "client_email": "test@example.com"
        })
    }, {})
    if response["statusCode"] == 200:
        print(json.loads(response["body"]))
    else:
        print(f"Error: {response}")
