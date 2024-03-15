import json
import boto3
import os


def lambda_handler(event, context):
    dynamodb = boto3.resource('dynamodb')

    DYNAMO_TABLE = os.environ['DYNAMO_TABLE']

    table = dynamodb.Table(DYNAMO_TABLE)

    response = table.scan()

    return {
        'statusCode': 200,
        'body': json.dumps(response),
        'headers': {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
        }
    }
