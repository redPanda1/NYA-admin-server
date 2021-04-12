import boto3
import botocore.exceptions
import decimal
import json
from boto3.dynamodb.conditions import Attr, Key
from datetime import date
import datetime
import dateutil
from dateutil import tz


def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError
    
def exception(e):
    # Response for errors
    status_code = 400
    return {
        'statusCode': status_code,
        'body': json.dumps({'errorMessage' : str(e)}, default=decimal_default)
    }

def response(data): 
    # Response for success
    return {
        'statusCode': 200,
        'body': json.dumps(data, default=decimal_default)
    }

dynamodb = boto3.resource('dynamodb')
companyTable = dynamodb.Table('Company')
personTable = dynamodb.Table('Person')

personLookUp = {}

def personName(id):
    # check if we have looked this one up before
    if id in personLookUp:
        return personLookUp[id]["name"]
    
    # else go to table
    responsePerson = personTable.query(
        KeyConditionExpression=Key('id').eq(id)
    )
     # Ensure user record exists
    personRecord = responsePerson['Items'][0]
    if personRecord is None:
        return exception('No user record found: ' + id)
        
    fullName = ''
    if "givenName" in personRecord:
        fullName = personRecord["givenName"] + " "
    if "familyName" in personRecord:
        fullName += personRecord["familyName"] 
    personLookUp[id] = {}
    personLookUp[id]["name"] = fullName
    personLookUp[id]["email"] = personRecord["email"]
    
    return fullName

def personEmail(id):
    # check if we have looked this one up before
    if id in personLookUp:
        return personLookUp[id]["email"]
    
    # else go to table
    responsePerson = personTable.query(
        KeyConditionExpression=Key('id').eq(id)
    )
     # Ensure user record exists
    personRecord = responsePerson['Items'][0]
    if personRecord is None:
        return exception('No user record found: ' + id)
        
    fullName = personRecord["givenName"] + " " + personRecord["familyName"]
    personLookUp[id] = {}
    personLookUp[id]["name"] = fullName
    personLookUp[id]["email"] = personRecord["email"]
    
    return personRecord["email"]

def formatEmailHistory(emailData):
    returnedData = []
    for emailRecord in emailData:
        if "receiverID" in emailRecord:
            emailRecord["receiver"] = personEmail(emailRecord["receiverID"])
        if "ccReceiverID" in emailRecord:
            emailRecord["ccReceiver"] = personEmail(emailRecord["ccReceiverID"])
        returnedData.append(emailRecord) 
    returnedData.sort(key=lambda item : item["timestamp"], reverse=True)
    return returnedData

# Get company list information filtered by status, name or reporting status
def lambda_handler(event, context):
    # Check parameters
    if "period" not in event["queryStringParameters"]:
        return exception("missing parameter: period")
        
    # Get period and status from parameters
    reportingPeriod = event["queryStringParameters"]['period']
    reportCompleted = None
        
    if "confirmed" in event["queryStringParameters"]:
        reportCompleted = event["queryStringParameters"]["confirmed"].lower() in ['true', '1']

    print(reportingPeriod)
    print(reportCompleted)
    
    try:
        scanResponse = companyTable.scan(
            FilterExpression = Attr('reporting').exists(),
            ProjectionExpression = 'id, logo, #n, reportingContactID, nyaContactID, #l, city, #st, #c, reporting',
            ExpressionAttributeNames = {'#n': 'name', '#l': 'location', '#st': 'state', '#c': 'country'}
            )
            
        print("Selected Companies: " + str(len(scanResponse['Items'])))

        # Iterate over companies to get email data
        companyList = []
        for company in scanResponse['Items']:
            print("Processing: " + company["name"])
            
            # Check if we have reporting data for this period
            if reportingPeriod not in company["reporting"]:
                print("Company: " + company["name"] + " has no reporting period")
                continue

            # Check status matches parameter (if needed)
            if reportCompleted != None:
                print("Checking report status>>>")
                
                isReportCompleted = False
                if "confirmed" in company["reporting"][reportingPeriod]:
                    if company["reporting"][reportingPeriod]["confirmed"]:
                        isReportCompleted = True
                if reportCompleted != isReportCompleted:
                    print("Company: " + company["name"] + " has no completed report")
                    continue
                    # print("Company: " + company["name"] + " has no completed report - " + str(json.dumps(company["reporting"][reportingPeriod])))

            print("Company: " + company["name"] + " GOOD TO GO>>>> " + str(json.dumps(company["reporting"][reportingPeriod])))


            # Good to send back data            
            companyData = {}
            companyData["id"] = company["id"]
            companyData["period"] = reportingPeriod 
            
            if "name" in company:
                companyData["name"] = company["name"]
            if "logo" in company:
                companyData["logo"] = company["logo"]
            if "reportingContactID" in company:
                companyData["contactID"] = company["reportingContactID"]
                companyData["contact"] = personName(companyData["contactID"])
            if "nyaContactID" in company:
                companyData["nyaContactID"] = company["nyaContactID"] 
                companyData["nyaContact"] = personName(companyData["nyaContactID"])
            reportingData = company["reporting"][reportingPeriod]
            if "confirmed" in reportingData:
                companyData["reportCompleted"] = reportingData["confirmed"]
            else:
                companyData["reportCompleted"] = False
            if "comments" in company["reporting"][reportingPeriod]:
                companyData["comments"] = company["reporting"][reportingPeriod]["comments"]
            if "email" in company["reporting"][reportingPeriod]:
                companyData["email"] = formatEmailHistory(company["reporting"][reportingPeriod]["email"])

            # Get Comment data for company, enhance to include Reporter Name and Sort to get most recent first
            # print(company)
            if "comments" in companyData:
                commentData = []
                for comment in companyData["comments"]:
                    if "reporterID" in comment:
                        comment["reporter"] = personName(comment["reporterID"])
                        commentData.append(comment)
                
                commentData.sort(key=lambda item : item["timestamp"], reverse=True)
                companyData["comments"] = commentData                

            companyList.append(companyData)

        # Return data
        companies = scanResponse['Items']
        # Build response body
        responseData = {}
        responseData['success'] = True
        responseData['count'] = len(companyList)
        responseData['data'] = companyList
        return response(responseData)
        
    except Exception as e:
        return exception('Unable to retrieve company records: ' + str(e))