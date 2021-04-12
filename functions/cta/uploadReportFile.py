import json
import boto3
import base64
import decimal
import datetime

# Constants
BUCKET_NAME = 'deiangels-data'

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


s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
companyTable = dynamodb.Table('Company')


def lambda_handler(event, context):
    # Instance variables
    responseData = {}
    filePath = None
    fileName = None

    # Extract Query parameters & Validate
    if 'queryStringParameters' not in event:
        return exception('No query parameters in event - check API Gateway configuration')
    try:
        filePath = event['queryStringParameters']['path']
        fileName = event['queryStringParameters']['fileName']
        companyID = event['queryStringParameters']['companyID']
        personID = event['queryStringParameters']['personID']
        reportingPeriod = event['queryStringParameters']['period']
    except Exception as e:
        return exception(f'Invalid patameters {str(e)}')
    
    method = event['routeKey'][:4]

    if method == 'POST': 
        try:
            bodyData = event['body']
            decodedFile = base64.b64decode(bodyData)
            s3.put_object(Bucket=BUCKET_NAME, Key=filePath+'/'+fileName, Body=decodedFile)
            s3Location = f"https://{BUCKET_NAME}.s3.amazonaws.com/{filePath}/{fileName}"
        except Exception as e:
            # Other exception
            return exception(f'File Upload failed: {str(e)}')

        # Update Company Record
        try:
            # First get company record and check reporting data
            companyResponse = companyTable.get_item(Key={'id': companyID})
            if 'Item' not in companyResponse:
                raise ValueError(f'Invalid company ID: {companyID}')
            
            companyData = companyResponse['Item']
            reportingData = {}
            # print("Get here 1")
            # if 'reporting' not in companyData:
            #     print("Get here 2")
            #     reportingData[reportingPeriod] = {}
            #     reportingData[reportingPeriod]["reports"] = []
            # elif reportingPeriod not in companyData['reporting']:
            #     print("Get here 3")
            #     reportingData = companyData['reporting']
            #     reportingData[reportingPeriod] = {}
            #     reportingData[reportingPeriod]["reports"] = []
            #     reportingData[reportingPeriod]["confirmed"] = True
            #     reportingData[reportingPeriod]["timestamp"] = datetime.datetime.now().isoformat()
            # elif 'reports' not in companyData['reporting'][reportingPeriod]:
            #     print("Get here 4")
            #     reportingData = companyData['reporting']
            #     reportingData[reportingPeriod]["reports"] = []

            print("Get here 1")
            if 'reporting' in companyData:
                print("Get here 2")
                reportingData = companyData['reporting']

            if reportingPeriod not in reportingData:
                print("Get here 3")
                reportingData[reportingPeriod] = {}
                reportingData[reportingPeriod]["confirmed"] = True
                reportingData[reportingPeriod]["reporterID"] = personID
                reportingData[reportingPeriod]["timestamp"] = datetime.datetime.now().isoformat()
            
            if "confirmed" not in reportingData[reportingPeriod]:
                print("Get here 3a")
                reportingData[reportingPeriod]["confirmed"] = True
                reportingData[reportingPeriod]["reporterID"] = personID
                reportingData[reportingPeriod]["timestamp"] = datetime.datetime.now().isoformat()
                
            if "reports" not in reportingData[reportingPeriod]:
                print("Get here 4")
                reportingData[reportingPeriod]["reports"] = []
                
            print("Get here 5")

            # Format record to include this report
            thisReport = {}
            thisReport["file"] = s3Location
            thisReport["timestamp"] = datetime.datetime.now().isoformat()
            thisReport["reporterID"] = personID
            reportingData[reportingPeriod]["reports"].append(thisReport)

            print("Get here 6")

        
            # Now Update company Record with new reporting data
            updateExpression = "SET updatedOn = :u"
            expressionAttributeValues = {':u': datetime.datetime.now().isoformat()}
    
            updateExpression+=", reporting= :rp"
            expressionAttributeValues[":rp"]=reportingData
    
            print(updateExpression)
            print(expressionAttributeValues)
    
            companyTable.update_item(Key={'id': companyID},
                        UpdateExpression=updateExpression,
                        ExpressionAttributeValues=expressionAttributeValues)
    
        except Exception as e:
            return exception('Unable to update company data: ' + str(e))


        # Return success message
        responseData['success'] = True
        return response(responseData)          