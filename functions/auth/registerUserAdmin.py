import boto3
import botocore.exceptions
import json
import re
import random


# Constants
USER_POOL_ID = 'us-east-1_Mcx33RgTq'
APP_ID = '2ne4im216icdqmmu78pk1abede'

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


def lambda_handler(event, context):
    client = boto3.client('cognito-idp')
    responseData = {}

    # Extract Query parameters & Validate
    if 'queryStringParameters' not in event:
        return exception('No query parameters in event - check API Gateway configuration')
    
    queryParams = event["queryStringParameters"]
    validUserParams = 'name' in queryParams and 'email' in queryParams and 'userType' in queryParams
    
    if not validUserParams:
        return exception('Invalid Parameters')
        
    nameArray = queryParams['name'].split()
    if len(nameArray) < 2:
        return exception('Invalid User Name')

    email = queryParams['email']
    if not valid_email(email):
        return exception('Invalid email')

    # Create a slightly random initial password (user will be forced to change)
    newPassword = 'Welcome' + str(random.randint(10, 99))

    try:
        responseNewUser = client.admin_create_user(
            UserPoolId=USER_POOL_ID,
            Username=queryParams['email'],
            UserAttributes=[
            {
                'Name': 'email',
                'Value': email
            },
           {
                'Name': 'given_name',
                'Value': nameArray[0]
            },
           {
                'Name': 'name',
                'Value': queryParams['name']
            },
           {
                'Name': 'family_name',
                'Value': nameArray[1]
            }
            ],
            TemporaryPassword=newPassword,
            DesiredDeliveryMediums=[
                'EMAIL'
            ]
        )
        print(responseNewUser)
        # All OK Create response 
        responseData['success'] = True
        return response(responseData)
    except client.exceptions.UsernameExistsException as e:      
        # User Already Exists
        responseData['success'] = False
        responseData['errorType'] = 'UsernameExistsException'
        responseData['errorMessage'] = str(e)
        return response(responseData)
    except Exception as e:
        # Other exception
        return exception(e)

def valid_email(email):
    return bool(re.search(r"^[\w\.\+\-]+\@[\w]+\.[a-z]{2,3}$", email))