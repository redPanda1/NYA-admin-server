import json
import boto3
from botocore.errorfactory import ClientError
import base64
import decimal
import os

# Constants
BUCKET_NAME = 'nya-portfolio-updates-public'


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

def fileExists(key):
    try:
        s3.head_object(Bucket=BUCKET_NAME, Key=key)
        print("File already exists: " + key)            
        return True
    except ClientError:
        # Not found
        return False

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
    
    # If file exists increment suffix
    while fileExists(filePath+'/'+fileName):
        name, extension = os.path.splitext(fileName)
        nameArray = name.rsplit("_", 1)
        print(nameArray)
        if len(nameArray) > 1:
            versionNumber = nameArray[len(nameArray)-1]
            newVersion = int(versionNumber) + 1
            fileName = nameArray[0] + "_" + str(newVersion) + extension
        else:
            fileName = name + "_1" + extension

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
      