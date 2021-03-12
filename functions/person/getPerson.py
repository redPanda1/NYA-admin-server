import boto3
import botocore.exceptions
import json
from boto3.dynamodb.conditions import Key

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

dynamodb = boto3.resource('dynamodb')
personTable = dynamodb.Table('Person')
companyTable = dynamodb.Table('Companies')

def getCompanyName(id):
    responseCompany = companyTable.query(
        KeyConditionExpression=Key('id').eq(id)
    )
     # Ensure user record exists
    companyRecord = responseCompany['Items'][0]
    if companyRecord is None:
        return exception('No company record found: ' + id)
    if "name" not in companyRecord:
        return "name missing"
    return companyRecord["name"]



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

    try:
        responsePerson = personTable.query(
            KeyConditionExpression=Key('id').eq(personID)
        )
    
        # Ensure person record exists
        personRecord = responsePerson['Items'][0]
        if personRecord is None:
            return exception('No person record found')
        
        # Build response body
        personData = {}
        personData['id'] = personID
        # Basic Data
        if 'type' in personRecord:
            personData['type'] = personRecord['type']
        if 'givenName' in personRecord:
            personData['givenName'] = personRecord['givenName']
        if 'familyName' in personRecord:
            personData['familyName'] = personRecord['familyName']
        if 'givenName' in personRecord or 'familyName' in personRecord:
            personData['personName'] = (personRecord['givenName'] + " " + personRecord['familyName']).strip()
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