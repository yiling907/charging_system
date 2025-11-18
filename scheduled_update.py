import json
import boto3
import os
import requests

cloudwatch_events = boto3.client('events')

UPDATE_CHARGER_STATUS_API = os.environ['UPDATE_CHARGER_STATUS_API']
AWS_REGION = os.environ['AWS_REGION']
AWS_ACCOUNT_ID = os.environ['AWS_ACCOUNT_ID']
AWS_LAMBDA_FUNCTION_NAME = os.environ['AWS_LAMBDA_FUNCTION_NAME']


def handler(event, context):
    try:
        charger_id = event.get('charger_id')
        target_status = event.get('target_status')

        if not charger_id:
            raise ValueError('lost charger_id')

        update_order_status(charger_id)

        delete_scheduled_task(charger_id)

        return {
            'statusCode': 200,
            'body': json.dumps({'message': f'update {charger_id}status to {target_status}', 'success': True})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e), 'charger_id': charger_id if 'charger_id' in locals() else 'unknown'})
        }


def update_order_status(charger_id):
    headers = {'Content-Type': 'application/json'}
    response = requests.post(UPDATE_CHARGER_STATUS_API + charger_id + '/set_active/', headers=headers)
    response.raise_for_status()
    return response.json()


def delete_scheduled_task(charger_id):
    rule_name = f'charger-timeout-rule-{charger_id}'
    target_id = f'charger-target-{charger_id}'

    cloudwatch_events.remove_targets(Rule=rule_name, Ids=[target_id])

    cloudwatch_events.delete_rule(Name=rule_name)

    lambda_client = boto3.client('lambda')
    try:
        lambda_client.remove_permission(
            FunctionName=AWS_LAMBDA_FUNCTION_NAME,
            StatementId=f'allow-cloudwatch-{rule_name}'
        )
    except Exception as e:
        print(f"error when remove the permission：{str(e)}")
