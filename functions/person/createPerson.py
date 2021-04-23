import boto3
import botocore.exceptions
import json
import datetime
import uuid


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

# Create Person record
def lambda_handler(event, context):
    # Extract data from body
    if not 'body' in event:
        return exception('Invalid Data. No Person data specified in body')
    newPersonRecord = {}
    try:
        newPersonRecord = json.loads(event['body'])
    except Exception as e: 
        return exception('Invalid Data. Invalid Person data specified in body: ' + str(e))
        
    # Validate Data
    if "email" not in newPersonRecord:
        return exception('Invalid Data. Please specify an email address')
    if "personName" not in newPersonRecord:
        return exception('Invalid Data. Please specify a name')
        
    # If a person Name has been specified, deconstruct givenName and familyName
    personName = newPersonRecord["personName"] 
    nameArray = personName.split(' ')
    if len(nameArray) == 2:
        newPersonRecord["givenName"] = nameArray[0]
        newPersonRecord["familyName"]=nameArray[1]
    elif len(nameArray) == 1:
        newPersonRecord["familyName"]=nameArray[0]
    elif len(nameArray) > 2:
        newPersonRecord["familyName"]=nameArray[len(nameArray) - 1]
        givenNames = ''
        for i in range(0, len(nameArray)-1):
            givenNames += nameArray[i]
            givenNames += ' '
        newPersonRecord["givenName"]=givenNames.strip()
    del newPersonRecord["personName"]
        
    try:
        # Create New Person Record
        newPersonRecord["id"] = str(uuid.uuid4())
        newPersonRecord["status"] = "created"
        newPersonRecord["createdOn"] = datetime.datetime.now().isoformat()
        newPersonRecord["updatedOn"] = datetime.datetime.now().isoformat()

        createPersonResponse = personTable.put_item(Item=newPersonRecord)
        
        # add back person name
        newPersonRecord["personName"] = personName

    except Exception as e:
        return exception('Unable to create Person record: ' + str(e))

    # Build response body
    responseData = {}
    responseData['success'] = True
    responseData['data'] = newPersonRecord
    return response(responseData)