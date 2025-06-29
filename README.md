# Live Assist Backend

A Python-based AI agent system that provides real-time insights and automation for customer service calls. This backend processes live call transcripts, analyzes conversations using OpenAI's GPT models, and integrates with HubSpot CRM and AWS services to provide actionable tips and automated workflows.

### 🚨 **Important: Switch to `post-call` branch for post-call analytics Lambda!**  
> The main branch only handles live call features. For post-call processing, **go to the `post-call` branch**.

## 🏗️ Architecture

The system consists of three main components:

- **Lambda Function** (`lambda_function.py`) - AWS Lambda handler that processes incoming call data
- **Agent Executor** (`agent_executor.py`) - AI agent that analyzes conversations and generates insights
- **Agent Toolkit** (`agent_toolkit.py`) - Collection of tools for CRM operations and knowledge retrieval

## 📁 Project Structure

```
live-assist-backend/
├── lambda_function.py      # AWS Lambda entry point and DynamoDB operations
├── agent_executor.py       # AI agent with conversation analysis logic
├── agent_toolkit.py        # HubSpot CRM and Kendra search tools
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container configuration for AWS Lambda
├── .dockerignore          # Docker build exclusions
├── .gitignore            # Git exclusions
└── test/
    ├── test_api.py       # API testing script
    └── test_data.json    # Sample call data for testing
```

## 🚀 Features

### AI-Powered Call Analysis
- Real-time conversation analysis using OpenAI GPT-4
- Generation of contextual AI tips (Urgent, Suggestion, Info)
- Tool invocation based on conversation context
- Memory retention across multiple call windows

### CRM Integration
- **HubSpot CRM Operations**:
  - Contact lookup by email
  - Support ticket creation
  - Contact property updates
  - Deal information retrieval
  - Company-based contact search
  - Activity timeline tracking

### Knowledge Management
- Amazon Kendra integration for company manual searches
- Contextual knowledge retrieval for support scenarios

### AWS Services Integration
- **DynamoDB**: Call records and analytics storage
- **Lambda**: Serverless compute execution
- **API Gateway**: RESTful API endpoints
- **Kendra**: Intelligent document search

## 🛠️ Dependencies

```txt
boto3                # AWS SDK
botocore            # AWS core library
pydantic            # Data validation
python-dotenv       # Environment variable management
langchain-core      # LangChain framework core
langchain-community # LangChain community tools
langgraph           # Graph-based agent execution
langchain-aws       # AWS integrations for LangChain
langchain-openai    # OpenAI integration
```

## 🔧 Environment Variables

Create a `.env` file in the root directory:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# HubSpot CRM
HUBSPOT_API_KEY=your_hubspot_api_key

# AWS Kendra
AMAZON_KENDRA_INDEX_ID=your_kendra_index_id

# AWS Configuration (if running locally)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_DEFAULT_REGION=ap-southeast-2
```

## 🏃‍♂️ Running Locally

### Prerequisites
- Python 3.13+
- AWS CLI configured
- Required environment variables set

### Setup
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd live-assist-backend
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

### Local Testing

#### Test the Lambda Function Locally
```bash
python lambda_function.py
```

#### Test the deployed lambda API  
Sample data is available at `test/test_data.json`  
```bash
cd test
python test_api.py
```

#### Interactive Agent Testing
```bash
python agent_executor.py
```
This starts an interactive roleplay simulation for testing conversation analysis.

## ☁️ AWS Deployment

### Prerequisites
- AWS CLI configured with appropriate permissions
- Docker installed
- Access to AWS ECR, Lambda, DynamoDB, and API Gateway

### Required AWS Resources

#### DynamoDB Tables
Create two DynamoDB tables:

1. **call-records**
   - Partition Key: `call_id` (String)
   - Sort Key: `window_number` (Number)

2. **call-analytics**
   - Partition Key: `client_email` (String)
   - Sort Key: `created_at` (String)

```bash
# Create call-records table
aws dynamodb create-table \
    --table-name call-records \
    --attribute-definitions \
        AttributeName=call_id,AttributeType=S \
        AttributeName=window_number,AttributeType=N \
    --key-schema \
        AttributeName=call_id,KeyType=HASH \
        AttributeName=window_number,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST

