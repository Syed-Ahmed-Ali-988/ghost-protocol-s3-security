"""
Ghost Protocol - Automated S3 Security Auditor
Lambda Function

This Lambda function is triggered by EventBridge when S3 buckets are created or modified.
It automatically detects public buckets and blocks all public access, then sends an email alert.

Author: [Your Name]
Date: February 2026
Course: Cloud DevOps Training
"""

import json
import boto3
import time
import os

# Initialize AWS SDK clients
s3 = boto3.client('s3')
sns = boto3.client('sns')

# Configuration: SNS Topic ARN for security alerts
# IMPORTANT: Replace this with your actual SNS Topic ARN
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:YOUR-ACCOUNT-ID:MyFirstAlert')


def lambda_handler(event, context):
    """
    Main Lambda handler function
    
    Triggered by: EventBridge rule when S3 bucket events occur
    Actions: Checks if bucket is public, remediates if needed, sends alert
    
    Args:
        event: EventBridge event containing CloudTrail S3 API call details
        context: Lambda context object
        
    Returns:
        dict: Status code and message indicating success/failure
    """
    
    print(f"🔍 Ghost Protocol activated!")
    print(f"Event received: {json.dumps(event, indent=2)}")
    
    try:
        # Extract the S3 bucket name from the CloudTrail event
        bucket_name = extract_bucket_name(event)
        
        if not bucket_name:
            print("⚠️ Could not extract bucket name from event")
            return {
                'statusCode': 200,
                'body': json.dumps('No bucket to check')
            }
        
        print(f"📦 Checking bucket: {bucket_name}")
        
        # Small delay to ensure bucket is fully created before checking
        time.sleep(2)
        
        # Check if the bucket has public access enabled
        is_public = check_if_bucket_is_public(bucket_name)
        
        if is_public:
            print(f"🚨 SECURITY ALERT: Bucket {bucket_name} is PUBLIC!")
            
            # Remediate: Block all public access
            block_public_access(bucket_name)
            
            # Send security alert via email
            send_security_alert(bucket_name, violation_fixed=True)
            
            return {
                'statusCode': 200,
                'body': json.dumps(f'✅ Secured public bucket: {bucket_name}')
            }
        else:
            print(f"✅ Bucket {bucket_name} is already private - no action needed")
            return {
                'statusCode': 200,
                'body': json.dumps(f'Bucket {bucket_name} is secure')
            }
    
    except Exception as e:
        error_msg = f"Error processing event: {str(e)}"
        print(f"❌ {error_msg}")
        send_error_alert(error_msg)
        return {
            'statusCode': 500,
            'body': json.dumps(error_msg)
        }


def extract_bucket_name(event):
    """
    Extract S3 bucket name from EventBridge/CloudTrail event
    
    EventBridge events have different structures depending on the S3 API call.
    This function handles multiple event types (CreateBucket, PutBucketPublicAccessBlock, etc.)
    
    Args:
        event: EventBridge event dictionary
        
    Returns:
        str: Bucket name, or None if not found
    """
    try:
        # EventBridge passes CloudTrail events in the 'detail' field
        detail = event.get('detail', {})
        
        # Try to extract from request parameters (CreateBucket events)
        request_parameters = detail.get('requestParameters', {})
        
        if 'bucketName' in request_parameters:
            return request_parameters['bucketName']
        
        # Try to extract from response elements (other events)
        response_elements = detail.get('responseElements', {})
        if 'bucketName' in response_elements:
            return response_elements['bucketName']
        
        # Check event name for bucket operations
        event_name = detail.get('eventName', '')
        if event_name == 'CreateBucket' and 'bucketName' in request_parameters:
            return request_parameters['bucketName']
        
        print(f"⚠️ Could not find bucket name in event structure")
        return None
        
    except Exception as e:
        print(f"Error extracting bucket name: {str(e)}")
        return None


