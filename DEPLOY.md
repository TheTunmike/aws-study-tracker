# AWS Study Tracker — Deployment Guide

A full-stack serverless app on AWS. Deploy time: ~20 minutes.

## Architecture

```
Browser (index.html on S3/CloudFront)
    │  Cognito JWT token
    ▼
API Gateway (REST API, Cognito authorizer)
    │
    ▼
Lambda (Python 3.12) — handler.py
    │
    ▼
DynamoDB (userId + dataKey → value)
```

**AWS Services used:** S3, CloudFront, API Gateway, Lambda, DynamoDB, Cognito
**Monthly cost:** $0 (all within Free Tier for personal use)

---

## Prerequisites

1. AWS CLI installed and configured (`aws configure`)
2. AWS account with admin access (or permissions for the services above)

---

## Step 1 — Deploy the backend (CloudFormation)

```bash
# Clone / create your project folder
mkdir aws-study-tracker && cd aws-study-tracker

# Copy template.yaml and lambda_function.py into this folder

# Package the Lambda code
zip lambda.zip lambda_function.py

# Deploy the CloudFormation stack
aws cloudformation deploy \
  --template-file template.yaml \
  --stack-name study-tracker \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
      AppName=study-tracker \
      FrontendURL='*'
```

Wait ~2 minutes for CloudFormation to create all resources.

```bash
# Get your output values (you need these for Step 3)
aws cloudformation describe-stacks \
  --stack-name study-tracker \
  --query 'Stacks[0].Outputs' \
  --output table
```

Copy down:
- `ApiUrl` → e.g. `https://abc123.execute-api.us-east-1.amazonaws.com/prod`
- `UserPoolId` → e.g. `us-east-1_AbCdEfGhI`
- `UserPoolClientId` → e.g. `1a2b3c4d5e6f7g8h9i0j`

---

## Step 2 — Upload the Lambda function code

The CloudFormation template uses placeholder code. Replace it with the real function:

```bash
# Zip the real Lambda code
zip lambda.zip lambda_function.py

# Update the Lambda function
aws lambda update-function-code \
  --function-name study-tracker-api \
  --zip-file fileb://lambda.zip
```

---

## Step 3 — Configure the frontend

Open `index.html` and find the CONFIG block near the top of the `<script>`:

```javascript
const CONFIG = {
  apiUrl:     'YOUR_API_GATEWAY_URL',     // ← paste ApiUrl from Step 1
  userPoolId: 'YOUR_USER_POOL_ID',        // ← paste UserPoolId
  clientId:   'YOUR_COGNITO_CLIENT_ID',   // ← paste UserPoolClientId
  region:     'us-east-1',
};
```

Replace the three placeholder values with your real outputs.

---

## Step 4 — Host the frontend on S3 + CloudFront

You already have this setup from Project 1. Just add the tracker to your existing bucket:

```bash
# Upload to your existing S3 bucket
aws s3 cp index.html s3://YOUR-EXISTING-BUCKET/study-tracker/index.html \
  --content-type "text/html"

# Invalidate CloudFront cache so changes show immediately
aws cloudfront create-invalidation \
  --distribution-id YOUR-CLOUDFRONT-DISTRIBUTION-ID \
  --paths "/study-tracker/*"
```

Your tracker is now live at:
`https://YOUR-CLOUDFRONT-URL.cloudfront.net/study-tracker/index.html`

---

## Step 5 — Update CORS for production

Once you have your real CloudFront URL, update the stack to restrict CORS:

```bash
aws cloudformation deploy \
  --template-file template.yaml \
  --stack-name study-tracker \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
      AppName=study-tracker \
      FrontendURL='https://YOUR-CLOUDFRONT-URL.cloudfront.net'
```

---

## Step 6 — Push to GitHub

```bash
git init
git remote add origin https://github.com/YOUR-USERNAME/aws-study-tracker.git

# IMPORTANT: never commit real config values to public repos
# The CONFIG values are not sensitive (Cognito client IDs are public by design)
# but good practice to use environment variables in production

git add .
git commit -m "feat: full-stack study tracker with DynamoDB sync + Cognito auth"
git branch -M main
git push -u origin main
```

---

## How it works (for your README and interviews)

1. **User signs up / logs in** via Cognito (email + password, no extra setup needed)
2. **JWT token** is issued by Cognito and sent with every API request
3. **API Gateway** validates the JWT using the Cognito authorizer — unauthenticated requests are rejected automatically
4. **Lambda** reads the `sub` claim from the token (unique user ID) and uses it as the DynamoDB partition key
5. **DynamoDB** stores all user data as `{userId, dataKey, value}` — each checkbox, note, and table row is a separate item
6. **Frontend** writes to localStorage immediately (fast UI) then syncs to DynamoDB 800ms later (debounced — avoids hammering the API on every keystroke)
7. **On login**, all data is loaded from DynamoDB into the local cache — works across any device

---

## What this demonstrates (for your portfolio)

- **Serverless architecture** — no servers to manage, scales to zero
- **Authentication** — Cognito user pools, JWT tokens, API Gateway authorizer
- **NoSQL data modelling** — single-table DynamoDB design with composite keys
- **Infrastructure as Code** — CloudFormation template deploys everything in one command
- **CORS and API security** — proper cross-origin configuration
- **Frontend/backend integration** — async/await, fetch API, token-based auth
- **AWS services**: S3, CloudFront, API Gateway, Lambda, DynamoDB, Cognito (6 services in one project)

---

## Teardown (if needed)

```bash
# Empty the S3 bucket first (CloudFormation can't delete non-empty buckets)
aws s3 rm s3://YOUR-BUCKET/study-tracker/ --recursive

# Delete the stack (removes DynamoDB, Lambda, API Gateway, Cognito)
aws cloudformation delete-stack --stack-name study-tracker
```
