from botocore.vendored import requests
import boto3
import json
import os
import re

HERE_API_APP_ID = os.environ.get('HERE_APP_ID')
HERE_API_APP_CODE = os.environ.get('HERE_APP_CODE')

S3_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
S3_SECRET_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
S3_BUCKET = 'cycling-routes-data-process'

GEOCODE_URL = 'https://geocoder.cit.api.here.com/6.2/geocode.json'
CALCULATEROUTE_URL = 'https://route.cit.api.here.com/routing/7.2/calculateroute.json'
WEATHER_URL = 'https://weather.cit.api.here.com/weather/1.0/report.json'
BATCH_URL = 'https://batch.geocoder.cit.api.here.com/6.2/jobs'


def weather():
    params = {
        'app_id': HERE_API_APP_ID,
        'app_code': HERE_API_APP_CODE,
        'latitude': '-27.468668',
        'longitude': '153.025997',
        'product': 'forecast_7days_simple'
    }
    request = requests.get(WEATHER_URL, params=params)
    json = request.json()
    return json

def geocode(searchtext):
    params = {
        'app_id': HERE_API_APP_ID,
        'app_code': HERE_API_APP_CODE,
        'searchtext': searchtext
    }
    request = requests.get(GEOCODE_URL, params=params)
    json = request.json()
    return json['Response']['View'][0]['Result'][0]['Location']['DisplayPosition']

def calculateroute(waypoint0, waypoint1):
    wp0 = geocode(waypoint0)
    wp1 = geocode(waypoint1)

    params = {
        'app_id': HERE_API_APP_ID,
        'app_code': HERE_API_APP_CODE,
        'waypoint0': '%s,%s' % (wp0['Latitude'], wp0['Longitude']),
        'waypoint1': '%s,%s' % (wp1['Latitude'], wp1['Longitude']),
        'mode': 'fastest;bicycle;traffic:enabled;boatFerry:-1',
        'routeattributes': 'shape',
        'maneuverattributes': 'roadName,shape,nextRoadName'
    }
    request = requests.get(CALCULATEROUTE_URL, params=params)
    return request.json()

def create_batch(route, time):
    params = {
        'app_id': HERE_API_APP_ID,
        'app_code': HERE_API_APP_CODE,
        'action': 'run',
        'gen': 8,
        'header': True,
        'mode': 'retrieveAddresses',
        'mailto': 'success@hogyanszavazzakkulfoldrol.com',
        'maxresults': 1,
        'indelim': '|',
        'outdelim': '|',
        'outcols': 'displayLatitude,displayLongitude,distance,locationLabel,houseNumber,street,district,city,postalCode,county,state,country',
        'outputCombined': False
    }
    data = ["recId|prox"]
    c = 1
    for shape in route['response']['route'][0]['shape']:
        data.append("%04d|%s,250" % (c, shape))
        c += 1

    print "\n".join(data)

    response = requests.post(BATCH_URL, params=params, data="\n".join(data))
    batch_id = re.search(r'<RequestId>(.*)</RequestId>', response.text).group(1)
    client = boto3.client('s3')
    # HERE doesn't give us access to weather :(
    # forecast = weather()
    # print(forecast)
    # print client
    route['time_and_date'] = time
    ret = client.put_object(ACL='public-read', Body=json.dumps(route, indent=4), Bucket=S3_BUCKET, Key='%s.route.json' % batch_id)

    print 'BATCH'
    print batch_id
    print response.text
    print 'END BATCH'
    return batch_id

def calculaterouteGET(json_input, context):
    route = calculateroute(json_input['queryStringParameters']['from'], json_input['queryStringParameters']['to'])

    time_and_date = json_input['queryStringParameters']['time']
    batch = create_batch(route, time_and_date)
    print('FINISHED')

    result = {
        'response': route['response'],
        'jobId': batch
    }

    # we will get the id from the batch and create an s3 bucket
    return {
        'statusCode': 200,
        'body': json.dumps(result),
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
    }
