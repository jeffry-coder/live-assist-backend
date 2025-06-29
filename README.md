# Live Assist Backend - Post-Call Analytics

A Python-based AI system that performs comprehensive post-call analytics for customer service interactions. This backend processes completed call transcripts with AI tips and tool calls, then generates detailed analytics including sentiment analysis, customer satisfaction metrics, agent performance scores, and actionable insights using OpenAI's GPT models.

## 🏗️ Architecture

The system consists of three main components:

- **Lambda Function** (`lambda_function.py`) - AWS Lambda handler that processes post-call analytics requests
- **Analytics Models** (`models.py`) - Pydantic data models defining comprehensive analytics output structure
- **AI Prompt** (`prompt.txt`) - System prompt for AI-powered call analysis and insight generation

## 📁 Project Structure

```
live-assist-backend/
├── lambda_function.py      # AWS Lambda entry point for post-call analytics
├── models.py              # Pydantic models for analytics data structures
├── prompt.txt             # System prompt for AI analysis
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container configuration for AWS Lambda
└── test/
    └── test_api.py       # API testing script for analytics endpoint
```

## 🛠️ Dependencies

```txt
boto3              # AWS SDK for DynamoDB operations
botocore           # AWS core library
pydantic           # Data validation and serialization
python-dotenv      # Environment variable management
langchain-core     # LangChain framework core
langchain-openai   # OpenAI integration for LLM analysis
```

## 🔧 Environment Variables

Create a `.env` file in the root directory:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

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

#### Test with API Endpoint
```bash
cd test
python test_api.py
```

## ☁️ AWS Deployment

### Prerequisites
- AWS CLI configured with appropriate permissions
- Docker installed
- Access to AWS ECR, Lambda, DynamoDB, and API Gateway

### Required AWS Resources

#### DynamoDB Tables
The system requires two DynamoDB tables:

1. **call-records** (Source Data)
   - Partition Key: `call_id` (String)
   - Sort Key: `window_number` (Number)
   - Contains: call transcripts, AI tips, and tool calls from live sessions

2. **call-analytics** (Analytics Output)
   - Partition Key: `client_email` (String)
   - Sort Key: `created_at` (String)
   - Contains: comprehensive post-call analytics results

```bash
# Create call-records table (if not exists)
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

### Container Deployment

#### 1. Build and Push Docker Image
```bash
# Get ECR login token
aws ecr get-login-password --region ap-southeast-2 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.ap-southeast-2.amazonaws.com

# Create ECR repository (if not exists)
aws ecr create-repository --repository-name live-assist-analytics --region ap-southeast-2

# Build and tag image
docker build -t live-assist-analytics .
docker tag live-assist-analytics:latest <account-id>.dkr.ecr.ap-southeast-2.amazonaws.com/live-assist-analytics:latest

# Push to ECR
docker push <account-id>.dkr.ecr.ap-southeast-2.amazonaws.com/live-assist-analytics:latest
```

#### 2. Create Lambda Function
```bash
aws lambda create-function \
    --function-name live-assist-analytics \
    --package-type Image \
    --code ImageUri=<account-id>.dkr.ecr.ap-southeast-2.amazonaws.com/live-assist-analytics:latest \
    --role arn:aws:iam::<account-id>:role/lambda-execution-role \
    --timeout 300 \
    --memory-size 1024 \
    --environment Variables='{
        "OPENAI_API_KEY":"your_openai_api_key"
    }'
```

#### 3. Create API Gateway Endpoint
```bash
# Create REST API
aws apigateway create-rest-api --name live-assist-analytics-api

# Configure API Gateway to proxy to Lambda function
# Recommended endpoint: POST /getCallAnalytics
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
                "dynamodb:Scan"
            ],
            "Resource": [
                "arn:aws:dynamodb:*:*:table/call-records",
                "arn:aws:dynamodb:*:*:table/call-analytics"
            ]
        }
    ]
}
```

## 📊 API Reference

### POST /getCallAnalytics

Generates comprehensive post-call analytics for a completed customer service call.

#### Request Body
```json
{
    "call_id": "string",
    "client_email": "string"
}
```

#### Response
```json
{
    "sentiment": {
        "score": 85,
        "label": "Positive"
    },
    "satisfaction": {
        "score": 90,
        "prediction": "Satisfied"
    },
    "emotions": [
        {
            "emotion": "relief",
            "intensity": 75
        },
        {
            "emotion": "gratitude",
            "intensity": 80
        }
    ],
    "callMetrics": {
        "duration": "08:42",
        "agentTalkTime": 45,
        "customerTalkTime": 50,
        "holdTime": 5
    },
    "issueResolution": {
        "resolved": true,
        "category": "password-reset",
        "resolutionTimeMinutes": 6,
        "escalationRisk": 10
    },
    "agentPerformance": {
        "professionalismScore": 95,
        "empathyScore": 88,
        "knowledgeScore": 92,
        "avgResponseLatencySeconds": 3
    },
    "keyInsights": [
        "Customer successfully resolved password issue with clear instructions",
        "Agent provided excellent support with quick response time",
        "Follow-up email sent to prevent future issues"
    ],
    "actionItems": [
        "Update password reset documentation based on customer feedback",
        "Consider proactive password security tips for similar cases"
    ],
    "tags": [
        "password-reset",
        "resolved",
        "satisfied-customer",
        "quick-resolution"
    ],
    "memory": {
        "deliverables": [
            "Password reset completed successfully",
            "Email with security tips sent to customer"
        ],
        "improvementAreas": [
            "Could have provided security best practices earlier in call"
        ]
    }
}
```

## 🧠 Cross-Call Learning Feature

The system's key innovation is **intelligent memory retention** across customer interactions. Each call generates a **Memory Box** containing:

- **Deliverables**: Key outcomes and commitments from the call
- **Improvement Areas**: Targeted coaching points for future interactions

This memory is stored with the customer's email as the primary key. When the same customer calls again, the system retrieves this context, enabling agents to pick up unresolved issues and personalize their response.

## 🔒 Security Considerations

- OpenAI API keys stored securely as environment variables
- AWS IAM roles follow principle of least privilege
- DynamoDB tables use encryption at rest
- API Gateway endpoints should implement authentication

## 📊 Monitoring & Analytics

### CloudWatch Integration
- Lambda function execution logs
- DynamoDB operation metrics
- API Gateway request/response tracking
- Error rate and latency monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/analytics-enhancement`)
3. Commit your changes (`git commit -m 'Add sentiment analysis improvements'`)
4. Push to the branch (`git push origin feature/analytics-enhancement`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions: please contact jeffry.code@gmail.com