"""
Lambda Function - 1:
Serialize Image Data: this function retrieves the image from s3, encodes it and returns the serialized data
"""
import json
import boto3
import base64

s3 = boto3.client('s3')

def lambda_handler(event, context):
    """A function to serialize target data from S3"""
    
    # Get the s3 address from the Step Function event input
    key = event["s3_key"]
    bucket = event["s3_bucket"]
    
    # Download the data from s3 to /tmp/image.png
    boto3.resource('s3').Bucket(bucket).download_file(key, "/tmp/image.png")
    
    # We read the data from a file
    with open("/tmp/image.png", "rb") as f:
        image_data = base64.b64encode(f.read())

    # Pass the data back to the Step Function
    print("Event:", event.keys())
    return {
        'statusCode': 200,
        'body': {
            "image_data": image_data,
            "s3_bucket": bucket,
            "s3_key": key,
            "inferences": []
        }
    }
"""
Lambda Function - 2:
Image Classifer: this function receives the input from Lambda function 1 and predict the image classification
"""
import os
import io
import boto3
import json
import base64

# setting the  environment variables
ENDPOINT_NAME = 'image-classification-2025-04-15-09-36-07-299'
# We will be using the AWS's lightweight runtime solution to invoke an endpoint.
runtime= boto3.client('runtime.sagemaker')
s3 = boto3.client('s3')
def lambda_handler(event, context):
    
    # Decode the image data
    # Decode image data
    if event['body']["image_data"]:
        image = base64.b64decode(event['body']["image_data"])
    else:
        # Fetch image from S3
        bucket = event['body']["s3_bucket"]
        key = event['body']["s3_key"]
        s3_response = s3.get_object(Bucket=bucket, Key=key)
        image = s3_response['Body'].read()
    # Make a prediction:
    response = runtime.invoke_endpoint(EndpointName=ENDPOINT_NAME,
                                       ContentType='image/png',
                                       Body=image)
    
    # We return the data back to the Step Function    
    event["inferences"] = json.loads(response['Body'].read().decode('utf-8'))
    return {
        'statusCode': 200,
        'body': event
    }
"""
Lambda Function - 3:
Inference Confidence Filter: this function evaluates the classification inferences and retains only those above a defined confidence threshold.  
"""
import json


THRESHOLD = .93


def lambda_handler(event, context):
    
    # Grab the inferences from the event
    inferences = event['body']['inferences']
    
    # Check if any values in our inferences are above THRESHOLD
    meets_threshold = (max(inferences)>THRESHOLD)
    
    # If our threshold is met, pass our data back out of the
    # Step Function, else, end the Step Function with an error
    if meets_threshold:
        pass
    else:
        raise("THRESHOLD_CONFIDENCE_NOT_MET")

    return {
        'statusCode': 200,
        'body': json.dumps(event)
    }
