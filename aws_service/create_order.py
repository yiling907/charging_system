import json
import boto3
import requests
import os
from datetime import datetime, timedelta

sqs = boto3.client("sqs")
cloudwatch_events = boto3.client("events")

CHARGER_STATUS_CHANGE_QUEUE_URL = os.environ["CHARGER_STATUS_CHANGE_QUEUE_URL"]
UPDATE_PAYMENT_STATUS_API = os.environ["UPDATE_PAYMENT_STATUS_API"]
UPDATE_CHARGER_STATUS_API = os.environ["UPDATE_CHARGER_STATUS_API"]
AWS_REGION = os.environ["AWS_REGION"]
AWS_ACCOUNT_ID = os.environ["AWS_ACCOUNT_ID"]
SCHEDULED_UPDATE_LAMBDA_ARN = os.environ["SCHEDULED_UPDATE_LAMBDA_ARN"]


def handler(event, context):
    request_body = json.loads(event["body"])
    record_id = request_body.get("recordId")
    timeout_minutes = request_body.get("chargingTime")
    request_body.get("paymentToken")
    charger_id = request_body.get("chargerId")

    update_payment_status(record_id)

    send_sqs_message(charger_id, "charging")

    create_scheduled_task(charger_id, timeout_minutes)

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(
            {
                "message": "created order",
                "record_id": record_id,
                "scheduled_timeout_minutes": timeout_minutes,
            }
        ),
    }


def update_payment_status(record_id):
    headers = {"Content-Type": "application/json"}
    response = requests.post(
        UPDATE_PAYMENT_STATUS_API + record_id + "/set_paid/", headers=headers
    )
    response.raise_for_status()
    return response.json()


def update_charger_status(charger_id):
    headers = {"Content-Type": "application/json"}
    response = requests.post(
        UPDATE_CHARGER_STATUS_API + charger_id + "/set_inactive/", headers=headers
    )
    response.raise_for_status()
    return response.json()


def send_sqs_message(charger_id, status):
    message_body = json.dumps(
        {
            "order_id": charger_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    )
    sqs.send_message(
        QueueUrl=CHARGER_STATUS_CHANGE_QUEUE_URL,
        MessageBody=message_body,
        MessageAttributes={
            "OrderId": {"DataType": "String", "StringValue": charger_id},
            "Status": {"DataType": "String", "StringValue": status},
        },
    )


def create_scheduled_task(charger_id, timeout_minutes):
    rule_name = f"charger-timeout-rule-{charger_id}"

    schedule_time = datetime.utcnow() + timedelta(minutes=timeout_minutes)

    cron_expression = f"cron({schedule_time.minute} {schedule_time.hour} {schedule_time.day} {schedule_time.month} ? {schedule_time.year})"

    cloudwatch_events.put_rule(
        Name=rule_name,
        ScheduleExpression=cron_expression,
        State="ENABLED",
        Description=f"Order {charger_id} timeout check (auto-delete after execution)",
    )

    target_lambda_arn = SCHEDULED_UPDATE_LAMBDA_ARN
    cloudwatch_events.put_targets(
        Rule=rule_name,
        Targets=[
            {
                "Id": f"charger-target-{charger_id}",
                "Arn": target_lambda_arn,
                "Input": json.dumps(
                    {"charger_id": charger_id, "target_status": "idle"}
                ),
            }
        ],
    )

    lambda_client = boto3.client("lambda")
    try:
        lambda_client.add_permission(
            FunctionName=target_lambda_arn.split(":")[-1],
            StatementId=f"allow-cloudwatch-{rule_name}",
            Action="lambda:InvokeFunction",
            Principal="events.amazonaws.com",
            SourceArn=f"arn:aws:events:{AWS_REGION}:{AWS_ACCOUNT_ID}:rule/{rule_name}",
        )
    except lambda_client.exceptions.ResourceConflictException:
        pass
