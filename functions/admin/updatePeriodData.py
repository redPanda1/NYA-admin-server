import json
import boto3
import datetime

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
adminTable = dynamodb.Table('Admin')


def lambda_handler(event, context):
    # No parameters, but check body is there
    if not 'body' in event:
        return exception('Invalid Data. No Period data specified in body')

    # Read Admin table - only one record id="0"
    try:
        adminQuery = adminTable.get_item(Key={'id': "0"})
        
        # Ensure Admin record exists (if not we have big problems)
        if 'Item' not in adminQuery:
            return exception('No admin record found.')

        updatedPeriodData = json.loads(event['body'])

        # Update Admin Record with received period data
        updateExpression = "SET updatedOn = :u"
        expressionAttributeValues = {':u': datetime.datetime.now().isoformat()}

        # Period Data
        updateExpression+=", periods= :periods"
        expressionAttributeValues[":periods"]=updatedPeriodData

        returnData = adminTable.update_item(Key={'id': "0"},
                    UpdateExpression=updateExpression,
                    ExpressionAttributeValues=expressionAttributeValues,
                    ReturnValues="UPDATED_NEW")

    except Exception as e:
        return exception('Unable to get period data: ' + str(e))
        
    # All good return period data
    responseData = {}
    responseData['success'] = True
    responseData['data'] = returnData["Attributes"]

    # Return data
    return response(responseData)


