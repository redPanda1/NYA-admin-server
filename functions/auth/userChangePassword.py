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
    validUserParam = 'userName' in queryParams
    validPasswordParam = 'newPassword' in queryParams
    validResetCodeParam = 'session' in queryParams
    
    if not validUserParam or not validPasswordParam or not validResetCodeParam:
        return exception('Invalid Parameters')
    
    try:
        responseAuthChallenge = client.admin_respond_to_auth_challenge(
            UserPoolId=USER_POOL_ID,
            ClientId=APP_ID,
            ChallengeName='NEW_PASSWORD_REQUIRED',
            ChallengeResponses={
                'NEW_PASSWORD': queryParams['newPassword'],
                'USERNAME' : queryParams['userName']
            },
            Session=queryParams['session']
        )

        # All OK Create response 
        responseData['success'] = True
        return response(responseData)
    except client.exceptions.NotAuthorizedException as e:
        print(e)
        print('>>>Get Here: NotAuthorizedException')
        # User not authorized
        responseData['success'] = False
        responseData['errorType'] = "NotAuthorizedException"
        responseData['errorMessage'] = repr(e)
    except Exception as e:
        # Other problem
        responseData['success'] = False
        responseData['errorType'] = "Other"
        responseData['errorMessage'] = repr(e)
        return response(responseData)

