import json
import boto3
from datetime import date, datetime

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
    templateList = []
    
    try:
        allTemplates = client.list_templates()
        for template in allTemplates["TemplatesMetadata"]:
            timestamp = template["CreatedTimestamp"]
            templateList.append({"name":template["Name"], "date":timestamp.isoformat() })    
    except Exception as e:
        return exception('Error retrieving template records: ' + str(e))

    # Build response body
    responseData = {}
    responseData['success'] = True
    responseData['data'] = templateList
    # Return data
    return response(responseData)