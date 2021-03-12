import boto3
import botocore.exceptions
import json
import re
import datetime
from decimal import Decimal

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


# Process update Person record
def lambda_handler(event, context):
    dynamodb = boto3.resource('dynamodb')
    personTable = dynamodb.Table('Person')

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
        
        # Update Person Record
        updateExpression = "SET updatedOn = :u"
        expressionAttributeValues = {':u': datetime.datetime.now().isoformat()}
        expressionAttributeNames = {}
        
        # Control Data
        if 'type' in updatedPersonRecord.keys():
            updateExpression+=", #t= :t"
            expressionAttributeValues[":t"]=updatedPersonRecord["type"]            
            expressionAttributeNames["#t"]="type"
        if 'status' in updatedPersonRecord.keys():
            updateExpression+=", #s= :s"
            expressionAttributeValues[":s"]=updatedPersonRecord["status"]            
            expressionAttributeNames["#s"]="status"

        # Basic Data
        if 'familyName' in updatedPersonRecord.keys():
            updateExpression+=", familyName= :fn"
            expressionAttributeValues[":fn"]=updatedPersonRecord["familyName"]
        if 'givenName' in updatedPersonRecord.keys():
            updateExpression+=", givenName= :gn"
            expressionAttributeValues[":gn"]=updatedPersonRecord["givenName"]
        if 'photoURL' in updatedPersonRecord.keys():
            updateExpression+=", photoURL= :pu"
            expressionAttributeValues[":pu"]=updatedPersonRecord["photoURL"]
        if 'email' in updatedPersonRecord.keys():
            if not valid_email(updatedPersonRecord["email"]):
                return exception('Unable to update Person record, invalid email: ' + str(updatedPersonRecord["email"]))
            updateExpression+=", email= :e"
            expressionAttributeValues[":e"]=updatedPersonRecord["email"]
        if 'phone' in updatedPersonRecord.keys():
            updateExpression+=", phone= :p"
            expressionAttributeValues[":p"]=updatedPersonRecord["phone"]
        if 'address' in updatedPersonRecord.keys():
            updateExpression+=", address= :add"
            expressionAttributeValues[":add"]=updatedPersonRecord["address"]
        if 'city' in updatedPersonRecord.keys():
            updateExpression+=", city= :c"
            expressionAttributeValues[":c"]=updatedPersonRecord["city"]
        if 'zip' in updatedPersonRecord.keys():
            updateExpression+=", zip= :z"
            expressionAttributeValues[":z"]=updatedPersonRecord["zip"]
        if 'state' in updatedPersonRecord.keys():
            updateExpression+=", #st= :st"
            expressionAttributeValues[":st"]=updatedPersonRecord["state"]
            expressionAttributeNames["#st"]="state"
        if 'location' in updatedPersonRecord.keys():
            updateExpression+=", #l= :l"
            expressionAttributeValues[":l"]=updatedPersonRecord["location"]
            expressionAttributeNames["#l"]="location"
            
        # Organization Data
        if 'companyID' in updatedPersonRecord.keys():
            updateExpression+=", companyID= :cid"
            expressionAttributeValues[":cid"]=updatedPersonRecord["companyID"]
        if 'title' in updatedPersonRecord.keys():
            updateExpression+=", title= :ttl"
            expressionAttributeValues[":ttl"]=updatedPersonRecord["title"]
        if 'isAngel' in updatedPersonRecord.keys():
            updateExpression+=", isAngel= :ia"
            expressionAttributeValues[":ia"]=updatedPersonRecord["isAngel"]
        
        
        # Professional Data
        if 'bio' in updatedPersonRecord.keys():
            updateExpression+=", bio= :b"
            expressionAttributeValues[":b"]=updatedPersonRecord["bio"]
        if 'linkedIn' in updatedPersonRecord.keys():
            updateExpression+=", linkedIn= :li"
            expressionAttributeValues[":li"]=updatedPersonRecord["linkedIn"]

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
        responseData['data'] = returnData["Attributes"]
        responseData['success'] = True

        # Return data
        return response(responseData)
    except Exception as e:
        return exception('Unable to update Person record: ' + str(e))


def valid_email(email):
    return bool(re.search(r"^[\w\.\+\-]+\@[\w]+\.[a-z]{2,3}$", email))