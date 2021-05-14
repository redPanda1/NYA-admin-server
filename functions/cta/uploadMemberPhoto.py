import json
import boto3
import base64
from botocore.errorfactory import ClientError
import os


# Constants
BUCKET_NAME = 'nya-portfolio-updates-public'
FILE_PATH = 'images/avatars'

"https://.s3.amazonaws.com/images/avatars/389a7198-c5a9-413d-adc2-09221b8c478d.jpg"

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
dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    # Instance variables
    responseData = {}
    fileName = None

    # Extract Query parameters & Validate
    if 'queryStringParameters' not in event:
        return exception('No query parameters in event - check API Gateway configuration')
    try:
        fileName = event['queryStringParameters']['fileName']
        personID = event['queryStringParameters']['personID']
    except Exception as e:
        return exception(f'Invalid patameters {str(e)}')
        
    # Check for existing Photo - If file exists increment suffix
    while fileExists(FILE_PATH+'/'+fileName):
        name, extension = os.path.splitext(fileName)
        nameArray = name.rsplit("_", 1)
        if len(nameArray) > 1:
            versionNumber = nameArray[len(nameArray)-1]
            newVersion = int(versionNumber) + 1
            fileName = nameArray[0] + "_" + str(newVersion) + extension
        else:
            fileName = name + "_1" + extension
    
    # Now save (with updated filename if needed)        
    try:
        bodyData = event['body']
        decodedFile = base64.b64decode(bodyData)
        s3.put_object(Bucket=BUCKET_NAME, Key=FILE_PATH+'/'+fileName, Body=decodedFile)
        s3Location = f"https://{BUCKET_NAME}.s3.amazonaws.com/{FILE_PATH}/{fileName}"
    except Exception as e:
        # Other exception
        return exception(f'File Upload failed: {str(e)}')

    # Return success message
    responseData['success'] = True
    responseData['data'] = {}
    responseData['data']['photoURL'] = s3Location
    return response(responseData)          