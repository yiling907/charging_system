import base64
import json
import boto3
import os

s3 = boto3.client('s3')

BUCKET_NAME = os.environ['BUCKET_NAME']


def handler(event, context):
    try:
        request_body = json.loads(event['body'])
        user_id = request_body.get('user_id')
        image = request_body.get('image')
        file_name = user_id + '/' + request_body.get('file_name')

        image_data = base64.b64decode(image)

        s3.delete_object(Bucket=BUCKET_NAME, Key=file_name)
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=file_name,
            Body=image_data,
            ContentType='image/png'
        )
        return {
            'statusCode': 200,
            'body': json.dumps(
                {'message': f"update {user_id}\'s avatar, the store link is: s3://{BUCKET_NAME}/{file_name}",
                 'success': True})
        }
    except Exception as e:
        return {'statusCode': 500, 'body': str(e)}
