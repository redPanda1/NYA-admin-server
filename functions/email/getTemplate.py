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


client = boto3.client('ses')

def lambda_handler(event, context):
    templateID = None
    templateData = {}
    try:
        templateID = event['queryStringParameters']['id']
    except Exception as e:
        return exception('Missing template name in parameters. Please check API configuration.' + str(e))

    try:
        templateResponse = client.get_template(
            TemplateName=templateID
        )
        templateData = templateResponse["Template"]
    except Exception as e:
        return exception('Error retrieving template records: ' + str(e))

    # Build response body
    responseData = {}
    responseData['success'] = True
    responseData['data'] = templateData
    # Return data
    return response(responseData)