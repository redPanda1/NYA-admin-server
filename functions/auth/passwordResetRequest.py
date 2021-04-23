import boto3
import botocore.exceptions
import json

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
    if 'userName' not in queryParams:
        return exception('Invalid Parameters: missing userName' )

    # Check user exists (not "Best Practice" but friendlier)
    try:
        responseCheckUser = client.admin_get_user(
            UserPoolId=USER_POOL_ID,
            Username=queryParams.get('userName')
        )
        if responseCheckUser.get("UserStatus") == "UNKNOWN":
            responseData['success'] = False
            responseData['errorType'] = 'UserNotFoundException'
            responseData['errorMessage'] = "Error: User doesn't exist"
            return response(responseData)
    except client.exceptions.UserNotFoundException as e:
        # User Not Found
        responseData['success'] = False
        responseData['errorType'] = 'UserNotFoundException'
        responseData['errorMessage'] = "Error: User doesn't exist"
        return response(responseData)
        
    except Exception as e:
        # Other exception
        print(e)
        responseData['success'] = False
        responseData['errorType'] = 'other'
        responseData['errorMessage'] = str(e)
        return response(responseData)

    # all good - reset user's password
    try:
        responseForgotPassword = client.forgot_password(
            ClientId=APP_ID,
            Username=queryParams.get('userName')
        )
        print(responseForgotPassword)
        if ('CodeDeliveryDetails' not in responseForgotPassword):
            raise Exception('Bad call to forgot_password: no CodeDeliveryDetails')

        # All OK Create response 
        responseData['success'] = True
        responseData['destination'] = responseForgotPassword.get('CodeDeliveryDetails').get('Destination')
        responseData['method'] = responseForgotPassword.get('CodeDeliveryDetails').get('DeliveryMedium')
        responseData['userName'] = queryParams.get('userName')
        
        return response(responseData)
    except client.exceptions.ResourceNotFoundException as e:        
        # User not found
        responseData['success'] = False
        responseData['errorType'] = 'ResourceNotFoundException'
        responseData['errorMessage'] = str(e)
        return response(responseData)
    except Exception as e:
        # Other exception
        print(e)
        responseData['success'] = False
        responseData['errorType'] = 'other'
        responseData['errorMessage'] = str(e)
        return response(responseData)