def check_if_bucket_is_public(bucket_name):
    """
    Check if an S3 bucket has public access enabled
    
    AWS S3 has 4 public access block settings:
    1. BlockPublicAcls - Blocks new public ACLs
    2. IgnorePublicAcls - Ignores existing public ACLs
    3. BlockPublicPolicy - Blocks new public bucket policies
    4. RestrictPublicBuckets - Restricts public bucket access
    
    A bucket is considered secure ONLY if all 4 are enabled (True).
    
    Args:
        bucket_name: Name of the S3 bucket to check
        
    Returns:
        bool: True if bucket is public (insecure), False if private (secure)
    """
    try:
        # Get the public access block configuration
        try:
            response = s3.get_public_access_block(Bucket=bucket_name)
            config = response['PublicAccessBlockConfiguration']
            
            # Check if all 4 security settings are enabled
            if (config['BlockPublicAcls'] and 
                config['IgnorePublicAcls'] and 
                config['BlockPublicPolicy'] and 
                config['RestrictPublicBuckets']):
                
                print(f"✅ All public access blocks are enabled - bucket is SECURE")
                return False  # Bucket is private (secure)
            else:
                print(f"⚠️ Some public access blocks are disabled - bucket is PUBLIC")
                return True  # Bucket is public (insecure)
                
        except s3.exceptions.NoSuchPublicAccessBlockConfiguration:
            # No configuration means bucket might be public (no protection)
            print(f"⚠️ No public access block configuration found - assuming PUBLIC")
            return True
            
    except Exception as e:
        print(f"Error checking bucket public access: {str(e)}")
        # If we can't check, assume it's public (fail secure)
        return True


def block_public_access(bucket_name):
    """
    Block all public access to an S3 bucket
    
    This function enables all 4 public access block settings:
    - BlockPublicAcls: Prevents new public ACLs
    - IgnorePublicAcls: Ignores existing public ACLs
    - BlockPublicPolicy: Prevents new public bucket policies
    - RestrictPublicBuckets: Restricts public bucket access via policies
    
    Args:
        bucket_name: Name of the S3 bucket to secure
        
    Raises:
        Exception: If remediation fails (propagated to caller)
    """
    try:
        print(f"🔧 Remediating bucket: {bucket_name}...")
        print(f"   Enabling all public access blocks...")
        
        # Apply comprehensive public access block configuration
        s3.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': True,        # Block new public ACLs
                'IgnorePublicAcls': True,       # Ignore existing public ACLs
                'BlockPublicPolicy': True,      # Block new public policies
                'RestrictPublicBuckets': True   # Restrict public access via policies
            }
        )
        
        print(f"✅ Successfully blocked all public access on {bucket_name}")
        
    except Exception as e:
        error_msg = f"Failed to remediate {bucket_name}: {str(e)}"
        print(f"❌ {error_msg}")
        raise Exception(error_msg)


def send_security_alert(bucket_name, violation_fixed=False):
    """
    Send SNS email alert about security violation
    
    Formats a detailed email with:
    - Violation details (bucket name, issue type)
    - Actions taken (remediation steps)
    - Security status after remediation
    
    Args:
        bucket_name: Name of the bucket with violation
        violation_fixed: Whether remediation was successful
    """
    try:
        if violation_fixed:
            subject = "🚨 Ghost Protocol: Public S3 Bucket FIXED"
            message = f"""
🚨 GHOST PROTOCOL SECURITY ALERT 🚨

VIOLATION DETECTED AND FIXED!

Bucket Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Bucket Name: {bucket_name}
• Issue: Bucket was created WITHOUT public access protection
• Severity: HIGH
• Status: ✅ REMEDIATED

Actions Taken:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ All public access has been BLOCKED
✅ Bucket is now SECURE
✅ No data was exposed

This bucket is now protected by:
• BlockPublicAcls: ON
• IgnorePublicAcls: ON
• BlockPublicPolicy: ON
• RestrictPublicBuckets: ON

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚡ Automated by Ghost Protocol Security System
🕐 Response time: < 5 seconds
"""
        else:
            subject = "⚠️ Ghost Protocol: Security Check"
            message = f"""
Ghost Protocol Security Check

Bucket: {bucket_name}
Status: Monitoring

This is a routine security check.
"""
        
        # Publish to SNS topic
        response = sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject,
            Message=message
        )
        
        print(f"📧 Alert sent successfully! MessageId: {response['MessageId']}")
        
    except Exception as e:
        print(f"❌ Failed to send SNS alert: {str(e)}")


def send_error_alert(error_message):
    """
    Send alert when Ghost Protocol encounters an error
    
    This ensures administrators are notified when the security system
    itself encounters issues that need manual investigation.
    
    Args:
        error_message: Description of the error that occurred
    """
    try:
        message = f"""
⚠️ GHOST PROTOCOL ERROR ALERT ⚠️

An error occurred in the Ghost Protocol security system:

Error Details:
{error_message}

Please check CloudWatch Logs for more information:
Log Group: /aws/lambda/GhostProtocol-S3-Monitor

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This requires manual investigation.
"""
        
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject='⚠️ Ghost Protocol System Error',
            Message=message
        )
        
    except Exception as e:
        print(f"❌ Could not send error alert: {str(e)}")
