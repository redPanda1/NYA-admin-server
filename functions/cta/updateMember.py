import boto3
import botocore.exceptions
import json
import re
import datetime
from decimal import Decimal
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

# Update Person record
def lambda_handler(event, context):
    # Extract Query parameters & Validate
    if 'queryStringParameters' not in event:
        return exception('No query parameters in event - check API Gateway configuration')
    
    queryParams = event["queryStringParameters"]

    if not 'id' in queryParams:
        return exception('Invalid Parameters. Person ID not specified')
    if not 'body' in event:
        return exception('Invalid Data. No person data specified in body')

    try:
        personQuery = personTable.get_item(Key={'id': queryParams['id']})

        # Ensure Person record exists
        if 'Item' not in personQuery:
            return exception('No person record found: ' +  queryParams['id'])

        personRecord = personQuery['Item']
        updatedPersonRecord = json.loads(event['body'])
        # Dump body for audit purposes
        print('Data for person: ' +  queryParams['id'])
        print(updatedPersonRecord)
        
        # Update Person Record
        updateExpression = "SET updatedOn = :u"
        expressionAttributeValues = {':u': datetime.datetime.now().isoformat()}
        expressionAttributeNames = {}
        
        # Basic Data
        # If a person Name has been specified, deconstruct givenName and familyName
        if 'personName' in updatedPersonRecord.keys():
            nameArray = updatedPersonRecord["personName"].split(' ')
            if len(nameArray) == 2:
                updateExpression+=", givenName= :gn"
                expressionAttributeValues[":gn"]=nameArray[0]
                updateExpression+=", familyName= :fn"
                expressionAttributeValues[":fn"]=nameArray[1]
            elif len(nameArray) == 1:
                updateExpression+=", familyName= :fn"
                expressionAttributeValues[":fn"]=nameArray[0]
            elif len(nameArray) > 2:
                updateExpression+=", familyName= :fn"
                expressionAttributeValues[":fn"]=nameArray[len(nameArray) - 1]
                givenNames = ''
                for i in range(0, len(nameArray)-1):
                    givenNames += nameArray[i]
                    givenNames += ' '
                updateExpression+=", givenName= :gn"
                expressionAttributeValues[":gn"]=givenNames.strip()
        else:
            if 'familyName' in updatedPersonRecord.keys():
                updateExpression+=", familyName= :fn"
                expressionAttributeValues[":fn"]=updatedPersonRecord["familyName"]
            if 'givenName' in updatedPersonRecord.keys():
                updateExpression+=", givenName= :gn"
                expressionAttributeValues[":gn"]=updatedPersonRecord["givenName"]
        if 'photoURL' in updatedPersonRecord.keys():
            updateExpression+=", photoURL= :pu"
            expressionAttributeValues[":pu"]=updatedPersonRecord["photoURL"]
            
        # Professional Data
        if 'bio' in updatedPersonRecord.keys():
            updateExpression+=", bio= :bio"
            expressionAttributeValues[":bio"]=updatedPersonRecord["bio"]
        if 'linkedIn' in updatedPersonRecord.keys():
            updateExpression+=", linkedIn= :li"
            expressionAttributeValues[":li"]=updatedPersonRecord["linkedIn"]
        if 'experience' in updatedPersonRecord.keys():
            updateExpression+=", experience= :exp"
            expressionAttributeValues[":exp"]=updatedPersonRecord["experience"]
        if 'interests1' in updatedPersonRecord.keys():
            updateExpression+=", interests1= :int1"
            expressionAttributeValues[":int1"]=updatedPersonRecord["interests1"]
        if 'interests2' in updatedPersonRecord.keys():
            updateExpression+=", interests2= :int2"
            expressionAttributeValues[":int2"]=updatedPersonRecord["interests2"]

        # Make sure syntax for update is correct (can't send empty expressionAttributeNames)
        if len(expressionAttributeNames) > 0:
            returnData = personTable.update_item(Key={'id': queryParams['id']},
                                UpdateExpression=updateExpression,
                                ExpressionAttributeValues=expressionAttributeValues,
                                ExpressionAttributeNames=expressionAttributeNames,
                                ReturnValues="UPDATED_NEW")
        else:
            returnData = personTable.update_item(Key={'id': queryParams['id']},
                        UpdateExpression=updateExpression,
                        ExpressionAttributeValues=expressionAttributeValues,
                        ReturnValues="UPDATED_NEW")

        # Build response body
        responseData = {}
        responseData['success'] = True

        # Return data
        return response(responseData)
    except Exception as e:
        print('ERROR: Unable to update Person record: ' + str(e))
        return exception('Unable to update Person record: ' + str(e))

    return exception('ERROR: Unable to update Person record')