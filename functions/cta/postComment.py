import json
import boto3
from boto3.dynamodb.conditions import Key
import datetime


DOMAIN = "https://www.simon50.com/"

dynamodb = boto3.resource('dynamodb')
companyTable = dynamodb.Table('Company')
personTable = dynamodb.Table('Person')

def exception(e):
    # Response for errors
    status_code = 400
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({'errorMessage' : str(e)})
    }

def response(data): 
    # Response for success
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(data)
    }


def lambda_handler(event, context):
    companyID = ""
    personID = ""
    reportingPeriod = ""
    commentText = ""
    reportingData = {}
    responseData = {}

    # Get data from parameters
    try:
        companyID = event["queryStringParameters"]['companyID']
        personID = event["queryStringParameters"]['personID']
        reportingPeriod = event["queryStringParameters"]['period']
        commentText = event["queryStringParameters"]['comment']
    except Exception as e:
        return exception('Missing parameter: ' + str(e))

    # Get Data from Company and Person Records
    try:
        # Company Data
        companyResponse = companyTable.get_item(Key={'id': companyID})
        if 'Item' not in companyResponse:
            raise ValueError(f'Invalid company ID: {companyID}')
        companyData = companyResponse['Item']
        # personID = companyData['reportingContactID']

        # Person Data
        personResponse = personTable.get_item(Key={'id': personID})
        if 'Item' not in personResponse:
            raise ValueError(f'Invalid person ID: {personID}')
        contactPersonData = personResponse['Item']

    except Exception as e:
        return exception('Unable to verify data: ' + str(e))
    
    # Update Company Record
    try:
        reportingData = {}
        newComment = {}
        newComment["text"] = commentText
        newComment["timestamp"] = datetime.datetime.now().isoformat()
        newComment["reporterID"] = personID
        
        if 'reporting' in companyData:
            reportingData = companyData['reporting']
            if reportingPeriod in reportingData:
                if "comments" in reportingData[reportingPeriod]:
                    reportingData[reportingPeriod]["comments"].append(newComment)
                else:                
                    reportingData[reportingPeriod]["comments"] = [newComment]
            else:
                reportingData[reportingPeriod] = {}
                reportingData[reportingPeriod]["comments"] = [newComment]
        else:
            reportingData = {}
            reportingData[reportingPeriod] = {}
            reportingData[reportingPeriod]["comments"] = [newComment]
        
        print(reportingData)
        
        # Update user Record
        updateExpression = "SET updatedOn = :u"
        expressionAttributeValues = {':u': datetime.datetime.now().isoformat()}

        updateExpression+=", reporting= :rp"
        expressionAttributeValues[":rp"]=reportingData

        print(updateExpression)
        print(expressionAttributeValues)

        companyTable.update_item(Key={'id': companyID},
                    UpdateExpression=updateExpression,
                    ExpressionAttributeValues=expressionAttributeValues)

    except Exception as e:
        return exception('Unable to update company data: ' + str(e))


    responseData['success'] = True
    return response(responseData)