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
companyTable = dynamodb.Table('Company')



# Update Company record
def lambda_handler(event, context):
    # Extract Query parameters & Validate
    if 'queryStringParameters' not in event:
        return exception('No query parameters in event - check API Gateway configuration')
    
    queryParams = event["queryStringParameters"]

    if not 'id' in queryParams:
        return exception('Invalid Parameters. Company ID not specified')
    if not 'body' in event:
        return exception('Invalid Data. No Company data specified in body')

    try:
        companyQuery = companyTable.get_item(Key={'id': queryParams['id']})
        
        # Ensure Company record exists
        if 'Item' not in companyQuery:
            return exception('No company record found: ' +  queryParams['id'])

        companyRecord = companyQuery['Item']
        
        updatedCompanyRecord = json.loads(event['body'])
        print(updatedCompanyRecord)
        
        
        # Update Company Record
        updateExpression = "SET updatedOn = :u"
        expressionAttributeValues = {':u': datetime.datetime.now().isoformat()}
        expressionAttributeNames = {}
        
        # Control Data
        if 'status' in updatedCompanyRecord.keys():
            updateExpression+=", #s= :s"
            expressionAttributeValues[":s"]=updatedCompanyRecord["status"]            
            expressionAttributeNames["#s"]="status"

        # Basic Data
        if 'name' in updatedCompanyRecord.keys():
            updateExpression+=", #nm= :nm"
            expressionAttributeValues[":nm"]=updatedCompanyRecord["name"]
            expressionAttributeNames["#nm"]="name"
        if 'sector' in updatedCompanyRecord.keys():
            updateExpression+=", #sec= :sec"
            expressionAttributeValues[":sec"]=updatedCompanyRecord["sector"]
            expressionAttributeNames["#sec"]="sector"
        if 'summary' in updatedCompanyRecord.keys():
            updateExpression+=", summary= :sum"
            expressionAttributeValues[":sum"]=updatedCompanyRecord["summary"]
        if 'logo' in updatedCompanyRecord.keys():
            updateExpression+=", logo= :l"
            expressionAttributeValues[":l"]=updatedCompanyRecord["logo"]
        if 'address' in updatedCompanyRecord.keys():
            updateExpression+=", #add= :add"
            expressionAttributeValues[":add"]=updatedCompanyRecord["address"]
            expressionAttributeNames["#add"]="address"
        if 'city' in updatedCompanyRecord.keys():
            updateExpression+=", city= :c"
            expressionAttributeValues[":c"]=updatedCompanyRecord["city"]
        if 'state' in updatedCompanyRecord.keys():
            updateExpression+=", #st= :st"
            expressionAttributeValues[":st"]=updatedCompanyRecord["state"]
            expressionAttributeNames["#st"]="state"
        if 'country' in updatedCompanyRecord.keys():
            updateExpression+=", country= :cnt"
            expressionAttributeValues[":cnt"]=updatedCompanyRecord["country"]
        if 'gustUrl' in updatedCompanyRecord.keys():
            updateExpression+=", gustUrl= :gu"
            expressionAttributeValues[":gu"]=updatedCompanyRecord["gustUrl"]

        # Contacts
        if 'nyaContactID' in updatedCompanyRecord.keys():
            updateExpression+=", nyaContactID= :nyaID"
            expressionAttributeValues[":nyaID"]=updatedCompanyRecord["nyaContactID"]
        if 'reportingContactID' in updatedCompanyRecord.keys():
            updateExpression+=", reportingContactID= :rptID"
            expressionAttributeValues[":rptID"]=updatedCompanyRecord["reportingContactID"]

    
        # Make sure syntax for update is correct (can't send empty expressionAttributeNames)
        if len(expressionAttributeNames) > 0:
            returnData = companyTable.update_item(Key={'id': queryParams['id']},
                                UpdateExpression=updateExpression,
                                ExpressionAttributeValues=expressionAttributeValues,
                                ExpressionAttributeNames=expressionAttributeNames,
                                ReturnValues="UPDATED_NEW")
        else:
            returnData = companyTable.update_item(Key={'id': queryParams['id']},
                        UpdateExpression=updateExpression,
                        ExpressionAttributeValues=expressionAttributeValues,
                        ReturnValues="UPDATED_NEW")

        # Build response body
        responseData = {}
        responseData['data'] = returnData["Attributes"]
        # enhance with company id
        responseData['data']['id'] = queryParams['id']
        responseData['success'] = True

        # Return data
        return response(responseData)
    except Exception as e:
        return exception('Unable to update Company record: ' + str(e))
