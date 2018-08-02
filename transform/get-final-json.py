from botocore.vendored import requests
import boto3
import json
import os
import io
import re
import gzip
import zlib
import cStringIO

S3_OUTPUT_BUCKET = 'cycling-route-risks'

def lambda_handler(event, context):
    key = event['Records'][0]['s3']['object']['key']
    bucket =  event['Records'][0]['s3']['bucket']['name']
    print(key)
    s3 = boto3.client('s3')
    s3_batch_prediction = s3.get_object(Bucket=bucket, Key=key)['Body'].read()
    stream=io.BytesIO(s3_batch_prediction)
    file = gzip.GzipFile(fileobj=stream).read()
    legs = file.splitlines()
    legs.pop(0)
    print('streaming')
    # print(file)
    batch_content = []
    for leg in legs:
        item = leg.split(',')
        number = [item[0], float(item[1])]
        # print(number)
        batch_content.append(number)
    print(batch_content)
    # file = z.read(fileName)
    # get original route
    id = key.split('/')[0]
    s3_route_object = s3.get_object(Bucket=bucket, Key='%s.route.json' % id)
    route_content = s3_route_object['Body'].read()
    route_data = json.loads(route_content)
    route_data['predictions'] = batch_content
    data = json.dumps(route_data)
    ret = s3.put_object(ACL='public-read', Body=data, Bucket=S3_OUTPUT_BUCKET, Key='%s.risks.json' % id)
    return 'OK'
