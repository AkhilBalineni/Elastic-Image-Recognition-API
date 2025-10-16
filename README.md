# Elastic-Image-Recognition-API
Overview:
This project was built as part of CSE 546 Cloud Computing. The goal was to design a scalable image recognition system using AWS cloud services with dynamic auto scaling capabilities. The system processes incoming image URLs from a queue, runs recognition on multiple EC2 worker instances, and stores the results efficiently in S3.

What I Did:

Designed a cloud based image recognition workflow with event driven architecture

Implemented auto scaling to dynamically spin up or terminate EC2 instances based on queue load

Built a queue based communication system to manage image processing tasks

Integrated AWS Rekognition to analyze images and extract labels

Stored processed outputs and metadata in S3 with structured access

Tools and Technologies:

AWS EC2

AWS S3

AWS SQS

AWS Rekognition

Python

NodeJS
