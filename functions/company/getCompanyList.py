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
companyTable = dynamodb.Table('Companies')
emailTable = dynamodb.Table('emailTracker')
personTable = dynamodb.Table('Person')

def personName(id):
    responsePerson = personTable.query(
        KeyConditionExpression=Key('id').eq(id)
    )
     # Ensure user record exists
    personRecord = responsePerson['Items'][0]
    if personRecord is None:
        return exception('No user record found: ' + id)
    return personRecord["givenName"] + " " + personRecord["familyName"]

def getEmailData(id, period):
    scanResponse = emailTable.scan(
            FilterExpression = Attr('companyID').eq(id) & Attr("reportingPeriod").eq(period),
            ProjectionExpression = 'emailType, eventType, receiver, #t',
            ExpressionAttributeNames = {'#t': 'timestamp'}
        )
    return scanResponse["Items"]

def getComment(emailData):
    if len(emailData) == 0:
        return None
    # Sort to get most recent action
    emailData.sort(key=lambda item : item["timestamp"], reverse=True)
    mostRecent = emailData[0]
    timestamp = dateutil.parser.parse(mostRecent["timestamp"])
    
    # convert to local time
    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz('America/New_York')
    timestamp = timestamp.replace(tzinfo=from_zone)
    localTime = timestamp.astimezone(to_zone)
    comment = "Email " + mostRecent["emailType"] + " " + mostRecent["eventType"] + f" on {timestamp:%a %b %d at %I:%M %p}"
    return comment


# Get company list information filtered by status, name or reporting status
def lambda_handler(event, context):

    # Get period from parameters
    try:
        reportingPeriod = event["queryStringParameters"]['period']
    except Exception as e:
        return exception("missing parameter: period")
    
    # Get filter from parameters
    try:
        statusFilter = event["queryStringParameters"]['status']
    except Exception as e:
        statusFilter = ''

    try:
        reportCompleted = event["queryStringParameters"]["reportCompleted"].lower() in ['true', '1']
    except Exception as e:
        reportCompleted = None

    nameFilter="beast"
    # try:
    #     nameFilter = event["queryStringParameters"]['name'].lower()
    # except Exception as e:
    #     nameFilter = ''

    try:
        if reportCompleted is not None:
            scanResponse = companyTable.scan(
                FilterExpression = Attr('reportCompleted').eq(reportCompleted), 
                ProjectionExpression = 'id, logo, #n, reportingContactID, nyaContactID, #l, city, #st, #c, reporting',
                ExpressionAttributeNames = {'#n': 'name', '#l': 'location', '#st': 'state', '#c': 'country'}
            )
        elif len(statusFilter) > 0:
            scanResponse = companyTable.scan(
                FilterExpression = Attr('compStatus').eq(statusFilter),
                ProjectionExpression = 'id, logo, #n, reportingContactID, nyaContactID, #l, city, #st, #c, reporting',
                ExpressionAttributeNames = {'#n': 'name', '#l': 'location', '#st': 'state', '#c': 'country'}
            )
        elif len(nameFilter) > 0:
            scanResponse = companyTable.scan(
                FilterExpression = Attr('search').contains(nameFilter) ,
                ProjectionExpression = 'id, logo, #n, reportingContactID, nyaContactID, #l, city, #st, #c, reporting',
                ExpressionAttributeNames = {'#n': 'name', '#l': 'location', '#st': 'state', '#c': 'country'}
            )
        else:
            scanResponse = companyTable.scan(
                ProjectionExpression = 'id, logo, #n, reportingContactID, nyaContactID, #l, city, #st, #c, reporting',
                ExpressionAttributeNames = {'#n': 'name', '#l': 'location', '#st': 'state', '#c': 'country'}
            )

        # Iterate over companies to get email data
        companyList = []
        for company in scanResponse['Items']:
            companyData = {}
            companyData["id"] = company["id"]
            companyData["period"] = reportingPeriod 
            
            companyData["_all"] = company

            if "logo" in company:
                companyData["logo"] = company["logo"]
            if "name" in company:
                companyData["name"] = company["name"]
            if "reportingContactID" in company:
                companyData["contactID"] = company["reportingContactID"]
                companyData["contact"] = personName(companyData["contactID"])
            if "nyaContactID" in company:
                companyData["nyaContactID"] = company["nyaContactID"] 
                companyData["nyaContact"] = personName(companyData["nyaContactID"])
            if "location" in company:
                companyData["location"] = company["location"]
            else:
                companyData["location"] = ""
                if "city" in company:
                    companyData["location"] += company["city"]
                if "state" in company:
                    companyData["location"] += ", "
                    companyData["location"] += company["state"]
                if "country" in company:
                    companyData["location"] += ", "
                    companyData["location"] += company["country"]
            companyData["emailData"] = getEmailData(company['id'], reportingPeriod)
            companyData["comment"] = getComment(companyData["emailData"])
            if "reporting" not in company:
                companyData["reportCompleted"] = False 
            elif reportingPeriod not in company["reporting"]:
                companyData["reportCompleted"] = False 
            else:
                reportingData = company["reporting"][reportingPeriod]
                companyData["reportCompleted"] = reportingData["confirmed"]
                companyData["reporterID"] = reportingData["reporterID"] 
                companyData["reporter"] = personName(reportingData["reporterID"])
                companyData["timestamp"] = reportingData["timestamp"]

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