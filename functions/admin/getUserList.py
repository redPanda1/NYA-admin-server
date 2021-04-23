import json
import boto3
from boto3.dynamodb.conditions import Key
import botocore.exceptions

# Constants
USER_POOL_ID = 'us-east-1_Mcx33RgTq'
APP_ID = '2ne4im216icdqmmu78pk1abede'
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

def getAttribute(attributes, attributeName):
    for attribute in attributes:
        if attribute.get("Name") == attributeName:
            return attribute.get("Value") 
    raise Exception("Error: PersonID attribute missing on user record")
    
def personName(person):
    returnData = ""
    if "givenName" in person:
        returnData = person.get('givenName')
    if "familyName" in person:
        if len(returnData) > 0:
            returnData += " "
        returnData += str(person.get('familyName'))
    return returnData



def lambda_handler(event, context):
    client = boto3.client('cognito-idp')
    usersResponse = client.list_users(
        UserPoolId=USER_POOL_ID,
        AttributesToGet=['custom:personID', 'email']
    )

    # Format return data
    returnData = []
    for user in usersResponse.get("Users"):
        # User Data
        userData = {}
        userData['active'] = user.get('Enabled')
        userData['status'] = user.get('UserStatus')
        userData['email'] = getAttribute(user.get("Attributes"), "email")
        
        # User Type
        try:
            groupsResponse = client.admin_list_groups_for_user(
                Username=user.get('Username'),
                UserPoolId=USER_POOL_ID
            )
            if len(groupsResponse.get("Groups")) > 0:
                userData['type'] = groupsResponse.get("Groups")[0].get("GroupName")
            else:
                userData['type'] = "User"
        except Exception as e:
            return exception("Unable to read Group data: " + str(e))

        # Get person data
        try:
            userData['id'] = getAttribute(user.get("Attributes"), "custom:personID")
            responsePerson = personTable.get_item(Key={'id': userData['id']})
            personRecord = responsePerson['Item']
            if 'photoURL' in personRecord:
                userData['photoURL'] = personRecord['photoURL']
            if len(personName(personRecord)) > 0:
                userData['personName'] = personName(personRecord)
            if "lastLogin" in personRecord:
                userData['lastLogin'] = personRecord["lastLogin"].get("timestamp")
            else:
                userData['lastLogin'] = "unknown"
        except Exception as e:
            return exception("Unable to read Person data: " + str(e))
        
        returnData.append(userData)

    # Build response body
    responseData = {}
    responseData['success'] = True
    responseData['data'] = returnData

    # Return data
    return response(responseData)
        