import boto3
import botocore.exceptions
import json
from boto3.dynamodb.conditions import Key
from datetime import datetime
import dateutil.parser

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
    
def noChange(): 
    # Response for no change in data
    return {
        'statusCode': 204
    }


dynamodb = boto3.resource('dynamodb')
personTable = dynamodb.Table('Person')
companyTable = dynamodb.Table('Company')

def getCompanyName(id):
    responseCompany = companyTable.query(
        KeyConditionExpression=Key('id').eq(id)
    )
    # Ensure Company record exists
    try:
        companyRecord = responseCompany['Items'][0]
    except Exception as e:
        return exception('No company record found: ' + id)
    return companyRecord["name"]

def personName(person):
    returnData = ""
    if "givenName" in person:
        returnData = person['givenName']
    if "familyName" in person:
        if len(returnData) > 0:
            returnData += " "
        returnData += person['familyName']
    return returnData


def lambda_handler(event, context):
    # Get Person id from either parameter or token if not specified
    personID = None
    try:
        personID = event['queryStringParameters']['id']
    except:
        try:
            personID = event['requestContext']['authorizer']['jwt']['claims']['cognito:username']
        except Exception as e:
            return exception('Missing person name in parameters. Please check API configuration.' + str(e))
    # Get timestamp if passed
    timestamp = None
    if "timestamp" in event['queryStringParameters']:
        timestamp = event['queryStringParameters']['timestamp']

    try:
        readResponse = personTable.get_item(Key={'id': personID})

        # Ensure person record exists
        try:
            personRecord = readResponse['Item']
        except:
            return exception('No person record found: ' + personID)
        
        # Check for no update
        if timestamp != None:
            if "updatedOn" in personRecord:
                lastUpdate = dateutil.parser.isoparse(personRecord["updatedOn"])
                checkTimestamp = dateutil.parser.isoparse(timestamp)
                if (checkTimestamp >= lastUpdate):
                    return noChange()
                    
        # Build response body
        personData = {}
        # Control Data
        personData['id'] = personID
        if 'updatedOn' in personRecord:
            personData['updatedOn'] = personRecord['updatedOn']
        else: 
            personData['updatedOn'] = "2020-01-01T00:00:00"
        # Basic Data
        if 'type' in personRecord:
            personData['type'] = personRecord['type']
        if 'givenName' in personRecord:
            personData['givenName'] = personRecord['givenName']
        if 'familyName' in personRecord:
            personData['familyName'] = personRecord['familyName']
        if len(personName(personRecord)) > 0:
            personData['personName'] = personName(personRecord)
        if 'photoURL' in personRecord:
            personData['photoURL'] = personRecord['photoURL']
        if 'email' in personRecord:
            personData['email'] = personRecord['email']
        if 'phone' in personRecord:
            personData['phone'] = personRecord['phone']
        if 'address' in personRecord:
            personData['address'] = personRecord['address']
        if 'city' in personRecord:
            personData['city'] = personRecord['city']
        if 'state' in personRecord:
            personData['state'] = personRecord['state']
        if 'zip' in personRecord:
            personData['zip'] = personRecord['zip']
        if 'location' in personRecord:
            personData['location'] = personRecord['location']
        elif 'city' in personRecord and 'state' in personRecord:
            personData['location'] = personRecord['city'] + ', ' + personRecord['state']

        # Organizational Data
        if 'isAngel' in personRecord:
            personData['isAngel'] = personRecord['isAngel']
        else:
            personData['isAngel'] = False
        if 'companyID' in personRecord:
            personData['companyID'] = personRecord['companyID']
            personData['company'] = getCompanyName(personRecord['companyID'])
        if 'title' in personRecord:
            personData['title'] = personRecord['title']
        if 'companyID' in personRecord:
            personData['companyID'] = personRecord['companyID']

        # Professional Data
        if 'linkedIn' in personRecord:
            personData['linkedIn'] = personRecord['linkedIn']
        if 'bio' in personRecord:
            personData['bio'] = personRecord['bio']

        # Build response body
        responseData = {}
        responseData['success'] = True
        responseData['data'] = personData

        # Return data
        return response(responseData)
    except Exception as e:
        return exception('Unable to retrieve person record: ' + str(e))