import boto3
import json
from boto3.dynamodb.conditions import Key

AWS_REGION = "us-east-1"
DOMAIN = "https://www.simon50.com/"
SENDER_EMAIL = "portfolioupdates@newyorkangels.com"
# SENDER_EMAIL = "simon@simon50.com"
SENDER_NAME = "New York Angels"


sesClient = boto3.client('ses', region_name=AWS_REGION)
dynamodb = boto3.resource('dynamodb')
companyTable = dynamodb.Table('Company')
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
                return emailRecord["companyName"] + ": Sent OK"
    return emailRecord["companyName"] + ": Failed"
    
    
def getContactData(companyID):
    returnData = {}
    # Company Data
    companyResponse = companyTable.get_item(Key={'id': companyID})
    if 'Item' not in companyResponse:
        raise ValueError(f'Invalid company ID: {companyID}')
    companyData = companyResponse['Item']
    returnData['companyName'] = companyData['name']
    
    # Company Reporting Contact
    if companyData.get('reportingContactID') != None:
        returnData['reportingContactID'] = companyData.get('reportingContactID')
        personResponse = personTable.get_item(Key={'id': companyData['reportingContactID']})
        if 'Item' not in personResponse:
            raise ValueError("Invalid person ID in reporting contact:" + companyData['reportingContactID'])
        contactPersonData = personResponse['Item']
        returnData['reportingContactName'] = contactPersonData['givenName']
        returnData['reportingContactEmail'] = contactPersonData['email']

    # NYA Contact
    if companyData.get('nyaContactID') != None:
        returnData['nyaContactID'] = companyData['nyaContactID']
        personResponse = personTable.get_item(Key={'id': companyData['nyaContactID']})
        if 'Item' not in personResponse:
            raise ValueError("Invalid person ID in nyaContact: " + companyData['nyaContactID'])
        nyaPersonData = personResponse['Item']
        returnData['nyaContactName'] = nyaPersonData['givenName']
        returnData['nyaContactEmail'] = nyaPersonData['email']
    
    return returnData
    

def lambda_handler(event, context):
    # Get data from parameters
    try:
        emailType = event["queryStringParameters"]['type']
        reportingPeriod = event["queryStringParameters"]['period']
        testMode = event["queryStringParameters"]['test'].lower() in ['true', '1']

    except Exception as e:
        return exception('Missing parameter: ' + str(e))

    if not 'body' in event:
        return exception('Invalid Data. No Company data specified in body')

    try:
        companyList = json.loads(event['body'])
    except Exception as e:
        return exception('Invalid Data. No Company data specified in body')
        
    if len(companyList) == 0:
        return exception('Invalid Data. No Company data specified in body')
        
    emailRecords = []
    for company in companyList:
        templateData = {}
        emailData = {}
        emailData["Destination"] = {}
        emailData["Source"] = SENDER_EMAIL
        emailData["ReplyToAddresses"] = [SENDER_EMAIL]
        emailData["Template"] = emailType
        emailData["ConfigurationSetName"] = "send_stats"

        # Get Data from Company and Person Records
        try:
            contactData = getContactData(company)
            # Select receiver/cc based upon email type
            if emailType == "preRequest":
                emailData["Destination"]["ToAddresses"] = [contactData["nyaContactEmail"]]
            elif emailType == "request1":
                emailData["Destination"]["ToAddresses"] = [contactData["reportingContactEmail"]]
                emailData["Destination"]["CcAddresses"] = [contactData["nyaContactEmail"]]
            elif emailType == "request2":
                emailData["Destination"]["ToAddresses"] = [contactData["reportingContactEmail"]]
                emailData["Destination"]["CcAddresses"] = [contactData["nyaContactEmail"]]
            elif emailType == "request3":
                emailData["Destination"]["ToAddresses"] = [contactData["reportingContactEmail"]]
                emailData["Destination"]["CcAddresses"] = [contactData["nyaContactEmail"]]
            elif emailType == "escalation":
                emailData["Destination"]["ToAddresses"] = [contactData["nyaContactEmail"]]
            elif emailType == "escalation2":
                emailData["Destination"]["ToAddresses"] = [contactData["nyaContactEmail"]]
            elif emailType == "contactRequest":
                emailData["Destination"]["ToAddresses"] = [contactData["nyaContactEmail"]]

            # Set up template data
            templateData['senderName'] = SENDER_NAME
            templateData['companyName'] = contactData["companyName"]
            if emailType != "contactRequest":
                templateData["contactName"] = contactData["reportingContactName"]
            templateData["nyaContactName"] = contactData["nyaContactName"]
            reportingPeriodList = reportingPeriod.split('-')
            templateData['reportingPeriod'] = 'Q' + reportingPeriodList[1] + ', ' + reportingPeriodList[0]
            ctaContact = contactData["nyaContactID"]
            if emailType[:6] == 'request':
                ctaContact = contactData["reportingContactID"]
            templateData['cta1'] = DOMAIN + 'cta1/' + company + "?n=" + ctaContact + "&p=" + reportingPeriod
            templateData['cta2'] = DOMAIN + 'cta2/' + company + "?n=" + ctaContact + "&p=" + reportingPeriod
            templateData['cta3'] = DOMAIN + 'cta3/' + company + "?n=" + ctaContact + "&p=" + reportingPeriod
            templateData['cta4'] = DOMAIN + 'cta4/' + company + "?n=" + ctaContact + "&p=" + reportingPeriod
            emailData["TemplateData"] = json.dumps(templateData)

            # Complete Tags
            tags = []
            tags.append({'Name': 'companyID', 'Value': company})
            tags.append({'Name': 'reportingPeriod', 'Value': reportingPeriod})
            tags.append({'Name': 'emailType', 'Value': emailType})
            emailData["Tags"] = tags
    
            # Add to send array          
            emailRecord = {}
            emailRecord["companyName"] = contactData["companyName"]
            emailRecord["data"] = emailData
            emailRecords.append(emailRecord)
        except Exception as e:
            print('Failed to get company/person data from database: ' + str(e))
            return exception('Failed to get company/person data from database: ' + str(e))

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
                print(emailRecord.get("companyName") + ": Email sent successfully to " + emailData.get("Destination").get("ToAddresses")[0])
            except Exception as e:
                message = emailRecord["companyName"] + ": Failed with error - " + str(e)
                print(message)
                responseMessages.append(message)
                responseData['success'] = False
    
    responseData['data'] = responseMessages

    return response(responseData)