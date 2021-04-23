import json
import boto3
import base64

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



s3 = boto3.client("s3")

def lambda_handler(event, context):
    # Get Bucket and Key parameters
    try:
        bucketName = event["queryStringParameters"]['bucket']
        fileName = event["queryStringParameters"]['key']
    except Exception as e:
        return exception('Error in parameters: ' + str(e))

    try: 
        fileObj = s3.get_object(Bucket=bucketName, Key=fileName)
        fileContent = fileObj["Body"].read()
        
        # All good return
        return {
            'statusCode': 200,
            'header': {
                "Content-Type": "application/octet-stream",
                "Content-Disposition": "attachment; filename='report.docx'"
                # "Content-Disposition": "attachment; filename={}".format(fileName)
            },
            'body': base64.b64encode(fileContent).decode('utf-8'),
            "isBase64Encoded": True
        }
    except Exception as e:
        return exception('Unable to download file: ' + str(e))
    
    
    
