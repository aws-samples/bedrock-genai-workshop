#!/bin/bash

# make sure we have a clean environment to start the build process
rm -rf package *.zip

if [ $# -ne 1 ]
then
   echo "Usage: ./build.sh [s3 location for the lambda function]"
   echo "Example: ./build.sh s3://sagemaker-us-east-1-123456789012/bedrock/agent/action_group1/"
   exit 1
fi
s3_location=$1
pip install --target ./package requests igdb-api-v4
cd package
zip -r ../bedrock_agent_action_group1_lambda_package.zip .
cd ..
echo "Building a lambda function with dependencies in a zip file"
zip bedrock_agent_action_group1_lambda_package.zip lambda_function.py
echo "Upload zip file to S3"
aws s3 cp bedrock_agent_action_group1_lambda_package.zip ${s3_location}
if [ $? -ne 0 ]
then
  echo "S3 upload failed. Please check the path and you have the permission to upload the file to the specified S3 location."
  exit 1
fi
echo "Clean up"
rm -rf package *.zip
echo "Finish successfully"

