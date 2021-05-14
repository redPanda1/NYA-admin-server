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
    personID = ""
    reportingPeriod = ""
    reportingData = {}
    responseData = {}


    # Get data from parameters
    try:
        personID = event["queryStringParameters"]['personID']
    except Exception as e:
        return exception('Missing parameter: ' + str(e))
        
    # Get Data from Person Record
    try:
        # Person Data - check exists and is an Angel
        personResponse = personTable.get_item(Key={'id': personID})
        if 'Item' not in personResponse:
            raise ValueError(f'Invalid person ID: {personID}')
        memberRecord = personResponse['Item']
        if not memberRecord.get("isAngel"):
            raise ValueError(f'Person is not a member: {personID}')

        # Format return data
        memberData = {}
        memberName = ""
        if "givenName" in memberRecord:   
            memberName = memberRecord.get("givenName")
        if "familyName" in memberRecord:   
            memberName += " "
            memberName += memberRecord.get("familyName")
        memberName.strip()
        memberData["name"] = memberName
        
        if "bio" in memberRecord:
            memberData["bio"] = memberRecord.get("bio")
        if "photoURL" in memberRecord:
            memberData["photoURL"] = memberRecord.get("photoURL")
        if "linkedIn" in memberRecord:
            memberData["linkedIn"] = memberRecord.get("linkedIn")
        if "experience" in memberRecord:
            memberData["experience"] = memberRecord.get("experience")
        if "interests1" in memberRecord:
            memberData["interests1"] = memberRecord.get("interests1")
        if "interests2" in memberRecord:
            memberData["interests2"] = memberRecord.get("interests2")
        
    except Exception as e:
        return exception('Unable to verify data: ' + str(e))
    

    responseData['success'] = True
    responseData['data'] = memberData
    return response(responseData)