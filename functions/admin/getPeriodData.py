import json
import boto3

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
    # No parameters

    # Ready Admin table - only one record id="0"
    try:
        adminQuery = adminTable.get_item(Key={'id': "0"})
        
        # Ensure Admin record exists (if not we have big problems)
        if 'Item' not in adminQuery:
            return exception('No admin record found.')

        adminRecord = adminQuery['Item']

        # Ensure Admin record has period data (if not we have some other problems)
        if 'periods' not in adminRecord:
            return exception('No period data found.')
    
    except Exception as e:
        return exception('Unable to get period data: ' + str(e))
        
    # All good return period data
    responseData = {}
    responseData['success'] = True
    responseData['data'] = adminRecord['periods']

    # Return data
    return response(responseData)
