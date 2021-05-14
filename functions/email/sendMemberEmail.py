import boto3
import json
from boto3.dynamodb.conditions import Key

AWS_REGION = "us-east-1"
DOMAIN = "https://www.simon50.com/"
SENDER_EMAIL = "simon@newyorkangels.com"


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
    
def sendEmail(emailRecord):
    sendResponse = sesClient.send_templated_email(**emailRecord["data"])
    if "ResponseMetadata" in sendResponse:
        if "HTTPStatusCode" in sendResponse["ResponseMetadata"]:
            if sendResponse["ResponseMetadata"]["HTTPStatusCode"] == 200:
                return emailRecord["personName"] + ": Sent OK"
    return emailRecord["personName"] + ": Failed"
    
    
def getPersonData(personID):
    personResponse = personTable.get_item(Key={'id': personID})
    if 'Item' not in personResponse:
        raise ValueError(f'Invalid person ID: {personID}')
    return personResponse['Item']


def lambda_handler(event, context):
    # Get data from parameters
    try:
        emailType = event["queryStringParameters"]['type']
        testMode = event["queryStringParameters"]['test'].lower() in ['true', '1']
    except Exception as e:
        return exception('Missing parameter: ' + str(e))

    if not 'body' in event:
        return exception('Invalid Data. No Member IDs specified in body')

    try:
        memberList = json.loads(event['body'])
    except Exception as e:
        return exception('Invalid Data. No Member data specified in body')
        
    if len(memberList) == 0:
        return exception('Invalid Data. No Member data specified in body')
        
    emailRecords = []
    for member in memberList:
        templateData = {}
        emailData = {}
        emailData["Destination"] = {}
        emailData["Source"] = SENDER_EMAIL
        emailData["ReplyToAddresses"] = [SENDER_EMAIL]
        emailData["Template"] = emailType
        emailData["ConfigurationSetName"] = "member_mail"

        # Get Data from Person Record
        try:
            personData = getPersonData(member)
            emailData["Destination"]["ToAddresses"] = [personData.get("email")]
            
            # Set up template data
            templateData['nyaMemberName'] = personData.get("givenName")
            templateData['cta5'] = DOMAIN + 'cta5/' + member
            emailData["TemplateData"] = json.dumps(templateData)

            # Complete Tags
            tags = []
            tags.append({'Name': 'personID', 'Value': member})
            tags.append({'Name': 'emailType', 'Value': emailType})
            emailData["Tags"] = tags
    
            # Add to send array          
            emailRecord = {}
            emailRecord["personName"] = f'{personData.get("givenName") or ""} {personData.get("familyName") or ""}'
            emailRecord["data"] = emailData
            emailRecords.append(emailRecord)
        except Exception as e:
            print('Failed to get person data from database: ' + str(e))
            return exception('Failed to get person data from database: ' + str(e))

    # Build response body
    responseData = {}
    responseData['success'] = True
    responseMessages = []

    # If TestMode return data
    if testMode:
        responseData['test'] = True
        responseMessages = emailRecords
    else:
        # Else Send
        for emailRecord in emailRecords:
            try:
                responseMessages.append(sendEmail(emailRecord))
                print(emailRecord.get("personName") + ": Email sent successfully to " + emailData.get("Destination").get("ToAddresses")[0])
            except Exception as e:
                message = emailRecord["personName"] + ": Failed with error - " + str(e)
                print(message)
                responseMessages.append(message)
                responseData['success'] = False
    
    responseData['data'] = responseMessages

    return response(responseData)