import json
import boto3
from boto3.dynamodb.conditions import Key
import datetime


DOMAIN = "https://www.simon50.com/"

dynamodb = boto3.resource('dynamodb')
companyTable = dynamodb.Table('Company')
personTable = dynamodb.Table('Person')

def exception(e):
    # Response for errors
    status_code = 400
    return {
        'statusCode': status_code,
        'body': json.dumps({'errorMessage' : str(e)})
    }

def response(data): 
    # Response for success
    return {
        'statusCode': 200,
        'body': json.dumps(data)
    }


def lambda_handler(event, context):
    companyID = ""
    responseData = {}

    # Get data from parameters
    try:
        companyID = event["queryStringParameters"]['companyID']
    except Exception as e:
        return exception('Missing parameter: ' + str(e))
        
    # Get Data from Company and Person Records
    try:
        # Company Data
        companyResponse = companyTable.get_item(Key={'id': companyID})
        if 'Item' not in companyResponse:
            raise ValueError(f'Invalid company ID: {companyID}')
        companyData = companyResponse['Item']
        responseData['data'] = {'name': companyData['name']}

    except Exception as e:
        return exception('Unable to verify data: ' + str(e))
    
    responseData['success'] = True
    return response(responseData)