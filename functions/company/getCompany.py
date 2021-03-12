import boto3
import botocore.exceptions
import json
import decimal
from boto3.dynamodb.conditions import Attr, Key

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
table = dynamodb.Table('Companies')
personTable = dynamodb.Table('Person')
emailTable = dynamodb.Table('emailTracker')


def personName(id):
    responsePerson = personTable.query(
        KeyConditionExpression=Key('id').eq(id)
    )
     # Ensure user record exists
    personRecord = responsePerson['Items'][0]
    if personRecord is None:
        return exception('No user record found: ' + id)
    return personRecord["givenName"] + " " + personRecord["familyName"]

def personAvatar(id):
    responsePerson = personTable.query(
        KeyConditionExpression=Key('id').eq(id)
    )
     # Ensure user record exists
    personRecord = responsePerson['Items'][0]
    if personRecord is None:
        return exception('No user record found: ' + id)
    if "photoURL" in personRecord:
        return personRecord["photoURL"]
    return None


def getEmailData(id, period):
    scanResponse = emailTable.scan(
            FilterExpression = Attr('companyID').eq(id) & Attr("reportingPeriod").eq(period),
            ProjectionExpression = 'emailType, eventType, receiver, ccReceiver, #t',
            ExpressionAttributeNames = {'#t': 'timestamp'}
        )
    return scanResponse["Items"]


# Get Company details using id
def lambda_handler(event, context):
    
    # Get Company id from parameters
    try:
        companyID = event["queryStringParameters"]['id']
    except Exception as e:
        return exception('Missing Company ID in parameters')

    
    try:
        readResponse = table.get_item(Key={'id': companyID})

        # Return data
        companyData = readResponse['Item']
        
        # Append Names for ease of rendering screen
        if "reportingContactID" in companyData:
            companyData["reportingContact"] = personName(companyData["reportingContactID"])
            personPhoto = personAvatar(companyData["reportingContactID"])
            if personPhoto:
                companyData["reportingContactPhoto"] = personPhoto
        if "nyaContactID" in companyData:
            companyData["nyaContact"] = personName(companyData["nyaContactID"])
            personPhoto = personAvatar(companyData["nyaContactID"])
            if personPhoto:
                companyData["nyaContactPhoto"] = personPhoto

        # Append Email to Reporting Data
        if "reporting" in companyData:
            for period in companyData["reporting"]:
                # Get Email History for company and Sort to get most recent action first
                emailHistory = getEmailData(companyData["id"], period)
                emailHistory.sort(key=lambda item : item["timestamp"], reverse=True)
                companyData["reporting"][period]["email"] = emailHistory
                if "reporterID" in companyData["reporting"][period]:
                    companyData["reporting"][period]["reporter"] = personName(companyData["reporting"][period]["reporterID"])
                # Get Comment data for company, enhance to include Reporter Name and Sort to get most recent first
                if "comments" in companyData["reporting"][period]:
                    commentData = []
                    for comment in companyData["reporting"][period]["comments"]:
                        if "reporterID" in comment:
                            comment["reporter"] = personName(comment["reporterID"])
                            commentData.append(comment)
                    commentData.sort(key=lambda item : item["timestamp"], reverse=True)
                    companyData["reporting"][period]["comments"] = commentData

        # Build response body
        responseData = {}
        responseData['success'] = True
        responseData['data'] = companyData
        return response(responseData)
        
    except Exception as e:
        return exception('Unable to retrieve company record: ' + str(e))
    
    
