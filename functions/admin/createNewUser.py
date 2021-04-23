import boto3
import botocore.exceptions
import json
import re
import datetime
import uuid
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
    
def valid_email(email):
    return bool(re.search(r"^[\w\.\+\-]+\@[\w]+\.[a-z]{2,3}$", email))


client = boto3.client('cognito-idp')
dynamodb = boto3.resource('dynamodb')
personTable = dynamodb.Table('Person')

def lambda_handler(event, context):
    responseData = {}
    userName = ""
    personRecord = None

    # Extract Query parameters & Validate
    if 'queryStringParameters' not in event:
        return exception('No query parameters in event - check API Gateway configuration')
    queryParams = event["queryStringParameters"]
    print(queryParams)
    if 'name' in queryParams and 'email' in queryParams:
        if 'personID' in queryParams:
            return exception('Parameter error: specify either personID or userName and userEmail')
        if not valid_email(queryParams.get("email")):
            return exception('Error: Invalid email - ' + queryParams.get("email"))
        userName = queryParams.get("email")
    else:
        if 'personID' not in queryParams:
            return exception('Parameter error: specify either personID or userName and userEmail')
        else:
            personResponse = personTable.get_item(Key={'id': queryParams.get("personID")})
            try:
                personRecord = personResponse['Item']
                userName = personRecord.get("email")
            except:
                return exception('No person record found: ' + queryParams.get("personID"))

    # Check no user already exists
    try:
        userResponse = client.admin_get_user(
            UserPoolId=USER_POOL_ID,
            Username=userName
        )
        # User Already Exists
        responseData['success'] = False
        responseData['errorMessage'] = 'Error: User already exists'
        return response(responseData)
    except client.exceptions.UserNotFoundException as e:
        # This is what we wanted!
        pass

    # Create Person record if none exists
    if personRecord is None:
        try:
            # Create New Person Record
            personRecord = {}
            personRecord["id"] = str(uuid.uuid4())
            personRecord["status"] = "created"
            personRecord["email"] = userName
            nameArray = queryParams['name'].split()
            if len(nameArray) < 2:
                return exception('Invalid User Name')
            personRecord["givenName"] = nameArray[0]
            personRecord["familyName"] = nameArray[len(nameArray) - 1]
            if len(nameArray) > 2:
                givenNames = ''
                for i in range(0, len(nameArray)-1):
                    givenNames += nameArray[i]
                    givenNames += ' '
                personRecord["givenName"]=givenNames.strip()
            personRecord["createdOn"] = datetime.datetime.now().isoformat()
            personRecord["updatedOn"] = datetime.datetime.now().isoformat()
    
            createPersonResponse = personTable.put_item(Item=personRecord)
            print("New Person created: " + personRecord["id"])
        except Exception as e:
            print('Unable to create Person record: ' + str(e))
            return exception('Unable to create Person record: ' + str(e))

    # Create User Record
    try:
        print("creating new user")
        # Create a slightly random initial password (user will be forced to change)
        newPassword = 'Welcome' + str(random.randint(10, 99))
        responseNewUser = client.admin_create_user(
            UserPoolId=USER_POOL_ID,
            Username=personRecord.get("email"),
            UserAttributes=[
          {
                'Name': 'custom:personID',
                'Value': personRecord.get("id")
            }
            ],
            TemporaryPassword=newPassword,
            DesiredDeliveryMediums=[
                'EMAIL'
            ]
        )
        print("New user created OK")
        # All OK Create response 
        responseData['success'] = True
        return response(responseData)
    except client.exceptions.UsernameExistsException as e:      
        # User Already Exists
        print("User already exists: " + personRecord.get("email"))
        responseData['success'] = False
        responseData['errorType'] = 'UsernameExistsException'
        responseData['errorMessage'] = str(e)
        return response(responseData)
    except Exception as e:
        # Other exception
        print("User not created: " + str(e))
        return exception(e)

