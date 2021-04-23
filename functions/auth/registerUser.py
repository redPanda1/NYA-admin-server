import boto3
import botocore.exceptions
import json
import re
import datetime


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


# Process response to register user from sign-up screen
def lambda_handler(event, context):
    client = boto3.client('cognito-idp')
    dynamodb = boto3.resource('dynamodb')
    responseData = {}

    # Extract Query parameters & Validate
    if 'queryStringParameters' not in event:
        return exception('No query parameters in event - check API Gateway configuration')
    
    queryParams = event["queryStringParameters"]
    validUserParams = 'name' in queryParams and 'email' in queryParams and 'userType' in queryParams and 'password' in queryParams
    
    if not validUserParams:
        return exception('Invalid Parameters')
        
    nameArray = queryParams['name'].split()
    if len(nameArray) < 2:
        return exception('Invalid User Name')

    email = queryParams['email']
    if not valid_email(email):
        return exception('Invalid email')

    try:
        responseSignUp = client.sign_up(
            ClientId=APP_ID,
            Username=email,
            Password=queryParams['password'],
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
            ]
        )

        print(responseSignUp)
        userID = responseSignUp['UserSub']
        
        # Create User record
        userTable = dynamodb.Table('Users')
        putResponse = userTable.put_item(
            Item={
                'id' : userID,
                'givenName': nameArray[0], 
                'familyName': nameArray[1], 
                'type': queryParams['userType'], 
                'email': email, 
                'status': 'created',
                'createdOn': datetime.datetime.now().isoformat(), 
                'updatedOn': datetime.datetime.now().isoformat()
            })
        
        # All OK Create response 
        responseData['success'] = True
        responseData['destination'] = responseSignUp['CodeDeliveryDetails']['Destination']
        responseData['method'] = responseSignUp['CodeDeliveryDetails']['DeliveryMedium']
        responseData['userName'] = userID
        return response(responseData)
    except client.exceptions.UsernameExistsException as e:      
        # User Already Exists
        responseData['success'] = False
        responseData['errorType'] = 'UsernameExistsException'
        responseData['errorMessage'] = repr(e)
        return response(responseData)
    except Exception as e:
        # Other exception
        responseData['success'] = False
        responseData['errorType'] = 'Other'
        responseData['errorMessage'] = repr(e)
        return response(responseData)

def valid_email(email):
    return bool(re.search(r"^[\w\.\+\-]+\@[\w]+\.[a-z]{2,3}$", email))