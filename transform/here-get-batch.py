from botocore.vendored import requests
import boto3
import json
import os
import io
import re
import zipfile

BATCH_RESULTS_URL = 'https://batch.geocoder.cit.api.here.com/6.2/jobs/%s/result'
HERE_APP_ID = os.environ.get('HERE_APP_ID')
HERE_APP_CODE = os.environ.get('HERE_APP_CODE')
SNS_SUCCESS_ARN = os.environ.get('SNS_SUCCESS_ARN')
S3_BUCKET = 'cycling-routes-data-process'

def get_result(id):
    params = {
        'app_id': HERE_APP_ID,
        'app_code': HERE_APP_CODE,
    }
    url = BATCH_RESULTS_URL % (id)
    print(url)
    response = requests.get(url, params=params)
    print(response)
    z = zipfile.ZipFile(io.BytesIO(response.content))
    file_name = z.infolist()[0].filename
    file_content = z.read(file_name)
    print(z)
    print(file_name)

    # SAVE file to csv
    s3 = boto3.client('s3')
    putFile = s3.put_object(ACL='public-read', Body=file_content, Bucket=S3_BUCKET, Key='%s.result.CSV' % id)

def publish_success(id):
    message = {"job-id": id}
    client = boto3.client('sns')
    response = client.publish(
        TargetArn=SNS_SUCCESS_ARN,
        Message=json.dumps({'default': json.dumps(message)}),
        MessageStructure='json'
    )

def lambda_handler(event, context):
    subject = event['Records'][0]['ses']['mail']['commonHeaders']['subject'];
    id = [x.strip() for x in subject.split(' ')][3]
    print('Getting ready to download data')
    get_result(id)
    publish_success(id)
    return 'Batch Results recieved and saved'
