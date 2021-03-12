import boto3
import json
from boto3.dynamodb.conditions import Key

AWS_REGION = "us-east-1"
DOMAIN = "https://www.simon50.com/"

sesClient = boto3.client('ses', region_name=AWS_REGION)
dynamodb = boto3.resource('dynamodb')
companyTable = dynamodb.Table('Companies')
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

def lambda_handler(event, context):
    SENDER_EMAIL = "simon@simon50.com"
    SENDER_NAME = "Graciela"
    RECIPIENT = []
    CCOPY = []
    templateData = {}
    companyID = ""
    emailType = ""
    reportingPeriod = ""
    responseData = {}
    reportingContactEmail = ""
    nyaContactEmail = ""
    
    # Get data from parameters
    try:
        companyID = event["queryStringParameters"]['id']
        emailType = event["queryStringParameters"]['type']
        reportingPeriod = event["queryStringParameters"]['period']
    except Exception as e:
        return exception('Missing parameter: ' + str(e))

    # Get Data from Company and Person Records
    try:
        # Company Data
        companyResponse = companyTable.get_item(Key={'id': companyID})
        if 'Item' not in companyResponse:
            raise ValueError(f'Invalid company ID: {companyID}')
        companyData = companyResponse['Item']
        templateData['companyName'] = companyData['name']
        
        # Company Reporting Contact
        reportingContactID = companyData['reportingContactID']
        personResponse = personTable.get_item(Key={'id': reportingContactID})
        if 'Item' not in personResponse:
            raise ValueError(f'Invalid person ID in reporting contact: {reportingContactID}')
        contactPersonData = personResponse['Item']
        templateData['contactName'] = contactPersonData['givenName']
        reportingContactEmail = contactPersonData['email']

        # NYA Contact
        nyaContactID = companyData['nyaContactID']
        personResponse = personTable.get_item(Key={'id': nyaContactID})
        if 'Item' not in personResponse:
            raise ValueError(f'Invalid person ID in nyaContact: {nyaContactID}')
        nyaPersonData = personResponse['Item']
        templateData['nyaContactName'] = contactPersonData['givenName']
        nyaContactEmail = nyaPersonData['email']
    
    except Exception as e:
        return exception('Unable to retrieve data from database: ' + str(e))

    # Complete Template
    reportingPeriodList = reportingPeriod.split('-')
    templateData['reportingPeriod'] = 'Q' + reportingPeriodList[1] + ', ' + reportingPeriodList[0]
    ctaContact = nyaContactID
    if emailType[:6] == 'request':
        ctaContact = reportingContactID

    templateData['cta1'] = DOMAIN + 'cta1/' + companyID + "?n=" + ctaContact + "&p=" + reportingPeriod
    templateData['cta2'] = DOMAIN + 'cta2/' + companyID + "?n=" + ctaContact + "&p=" + reportingPeriod
    templateData['cta3'] = DOMAIN + 'cta3/' + companyID + "?n=" + ctaContact + "&p=" + reportingPeriod
    templateData['senderName'] = SENDER_NAME

    # Select receiver/cc based upon email type
    if emailType == "preRequest":
        RECIPIENT = [nyaContactEmail]
    elif emailType == "request1":
        RECIPIENT = [reportingContactEmail]
        CCOPY = [nyaContactEmail]
    elif emailType == "request2":
        RECIPIENT = [reportingContactEmail]
        CCOPY = [nyaContactEmail]
    elif emailType == "escalation":
        RECIPIENT = [nyaContactEmail]

    # Complete Tags
    TAGS = []
    TAGS.append({'Name': 'companyID', 'Value': companyID})
    TAGS.append({'Name': 'reportingPeriod', 'Value': reportingPeriod})
    TAGS.append({'Name': 'emailType', 'Value': emailType})

    print(templateData)
    print(RECIPIENT)
    print(CCOPY)
    print(TAGS)
            
    try:
        emailResponse = sesClient.send_templated_email(
            Source=SENDER_EMAIL,
            Destination={
                'ToAddresses': RECIPIENT,
                'CcAddresses': CCOPY
            },
            ReplyToAddresses=[
                SENDER_EMAIL
            ],
            Tags=TAGS,
            ConfigurationSetName="send_stats",
            Template="preRequest",
            TemplateData=json.dumps(templateData)
        )
        print(emailResponse)
    except Exception as e:
        return exception('Send email failed: ' + str(e))

    # Format response
    responseData['success'] = True
    return response(responseData)
