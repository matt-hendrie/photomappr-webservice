import os
import boto3
import botocore

s3 = boto3.resource('photomappr-storage')

def image_exists(bucket_name, key):
    try:
        s3.Object(bucket_name=bucket_name, key=key).load()
        except botocore.exceptions.ClientError:
            return None

def tag_image(bucket_name, key):
    try:
        s3.Object(bucket_name=bucket_name, key=key).load()
        image_exists(bucket_name, key)
    except botocore.exceptions.ClientError:
        return None
    obj = s3.Object(bucket_name=bucket_name, key=key)
    obj_body = obj.get()['Body'].read

def lambda_handler(event, context):
    key = event('queryStringParameters').get('key', None)
    image_url = tag_image(os.environ['BUCKET_NAME'], key)

    return {
        'StatusCode' : 301,
        'body' : image_url
    }