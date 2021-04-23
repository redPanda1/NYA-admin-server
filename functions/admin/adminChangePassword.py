import boto3
import botocore.exceptions
import json
import random

# Constants
AWS_REGION = "us-east-1"
USER_POOL_ID = 'us-east-1_Mcx33RgTq'
APP_ID = '2ne4im216icdqmmu78pk1abede'
SENDER_EMAIL = "portfolioupdates@newyorkangels.com"

# Globals
cognitoClient = boto3.client('cognito-idp')
sesClient = boto3.client('ses', region_name=AWS_REGION)
dynamodb = boto3.resource('dynamodb')
personTable = dynamodb.Table('Person')

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
    
def getPersonID(attributes):
    for attribute in attributes:
        if attribute.get("Name") == 'custom:personID':
            return attribute.get("Value")
    raise Exception("No personID on user record")


def lambda_handler(event, context):
    responseData = {}

    # Extract Query parameters & Validate
    if 'queryStringParameters' not in event:
        return exception('No query parameters in event - check API Gateway configuration')
    if "userName" not in event["queryStringParameters"]:
        return exception('Invalid Parameters: userName')
    userName = event["queryStringParameters"]['userName']
    
    try:
        # Create a slightly random initial password (user will be forced to change)
        newPassword = 'Welcome' + str(random.randint(10, 99))
        responseAdminSetPassword = cognitoClient.admin_set_user_password(
            UserPoolId=USER_POOL_ID,
            Username=userName,
            Password=newPassword,
            Permanent=False
        )
    except Exception as e:
        print(e)
        return exception('Failed to reset password for user: ' + userName + " - " + str(e))

    try:
        # get person record via user
        getUserResponse = cognitoClient.admin_get_user(
            UserPoolId=USER_POOL_ID,
            Username=userName
        )
        getPersonResponse = personTable.get_item(Key={'id': getPersonID(getUserResponse.get("UserAttributes"))})
        personRecord = getPersonResponse['Item']
    except Exception as e:
        return exception('Unable to retrieve person record: ' + str(e))

    try:
        # Send email confirming reset
        templateData = {}
        emailData = {}
        emailData["Destination"] = {}
        emailData["Source"] = SENDER_EMAIL
        emailData["ReplyToAddresses"] = [SENDER_EMAIL]
        emailData["Template"] = "passwordReset"
        emailData["ConfigurationSetName"] = ""
        emailData["Destination"]["ToAddresses"] = [userName]
        # Set up template data
        templateData['givenName'] = personRecord.get("givenName")
        templateData['newPassword'] = newPassword
        emailData["TemplateData"] = json.dumps(templateData)

        # Send validation email
        sendResponse = sesClient.send_templated_email(**emailData)
        
        if "HTTPStatusCode" in sendResponse["ResponseMetadata"]:
            if sendResponse["ResponseMetadata"]["HTTPStatusCode"] == 200:
                # All Good!
                responseData['success'] = True
                message = "Password reset for user: " + userName
                responseData['data'] = {"message": message}
                return response(responseData)
        return exception("Password reset for user failed: " + userName)
    except Exception as e: 
        print('Failed to get company/person data from database: ' + str(e))
        return exception('Failed to get company/person data from database: ' + str(e))

