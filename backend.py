import boto3
import json
import os
from face_recognition import face_match

AWS_REGION = "us-east-1"
ASU_ID = ""

AWS_Access_Key=""
AWS_Secret_Access_key=""

S3_InputBucket = ""
S3_OutputBucket = ""
SQS_Reqq = ""
SQS_Respq = ""
Faces_Directory = "./images/"

s3ct = boto3.client("s3", region_name=AWS_REGION,aws_access_key_id=AWS_Access_Key,aws_secret_access_key=AWS_Secret_Access_key)
sqsct = boto3.client("sqs", region_name=AWS_REGION,aws_access_key_id=AWS_Access_Key,aws_secret_access_key=AWS_Secret_Access_key)

try:
    request_queue_url = sqsct.get_queue_url(QueueName=SQS_Reqq)["QueueUrl"]
    response_queue_url = sqsct.get_queue_url(QueueName=SQS_Respq)["QueueUrl"]
except Exception as e:
    print("Error fetching SQS queue URLs:", e)
    raise

def process_image(img_name):
    img_path = os.path.join(Faces_Directory, img_name)
    print("In process_image function")
    if not os.path.exists(Faces_Directory):
        os.makedirs(Faces_Directory)

    try:
        s3ct.download_file(S3_InputBucket, img_name, img_path)
        print(f"Downloaded {img_name} from {S3_InputBucket}")
    except Exception as e:
        print(f"Error downloading {img_name}: {e}")
        return None

    try:
        result = face_match(img_path)[0]
        print(f"Recognition result for {img_name}: {result}")
        return result
    except Exception as e:
        print(f"Error processing {img_name}: {e}")
        return None

def read_message_from_sqs():
    response = sqsct.receive_message(
        QueueUrl=request_queue_url,
        AttributeNames=['All'],
        MaxNumberOfMessages=1,
        MessageAttributeNames=['All'],
        WaitTimeSeconds=5
    )
    messages = response.get('Messages', [])

    if not messages:
        return None

    message = messages[0]
    receipt_handle = message['ReceiptHandle']
    body = message['Body']

    try:
        img_name, img_uuid = body.split(":")
    except ValueError:
        print(f"Invalid message format: {body}")
        return None

    print(f"Processing file: {img_name}, UUID: {img_uuid}")

    face = process_image(img_name)
    if not face:
        print(f"Skipping {img_name} due to processing error.")
        return None

    sqsct.delete_message(QueueUrl=request_queue_url, ReceiptHandle=receipt_handle)
    print(f"Deleted processed request for {img_name} from SQS request queue")

    response_message = f"{face}:{img_uuid}"
    sqsct.send_message(
        QueueUrl=response_queue_url,
        MessageBody=response_message,
        MessageAttributes={
            'Image': {
                'DataType': 'String',
                'StringValue': img_name
            }
        }
    )
    print(f"Sent recognition result to response queue: {response_message}")

    # Store result in S3 Output Bucket
    result_data = json.dumps({"img_name": img_name, "face": face})
    s3ct.put_object(Bucket=S3_OutputBucket, Key=img_name.split('.')[0], Body=result_data, ContentType='application/json')
    print(f"Stored result in {S3_OutputBucket}: {img_name}")

if __name__ == "__main__":
    while True:
        print("Waiting for messages in request queue...")
        read_message_from_sqs()
