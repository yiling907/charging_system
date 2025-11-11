# Use this code snippet in your app.
# If you need more information about configurations
# or implementing the sample code, visit the AWS docs:
# https://aws.amazon.com/developer/language/python/
from typing import Any

import boto3
from botocore.exceptions import ClientError
import json
import logging

logger = logging.getLogger(__name__)


def get_google_maps_api_key():

    secret_name = "google_api_key"
    client = get_aws_client()
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        logger.error(e)
        raise e
    logger.info(get_secret_value_response)
    secret = get_secret_value_response['SecretString']
    return secret


def get_aws_client() -> Any:
    region_name = "us-east-1"
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name,
        endpoint_url='http://localhost:4566',
        aws_access_key_id='localstack',
        aws_secret_access_key='localstack'
    )
    logger.info(client)
    return client
