import boto3
import botocore.exceptions
import decimal
import json
from boto3.dynamodb.conditions import Attr

def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError
    
def exception(e):
    # Response for errors
    status_code = 400
    return {
        'statusCode': status_code,
        'body': json.dumps({'errorMessage' : str(e)}, default=decimal_default)
    }

def response(data): 
    # Response for success
    return {
        'statusCode': 200,
        'body': json.dumps(data, default=decimal_default)
    }


dynamodb = boto3.resource('dynamodb')
personTable = dynamodb.Table('Person')

def lambda_handler(event, context):
    
    # Get filter from parameters
    try:
        typeFilter = event["queryStringParameters"]['status']
    except Exception as e:
        typeFilter = None

    try:
        if typeFilter is not None:
            scanResponse = personTable.scan(
                FilterExpression = Attr('status').contains(typeFilter) ,
                ProjectionExpression = 'id, photoURL, familyName, givenName, isAngel, company, email, #l, #s, #t, city, #st',
                ExpressionAttributeNames = {'#s': 'status', '#l': 'location', '#t': 'title', '#st': 'state'}
            )
        else:
            scanResponse = personTable.scan(
                ProjectionExpression = 'id, photoURL, familyName, givenName, isAngel, company, email, #l, #s, #t, city, #st',
                ExpressionAttributeNames = {'#s': 'status', '#l': 'location', '#t': 'title', '#st': 'state'}
            )

        # Return data
        people = scanResponse['Items']
        # Build response body
        responseData = {}
        responseData['success'] = True
        responseData['count'] = len(people)
        responseData['data'] = people
        return response(responseData)
        
    except Exception as e:
        return exception('Unable to retrieve Person records: ' + str(e))