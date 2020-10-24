import os
import boto3
import json
import base64
import random

s3 = boto3.resource('s3')
bucket = s3.Bucket('photomappr-storage')
def handler(event, context):
    file_content = base64.b64decode(event['content'])
    file_path = str(random.randint(1,100)) + ".jpg" 
    try:
        s3_response = bucket.put_object(Key=file_path, Body=file_content)
    except Exception as e:
        raise IOError(e)
    return {
        'statusCode': 200,
        'body': 'hi'
    }