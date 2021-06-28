import boto3
import botocore.exceptions
from boto3.dynamodb.conditions import Attr
import json

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
    dashboardData = {}
    # No Parameters

    try:
        statusFilter = 'active'
        companyQuery = companyTable.scan(
            FilterExpression = Attr('status').eq(statusFilter)
        )
        # Ensure Company records exists
        if 'Items' not in companyQuery:
            return exception('No company records found: ')
        companyRecords = companyQuery['Items']
        
        # Process company records to fill return structure
        for company in companyRecords:
            if "reporting" in company:
                for period, reportingData in company["reporting"].items():
                    if period not in dashboardData:
                        dashboardData[period] = {}
                        dashboardData[period]["total"] = 0
                        dashboardData[period]["confirmed"] = 0
                        dashboardData[period]["missing"] = 0
                    dashboardData[period]["total"] += 1
                    if "confirmed" in reportingData:
                        if reportingData["confirmed"]:
                            dashboardData[period]["confirmed"] += 1
                        else:                        
                            dashboardData[period]["missing"] += 1
                    else:
                        dashboardData[period]["missing"] += 1
        # Build response body
        responseData = {}
        responseData['success'] = True
        responseData['data'] = dashboardData

        # Return data
        return response(responseData)
    except Exception as e:
        return exception('Unable to extract dashboard data: ' + str(e))
