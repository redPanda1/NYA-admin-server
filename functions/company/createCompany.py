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
companyTable = dynamodb.Table('Company')

# Update Company record
def lambda_handler(event, context):
    # Extract data from body
    if not 'body' in event:
        return exception('Invalid Data. No Company data specified in body')
    newCompanyRecord = {}
    try:
        newCompanyRecord = json.loads(event['body'])
        # newCompanyRecord = event['body']
    except Exception as e: 
        return exception('Invalid Data. Invalid Company data specified in body: ' + str(e))
        
    # Validate Data
    if "name" not in newCompanyRecord:
        return exception('Invalid Data. Please specify a company name')
        
    try:
        # Create New Company Record
        newCompanyRecord["id"] = str(uuid.uuid4())
        newCompanyRecord["status"] = "active"
        newCompanyRecord["createdOn"] = datetime.datetime.now().isoformat()
        newCompanyRecord["updatedOn"] = datetime.datetime.now().isoformat()

        createCompanyResponse = companyTable.put_item(Item=newCompanyRecord)

    except Exception as e:
        return exception('Unable to create Company record: ' + str(e))

    # Build response body
    responseData = {}
    responseData['success'] = True
    responseData['data'] = newCompanyRecord
    return response(responseData)