import boto3
import botocore.exceptions
import json
import decimal
from boto3.dynamodb.conditions import Attr, Key
from datetime import datetime
import dateutil.parser


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
    
def noChange(): 
    # Response for no change in data
    return {
        'statusCode': 204
    }


dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Company')
personTable = dynamodb.Table('Person')

personLookUp = {}

def personDetails(id):
    # check if we have looked this one up before
    if id in personLookUp:
        return personLookUp[id]

    # else Look up now
    responsePerson = personTable.query(
        KeyConditionExpression=Key('id').eq(id)
    )
     # Ensure user record exists
    personRecord = responsePerson['Items'][0]
    if personRecord is None:
        return exception('No user record found: ' + id)

    # populate data
    fullName = ''
    if "givenName" in personRecord:
        fullName = personRecord["givenName"] + " "
    if "familyName" in personRecord:
        fullName += personRecord["familyName"] 
    personLookUp[id] = {}
    personLookUp[id]["name"] = fullName
    personLookUp[id]["email"] = personRecord["email"] if ("email" in personRecord) else None
    personLookUp[id]["photoURL"] = personRecord["photoURL"] if ("photoURL" in personRecord) else None
    
    return personLookUp[id]

def personName(id):
    # check if we have looked this one up before
    if id in personLookUp:
        return personLookUp[id]["name"]
    else:
        return personDetails(id)["name"]

def personAvatar(id):
    # check if we have looked this one up before
    if id in personLookUp:
        return personLookUp[id]["photoURL"]
    else:
        return personDetails(id)["photoURL"]

def personEmail(id):
    # check if we have looked this one up before
    print("Get Email: " + id)
    if id in personLookUp:
        print("Alreadt got: ")
        print(personLookUp[id])
        return personLookUp[id]["email"]
    else:
        print("Add New: ")
        newP = personDetails(id)
        print(newP)
        return newP["email"]

def formatEmailData(emailData):
    returnedData = []
    for emailRecord in emailData:
        if "receiverID" in emailRecord:
            emailRecord["receiver"] = personEmail(emailRecord["receiverID"])
        if "ccReceiverID" in emailRecord:
            emailRecord["ccReceiver"] = personEmail(emailRecord["receiverID"])
        returnedData.append(emailRecord) 
    returnedData.sort(key=lambda item : item["timestamp"], reverse=True)
    return returnedData

# Get Company details using id
def lambda_handler(event, context):
    
    # Get Company id from parameters
    try:
        companyID = event["queryStringParameters"]['id']
    except Exception as e:
        return exception('Missing Company ID in parameters')
        
    # Get timestamp if passed
    timestamp = None
    if "timestamp" in event['queryStringParameters']:
        timestamp = event['queryStringParameters']['timestamp']
    
    try:
        readResponse = table.get_item(Key={'id': companyID})

        # Ensure company record exists
        try:
            companyData = readResponse['Item']
        except:
            return exception('No company record found: ' + companyID)

        # Check for no update
        if timestamp != None:
            if "updatedOn" in companyData:
                lastUpdate = dateutil.parser.isoparse(companyData["updatedOn"])
                checkTimestamp = dateutil.parser.isoparse(timestamp)
                if (checkTimestamp >= lastUpdate):
                    return noChange()

        # Return data
        if "updatedOn" not in companyData:
            companyData['updatedOn'] = "2020-01-01T00:00:00"

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
                if "email" in companyData["reporting"][period]:
                    # Format Email History with email addresses & Sort to get most recent action first
                    companyData["reporting"][period]["email"] = formatEmailData(companyData["reporting"][period]["email"])
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
    
    
