import boto3
import botocore.exceptions
import json
from boto3.dynamodb.conditions import Key


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

dynamodb = boto3.resource('dynamodb')
personTable = dynamodb.Table('Person')
adminTable = dynamodb.Table('Admin')


# Handler for login returns user data and tokens 
# Can be called with UserId/Password or Refresh token
def lambda_handler(event, context):
    # Instance variables
    client = None
    authParameters = {}
    authType = None 
    responseData = {}
    userData = {}

    # Extract Query parameters & Validate
    if 'queryStringParameters' not in event:
        return exception('No query parameters in event - check API Gateway configuration')
    
    queryParams = event["queryStringParameters"]
    validRefreshParam = 'refreshToken' in queryParams
    validUserParams = 'userName' in queryParams and 'password' in queryParams
    
    if not validUserParams and not validRefreshParam:
        return exception('Invalid Parameters')

    # Populate auth calling parameters based upon type of login
    if validRefreshParam:
        authType = 'REFRESH_TOKEN_AUTH'
        authParameters = authParameters = {'REFRESH_TOKEN': queryParams['refreshToken']}
    else:
        authType = 'USER_PASSWORD_AUTH'
        authParameters = {             
            'USERNAME': queryParams['userName'],
            'PASSWORD': queryParams['password']
        }
    
    # validate user with Cognito
    client = boto3.client('cognito-idp')
    try:
        responseAuth = client.initiate_auth(
            ClientId=APP_ID,
            AuthFlow=authType,
            AuthParameters=authParameters
        )
        print(responseAuth)
        # Validate return
        if 'ChallengeName' in responseAuth:
            if responseAuth['ChallengeName'] == 'NEW_PASSWORD_REQUIRED':
                # We need to respond with a Password reset
                responseData['success'] = False
                responseData['errorType'] = 'NEW_PASSWORD_REQUIRED'
                responseData['errorMessage'] = 'A Password reset is required'
                responseData['data'] = {}
                responseData['data']['session'] = responseAuth['Session']
                responseData['data']['userID'] = responseAuth['ChallengeParameters']['USER_ID_FOR_SRP']
                return response(responseData)
        # Validate authentication
        if 'AuthenticationResult' not in responseAuth:
            return exception('Call to initiate_auth failed - no AuthenticationResult')
        if 'AccessToken' not in responseAuth['AuthenticationResult']:
            return exception('Call to initiate_auth failed - no AccessToken')
        if 'IdToken' not in responseAuth['AuthenticationResult']:
            return exception('Call to initiate_auth failed - no IdToken')
    except client.exceptions.NotAuthorizedException as e:
        # User not authorized
        responseData['success'] = False
        responseData['errorType'] = 'NotAuthorizedException'
        responseData['errorMessage'] = str(e)
        return response(responseData)
    except client.exceptions.UserNotConfirmedException as e:
        # User has not confirmed email
        responseData['success'] = False
        responseData['errorType'] = 'UserNotConfirmedException'
        responseData['errorMessage'] = "Login prohibited as user has not yet confirmed password"
        return response(responseData)
    except Exception as e:
        # Other exception
        responseData['success'] = False
        responseData['errorType'] = 'other'
        responseData['errorMessage'] = str(e)
        return response(responseData)
    
    # Get User Data
    responseUser = client.get_user(
        AccessToken=responseAuth['AuthenticationResult']['AccessToken']
    )
    print(responseUser)
    
    personID = None
    for item in responseUser.get("UserAttributes"):
        if item["Name"] == "custom:personID":
            personID = item["Value"]
            break
    if personID == None:
        return exception('No PersonID on user record')

    # Validate Return
    if 'Username' not in responseUser:
        return exception('Call to get_user failed - no Username')
    if 'UserAttributes' not in responseUser:
        return exception('Call to get_user failed - no UserAttributes')
    
    # Validate user
    for item in responseUser['UserAttributes']:
        if item['Name'] == 'email_verified' and item['Value'] == 'false':
            responseData['success'] = False
            responseData['errorMessage'] = "User's email has not yet validated."
            return response(responseData)
    
    # Format response
    userData['userID'] = responseUser['Username']
    userData['idToken'] = responseAuth['AuthenticationResult']['IdToken']
    if 'RefreshToken' in responseAuth['AuthenticationResult']:
        userData['refreshToken'] = responseAuth['AuthenticationResult']['RefreshToken']

    # include person data and period data
    try:
        responsePerson = personTable.query(
            KeyConditionExpression=Key('id').eq(personID)
        )
        # Ensure user record exists
        try:
            personRecord = responsePerson['Items'][0]
        except:
            # Missing person
            responseData = {}
            responseData['success'] = False
            responseData['errorType'] = 'other'
            responseData['errorMessage'] = "Person Record Missing: " + personID
            return response(responseData)

        print(personRecord)
        if personRecord is None:
            raise Exception("Missing Person record: " + responseUser['Username'])
        if "givenName" in personRecord:
            userData['givenName'] = personRecord["givenName"]
        if "familyName" in personRecord:
            userData['familyName'] = personRecord["familyName"]
        if "photoURL" in personRecord:
            userData['photoURL'] = personRecord["photoURL"]
        if "address" in personRecord:
            userData['address'] = personRecord["address"]
        if "city" in personRecord:
            userData['city'] = personRecord["city"]
        if "zip" in personRecord:
            userData['zip'] = personRecord["zip"]
        if "state" in personRecord:
            userData['state'] = personRecord["state"]
        if "phone" in personRecord:
            userData['phone'] = personRecord["phone"]
        if "email" in personRecord:
            userData['email'] = personRecord["email"]
        print(userData)
        
        # And period Data
        adminQuery = adminTable.get_item(Key={'id': "0"})
        # Ensure Admin record exists (if not we have big problems)
        if 'Item' not in adminQuery:
            return exception('No admin record found.')
        periodData = adminQuery['Item']['periods']
        
        for period in periodData:
            if periodData[period]['isCurrent']:
                userData['currentPeriod'] = period 
                userData['periodOpen'] = periodData[period]['isOpen'] 

    except Exception as e:
        # Other exception
        responseData = {}
        responseData['success'] = False
        responseData['errorType'] = 'other'
        responseData['errorMessage'] = str(e)
        return response(responseData)

    # All good - return data
    responseData['success'] = True
    responseData['data'] = userData

    return response(responseData)