import json
import boto3
from boto3.dynamodb.conditions import Key
import datetime
import uuid

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
    # Get data from parameters
    try:
        name = event["queryStringParameters"]['name']
        title = event["queryStringParameters"]['title']
        email = event["queryStringParameters"]['email']
        companyID = event["queryStringParameters"]['companyID']
    except Exception as e:
        return exception('Missing parameter: ' + str(e))

    try:
        # Create New Person Record
        newPersonRecord = {}
        nameArray = name.split(' ')
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
        newPersonRecord["id"] = str(uuid.uuid4())
        newPersonRecord["status"] = "created"
        newPersonRecord["createdOn"] = datetime.datetime.now().isoformat()
        newPersonRecord["updatedOn"] = datetime.datetime.now().isoformat()
        newPersonRecord["email"] = email
        newPersonRecord["title"] = title
        createPersonResponse = personTable.put_item(Item=newPersonRecord)
    except Exception as e:
        return exception('Unable to create Person record: ' + str(e))

    # Update company with new personID
    try:
        # Update Company Record
        updateExpression = "SET updatedOn = :u"
        expressionAttributeValues = {':u': datetime.datetime.now().isoformat()}
        updateExpression+=", reportingContactID= :rptID"
        expressionAttributeValues[":rptID"]=newPersonRecord["id"]

        returnData = companyTable.update_item(Key={'id': companyID},
                UpdateExpression=updateExpression,
                ExpressionAttributeValues=expressionAttributeValues,
                ReturnValues="NONE")
    except Exception as e:
        return exception('Unable to Update Company record: ' + str(e))
    
    # Response
    responseData = {}
    responseData['success'] = True
    return response(responseData)
