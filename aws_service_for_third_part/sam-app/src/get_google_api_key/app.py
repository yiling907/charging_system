import json
from typing import Any

import boto3
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)


def lambda_handler(event, context):
    secret_name = "google_api_key"
    client = get_aws_client()
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        logger.error(e)
        raise e
    logger.info(get_secret_value_response)
    secret = get_secret_value_response["SecretString"]

    return {
        "statusCode": 200,
        "body": json.dumps({"google_maps_api_key": secret}),
        "headers": {
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Origin": "https://t0oy2j75f0.execute-api.us-east-1.amazonaws.com",
            "Access-Control-Allow-Methods": "POST, GET",
        },
    }


def get_aws_client() -> Any:
    region_name = "us-east-1"
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)
    logger.info(client)
    return client
