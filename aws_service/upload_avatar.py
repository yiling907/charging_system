import base64
import json
import boto3
import os

s3 = boto3.client("s3")

BUCKET_NAME = os.environ["BUCKET_NAME"]


def handler(event, context):
    try:
        if event["isBase64Encoded"]:
            try:
                body = base64.b64decode(event["body"])
            except Exception:
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": "Invalid binary data"}),
                }
        user_id = json.loads(body).get("user_id")
        image = json.loads(body).get("image")
        file_name = user_id + "/" + json.loads(body).get("file_name")
        image_data = base64.b64decode(image)

        s3.delete_object(Bucket=BUCKET_NAME, Key=file_name)
        s3.put_object(
            Bucket=BUCKET_NAME, Key=file_name, Body=image_data, ContentType="image/png"
        )
        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": f"update {user_id}'s avatar, the store link is: s3://{BUCKET_NAME}/{file_name}",
                    "success": True,
                }
            ),
        }
    except Exception as e:
        return {"statusCode": 500, "body": str(e)}
