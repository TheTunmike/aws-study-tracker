# AWS Study Tracker

A full-stack serverless web application for tracking AWS certification study progress — with cross-device sync, authentication, and persistent cloud storage.

Built as part of my AWS certification journey (CLF-C02 ✅ → AIF-C01 → SAA-C03).

## Live Demo

[Click Here For Live Demo](https://d3i4clr9tshcxy.cloudfront.net)

## Architecture
![Architecture](./aws-study-tracker-architecture.svg)
Browser (S3 + CloudFront)
    │  Cognito JWT
    ▼
API Gateway  →  Lambda (Python)  →  DynamoDB
                     │
               Cognito User Pool
               (auth + JWT validation)
```

## AWS Services Used

| Service | Role |
|---|---|
| Amazon S3 | Frontend hosting |
| Amazon CloudFront | Global CDN + HTTPS |
| Amazon Cognito | User authentication + JWT tokens |
| Amazon API Gateway | REST API with Cognito authorizer |
| AWS Lambda | Business logic (Python 3.12) |
| Amazon DynamoDB | Persistent data store (single-table design) |

## Features

- **Real-time cross-device sync** — data saved to DynamoDB, loads on any device after login
- **Cognito authentication** — email/password sign-up, email verification, JWT-secured API
- **40-day structured study log** — expandable day cards with checklists and note fields
- **14 AWS AI service cards** — fill in as you study each service, rate your confidence
- **Practice exam tracker** — log scores, domain breakdown, running average
- **Project checklist** — step-by-step build tracker for all 5 hands-on projects
- **Weak topics log** — track wrong answers with status from ❌ New → ✅ Mastered
- **Job application tracker** — with LinkedIn optimisation checklist
- **Offline-first** — localStorage fallback when offline, syncs on reconnect

## Run Locally

```bash
# No build step needed — it's a single HTML file
open index.html
# or
python3 -m http.server 8080
```

Note: Without the backend configured, the app runs in local-only mode using localStorage.

## Deploy to AWS

See [DEPLOY.md](./DEPLOY.md) for full step-by-step instructions.

```bash
# One-command backend deploy
aws cloudformation deploy \
  --template-file template.yaml \
  --stack-name study-tracker \
  --capabilities CAPABILITY_NAMED_IAM

# Then update CONFIG in index.html with your outputs and upload to S3
```

**Cost:** $0/month (all within AWS Free Tier)

## Key Technical Concepts Demonstrated

- **Single-table DynamoDB design** — composite key `{userId, dataKey}` stores all data types
- **JWT-secured API** — API Gateway Cognito authorizer validates tokens on every request, no Lambda code needed for auth
- **Debounced writes** — 800ms debounce prevents hammering DynamoDB on every keystroke
- **Offline-first** — writes to localStorage immediately, syncs to DynamoDB asynchronously
- **Infrastructure as Code** — CloudFormation deploys all 6 AWS services in one command

## What I Learned Building This

> Fill this in honestly after you build it — interviewers will ask.
