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

def personName(id):
    responsePerson = personTable.query(
        KeyConditionExpression=Key('id').eq(id)
    )
    if "Items" not in responsePerson:
        return "missing"
    if len(responsePerson['Items']) == 0:
        return "missing"
    personRecord = responsePerson['Items'][0]

    personName = ""
    if "givenName" in personRecord:
        personName = personRecord.get("givenName")
    if "familyName" in personRecord:
         personName += personRecord.get("familyName")
    return personName.strip()

# Get company list information filtered by status, name or reporting status
def lambda_handler(event, context):

    # Get filter from parameters
    try:
        statusFilter = event["queryStringParameters"]['status']
    except Exception as e:
        statusFilter = 'active'

    try:
        if len(statusFilter) > 0:
            scanResponse = companyTable.scan(
                FilterExpression = Attr('status').eq(statusFilter),
                ProjectionExpression = 'id, #s, logo, #n, reportingContactID, nyaContactID, #l, city, #st, #c, reporting',
                ExpressionAttributeNames = {'#s': 'status', '#n': 'name', '#l': 'location', '#st': 'state', '#c': 'country'}
            )
        else:
            scanResponse = companyTable.scan(
                ProjectionExpression = 'id, #s, logo, #n, reportingContactID, nyaContactID, #l, city, #st, #c, reporting',
                ExpressionAttributeNames = {'#s': 'status', '#n': 'name', '#l': 'location', '#st': 'state', '#c': 'country'}
            )

        # Iterate over companies to get email data
        companyList = []
        for company in scanResponse['Items']:
            companyData = {}
            companyData["id"] = company["id"]

            if "status" in company:
                companyData["status"] = company["status"]
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

            # Work out last successful reporting period (if any)
            companyData["lastReport"] = "none" 
            if "reporting" in company:
                lastReport = []
                reportingPeriods = [*company["reporting"]]
                for reportingPeriod in reportingPeriods:
                    if "confirmed" in company["reporting"][reportingPeriod] and company["reporting"][reportingPeriod]:
                        lastReport.append(reportingPeriod)
                if len(lastReport) > 0:
                    lastReport.sort(reverse=True)
                    companyData["lastReport"] = lastReport[0]

            # Collect all data on company
            companyList.append(companyData)

        # Return data
        # Build response body
        responseData = {}
        responseData['success'] = True
        responseData['count'] = len(companyList)
        responseData['data'] = companyList
        return response(responseData)
        
    except Exception as e:
        return exception('Unable to retrieve company records: ' + str(e))