# Create call-analytics table
aws dynamodb create-table \
    --table-name call-analytics \
    --attribute-definitions \
        AttributeName=client_email,AttributeType=S \
        AttributeName=created_at,AttributeType=S \
    --key-schema \
        AttributeName=client_email,KeyType=HASH \
        AttributeName=created_at,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST
```

#### Amazon Kendra Index
Set up a Kendra index for company manual searches:
```bash
aws kendra create-index \
    --name "company-manuals" \
    --description "Company manuals and documentation for customer support" \
    --role-arn "arn:aws:iam::ACCOUNT:role/KendraServiceRole"
```

### Container Deployment

#### 1. Build and Push Docker Image
```bash
# Get ECR login token
aws ecr get-login-password --region ap-southeast-2 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.ap-southeast-2.amazonaws.com

# Create ECR repository (if not exists)
aws ecr create-repository --repository-name live-assist-backend --region ap-southeast-2

# Build and tag image
docker build -t live-assist-backend .
docker tag live-assist-backend:latest <account-id>.dkr.ecr.ap-southeast-2.amazonaws.com/live-assist-backend:latest

# Push to ECR
docker push <account-id>.dkr.ecr.ap-southeast-2.amazonaws.com/live-assist-backend:latest
```

#### 2. Create Lambda Function
```bash
aws lambda create-function \
    --function-name live-assist-backend \
    --package-type Image \
    --code ImageUri=<account-id>.dkr.ecr.ap-southeast-2.amazonaws.com/live-assist-backend:latest \
    --role arn:aws:iam::<account-id>:role/lambda-execution-role \
    --timeout 300 \
    --memory-size 1024 \
    --environment Variables='{
        "OPENAI_API_KEY":"your_key",
        "HUBSPOT_API_KEY":"your_key",
        "AMAZON_KENDRA_INDEX_ID":"your_index_id"
    }'
```

#### 3. Create API Gateway
```bash
# Create REST API
aws apigateway create-rest-api --name live-assist-api

# Configure API Gateway to proxy to Lambda function
# (Follow AWS API Gateway documentation for detailed setup)
```

### Required IAM Permissions

The Lambda execution role needs the following permissions:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:Query",
                "dynamodb:UpdateItem"
            ],
            "Resource": [
                "arn:aws:dynamodb:*:*:table/call-records",
                "arn:aws:dynamodb:*:*:table/call-analytics"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "kendra:Query",
                "kendra:Retrieve"
            ],
            "Resource": "arn:aws:kendra:*:*:index/*"
        }
    ]
}
```

## 📊 API Reference

### POST /default/callAgent

Analyzes a conversation window and returns AI tips and activity feed.

#### Request Body
```json
{
    "call_id": "string",
    "window_num": number,
    "client_email": "string",
    "turns": [
        {
            "speaker": "agent|customer",
            "transcript": "string",
            "timestamp": "ISO 8601 string"
        }
    ]
}
```

#### Response
```json
{
    "aiTips": [
        {
            "tag": "Urgent|Suggestion|Info",
            "content": "string"
        }
    ],
    "activityFeed": [
        {
            "name": "string",
            "input": "string",
            "output": "string",
            "status": "success|failed"
        }
    ]
}
```

## 🔒 Security Considerations

- All API keys are stored as environment variables
- AWS IAM roles follow the principle of least privilege
- DynamoDB tables use encryption at rest
- API Gateway endpoints should be secured with API keys or OAuth

## 📈 Monitoring

- CloudWatch logs are automatically created for Lambda function execution
- DynamoDB metrics are available in CloudWatch
- Consider setting up CloudWatch alarms for error rates and latency

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions: please contact jeffry.code@gmail.com
