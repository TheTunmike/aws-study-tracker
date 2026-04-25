"""
AWS Study Tracker — Lambda Function
Handles all API operations: save/load tracker data per user.
DynamoDB table: StudyTrackerData
  PK: userId (from Cognito sub claim)
  SK: dataKey (e.g. 'streak', 'exams', 'week1-d1-checks', etc.)
  value: JSON string of the data
  updatedAt: ISO timestamp
"""

import json
import boto3
import os
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ.get('TABLE_NAME', 'StudyTrackerData')
table = dynamodb.Table(TABLE_NAME)

CORS_HEADERS = {
    'Access-Control-Allow-Origin': os.environ.get('ALLOWED_ORIGIN', '*'),
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS',
    'Content-Type': 'application/json'
}


def response(status, body):
    return {
        'statusCode': status,
        'headers': CORS_HEADERS,
        'body': json.dumps(body)
    }


def get_user_id(event):
    """Extract userId from Cognito JWT claims (set by API Gateway authorizer)."""
    try:
        claims = event['requestContext']['authorizer']['claims']
        return claims['sub']  # Cognito unique user ID
    except (KeyError, TypeError):
        return None


def handler(event, context):
    method = event.get('httpMethod', '')
    path = event.get('path', '')

    # CORS preflight
    if method == 'OPTIONS':
        return response(200, {})

    user_id = get_user_id(event)
    if not user_id:
        return response(401, {'error': 'Unauthorized'})

    # GET /data — load ALL keys for this user
    if method == 'GET' and path == '/data':
        return load_all(user_id)

    # GET /data/{key} — load one key
    if method == 'GET' and path.startswith('/data/'):
        key = path[len('/data/'):]
        return load_one(user_id, key)

    # POST /data — save one or many keys
    if method == 'POST' and path == '/data':
        body = json.loads(event.get('body') or '{}')
        return save_data(user_id, body)

    # DELETE /data/{key} — delete one key
    if method == 'DELETE' and path.startswith('/data/'):
        key = path[len('/data/'):]
        return delete_key(user_id, key)

    return response(404, {'error': 'Not found'})


def load_all(user_id):
    """Load all data keys for a user."""
    try:
        result = table.query(
            KeyConditionExpression=Key('userId').eq(user_id)
        )
        data = {}
        for item in result.get('Items', []):
            data[item['dataKey']] = json.loads(item['value'])
        return response(200, {'data': data})
    except Exception as e:
        return response(500, {'error': str(e)})


def load_one(user_id, key):
    """Load a single key for a user."""
    try:
        result = table.get_item(Key={'userId': user_id, 'dataKey': key})
        item = result.get('Item')
        if not item:
            return response(200, {'data': None})
        return response(200, {'data': json.loads(item['value'])})
    except Exception as e:
        return response(500, {'error': str(e)})


def save_data(user_id, body):
    """Save one or many key-value pairs for a user.
    Body format: { "key": value } or { "items": [{"key": k, "value": v}, ...] }
    """
    try:
        now = datetime.now(timezone.utc).isoformat()

        # Batch save: {"items": [{"key": k, "value": v}]}
        if 'items' in body:
            with table.batch_writer() as batch:
                for item in body['items']:
                    batch.put_item(Item={
                        'userId': user_id,
                        'dataKey': item['key'],
                        'value': json.dumps(item['value']),
                        'updatedAt': now
                    })
            return response(200, {'saved': len(body['items'])})

        # Single save: {"key": k, "value": v}
        if 'key' in body and 'value' in body:
            table.put_item(Item={
                'userId': user_id,
                'dataKey': body['key'],
                'value': json.dumps(body['value']),
                'updatedAt': now
            })
            return response(200, {'saved': 1})

        return response(400, {'error': 'Body must have "key"+"value" or "items" array'})

    except Exception as e:
        return response(500, {'error': str(e)})


def delete_key(user_id, key):
    """Delete a single key for a user."""
    try:
        table.delete_item(Key={'userId': user_id, 'dataKey': key})
        return response(200, {'deleted': key})
    except Exception as e:
        return response(500, {'error': str(e)})
