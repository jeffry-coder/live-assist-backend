import json
import datetime
import logging
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser
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
    logger.info(f"Received event: {json.dumps(event)}")
    try:
        # 1) get call_id and client_email
        body = json.loads(event.get("body", "{}"))
        logger.info(f"Parsed body: {body}")
        call_id = body.get("call_id")
        client_email = body.get("client_email")
        logger.info(f"call_id: {call_id}, client_email: {client_email}")

        # 2) fetch call windows
        logger.info(f"Querying call_table for call_id: {call_id}")
        resp = call_table.query(
            KeyConditionExpression=Key("call_id").eq(call_id),
            ScanIndexForward=True
        )
        windows = resp.get("Items", [])
        logger.info(f"Fetched {len(windows)} windows from call_table")

        payload = [
            {
                "activityFeed": json.loads(win.get("activityFeed", "[]")),
                "aiTips":       json.loads(win.get("aiTips",       "[]")),
                "turns":        json.loads(win.get("turns",        "[]")),
            }
            for win in windows
        ]
        logger.info(f"Constructed payload for LLM: {json.dumps(payload)[:500]}{'...' if len(json.dumps(payload)) > 500 else ''}")

        # 3) build LLM messages
        messages = [
            ("system", SYSTEM_PROMPT),
            ("human", json.dumps(payload))
        ]
        logger.info("Built LLM messages.")

        # 4) invoke LLM + parse
        chain = llm | parser
        logger.info("Invoking LLM chain...")
        analytics = chain.invoke(messages)
        logger.info(f"LLM analytics output: {analytics.model_dump_json()}")

        # 5) save post-call analytics with client_email as primary key
        item = {
            "client_email": client_email,
            "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
            "call_id": call_id,
            **analytics.model_dump()
        }
        logger.info(f"Saving analytics to analytics_table: {json.dumps(item)}")
        analytics_table.put_item(Item=item)
        logger.info("Analytics saved successfully.")

        # 6) return for API Gateway/Electron
        response = {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": analytics.model_dump_json()
        }
        logger.info(f"Returning response: {response}")
        return response
        
    except (KeyError, ValueError, TypeError) as e:
        logger.error(f"Invalid input payload: {e}", exc_info=True)
        return {"statusCode": 400, "body": json.dumps({"error": "Bad request: missing or invalid fields"})}
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Database operation failed"})
        }
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"})
        }

if __name__ == "__main__":
    response = lambda_handler({
        "body": json.dumps({
            "call_id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
            "client_email": "test@example.com"
        })
    }, {})
    if response["statusCode"] == 200:
        print(json.loads(response["body"]))
    else:
        print(f"Error: {response}")
