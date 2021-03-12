import json
import boto3
import base64
import decimal

# Constants
BUCKET_NAME = 'deiangels-data'

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


s3 = boto3.client('s3')

def lambda_handler(event, context):
    # Instance variables
    responseData = {}
    filePath = None
    fileName = None

    # Extract Query parameters & Validate
    if 'queryStringParameters' not in event:
        return exception('No query parameters in event - check API Gateway configuration')
    try:
        filePath = event['queryStringParameters']['path']
        fileName = event['queryStringParameters']['name']
    except Exception as e:
        return exception(f'Invalid patameters {str(e)}')
    
    method = event['routeKey'][:4]

    if method == 'POST': 
        try:
            bodyData = event['body']
            decodedFile = base64.b64decode(bodyData)
            s3.put_object(Bucket=BUCKET_NAME, Key=filePath+'/'+fileName, Body=decodedFile)
            responseData['fileName'] = f"https://{BUCKET_NAME}.s3.amazonaws.com/{filePath}/{fileName}"
            # Return success message
            responseData['success'] = True
            return response(responseData)
        except Exception as e:
            # Other exception
            return exception(f'File Upload failed: {str(e)}')
          