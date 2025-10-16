import boto3
import time
import uuid
from flask import Flask, request

app = Flask(__name__)

AWS_REGION = "us-east-1"
ASU_ID = "1"  

AWS_Access_Key=""
AWS_Secret_Access_key=""


S3_InputBucket = ""
S3_OutputBucket = ""
SQS_Reqq = ""
SQS_Respq = ""

# AWS 
s3ct = boto3.client("s3", region_name=AWS_REGION,aws_access_key_id=AWS_Access_Key,aws_secret_access_key=AWS_Secret_Access_key)
sqsct = boto3.client("sqs", region_name=AWS_REGION,aws_access_key_id=AWS_Access_Key,aws_secret_access_key=AWS_Secret_Access_key)

try:
    request_queue_url = sqsct.get_queue_url(QueueName=SQS_Reqq)["QueueUrl"]
    response_queue_url = sqsct.get_queue_url(QueueName=SQS_Respq)["QueueUrl"]
except Exception as e:
    print("Error fetching SQS queue URLs:", e)
    raise

@app.route("/", methods=["POST"])
def upload_file():
    if "inputFile" not in request.files:
        return "Bad Request! Attach a file to the request.", 400
    
    file = request.files["inputFile"]
    if file.filename == "":
        return "File name could not be determined. Please check the request again.", 400

    filename = file.filename
    file_key = filename.split('.')[0]  
    print(f"Received file: {filename}")  

    img_uuid = str(uuid.uuid4())  
    message = f"{filename}:{img_uuid}"  

    try:
        s3ct.upload_fileobj(file, S3_InputBucket, filename)
        print(f"Uploaded {filename} to {S3_InputBucket}")  

        sqsct.send_message(QueueUrl=request_queue_url, MessageBody=message)
        print(f"Message sent to {SQS_Reqq}: {message}")  

    except Exception as e:
        print("Exception occurred:", e)
        return "Error uploading file to S3 or sending SQS message. Check logs for details.", 500

    print(f"Waiting for response for {filename}")  

    response = None
    while not response:
        response = get_response_from_sqs(sqsct, img_uuid)
        time.sleep(1)

    return f"{file_key}:{response}", 200

def get_response_from_sqs(sqs, im_uuid):
    response = sqs.receive_message(
        QueueUrl=response_queue_url,
        AttributeNames=['All'],
        MaxNumberOfMessages=15,
        MessageAttributeNames=['All'],
        VisibilityTimeout=1,
        WaitTimeSeconds=0
    )
    messages = response.get('Messages', [])

    if not messages:
        print("No message in the queue")  
        return None

    for message in messages:
        receipt_handle = message['ReceiptHandle']
        body = message['Body']
        face, img_uuid = body.split(":")

        if img_uuid == im_uuid:
            print(f"Received response from SQS: {face}")  
            sqs.delete_message(QueueUrl=response_queue_url, ReceiptHandle=receipt_handle)
            return face

    print("No matching message in the queue")  
    return None

if __name__ == "__main__":  
    app.run(host="0.0.0.0", port=8000)
