import boto3
import json
import os


def handler(event, context):
    sfn = boto3.client('stepfunctions')
    statemachine = os.environ['STATEMACHINE']
    for record in event['Records']:
        message = json.loads(record["body"])
        name = message["name"]
        input = {"symbol": message["symbol"], "security": message["security"],
                 "sector": message["sector"], "date": message["date"]}
        sfn.start_execution(
            stateMachineArn=statemachine,
            name=name,
            input=json.dumps(input),
        )
