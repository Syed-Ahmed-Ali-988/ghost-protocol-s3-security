# Ghost Protocol - Quick Setup Guide

## 🚀 Quick Start (15 Minutes)

### 1. Enable CloudTrail
```
AWS Console → CloudTrail → Create Trail
- Name: ghost-protocol-trail
- Management events: Write
```

### 2. Create SNS Topic
```
AWS Console → SNS → Create Topic
- Name: MyFirstAlert
- Type: Standard
- Create subscription (Email)
- Confirm email
```

### 3. Create Lambda Function
```
AWS Console → Lambda → Create Function
- Name: GhostProtocol-S3-Monitor
- Runtime: Python 3.12
- Paste code from lambda_function.py
- Update SNS_TOPIC_ARN with your SNS ARN
- Timeout: 30 seconds
```

### 4. Add IAM Permissions
```
Lambda → Configuration → Permissions → Execution Role
Add policies:
- AmazonS3FullAccess
- AmazonSNSFullAccess
```

### 5. Create EventBridge Rule
```
AWS Console → EventBridge → Create Rule
- Name: ghost-protocol-s3-trigger
- Event pattern: Paste from event_pattern.json
- Target: Lambda → GhostProtocol-S3-Monitor
```

### 6. Test
```
S3 → Create Bucket
- Uncheck "Block all public access"
- Wait 10 seconds
- Check email for alert
- Verify bucket is now private
```

## ✅ Done!

Your Ghost Protocol is now protecting your AWS account 24/7!

## 📊 Verify It's Working

1. CloudWatch → Log Groups → `/aws/lambda/GhostProtocol-S3-Monitor`
2. Should see logs showing bucket checks
3. Email should arrive within 10 seconds of creating public bucket

## 🛑 Disable/Remove

To stop Ghost Protocol:
1. EventBridge → Rules → ghost-protocol-s3-trigger → Disable
2. To fully remove: Delete Lambda, EventBridge rule, SNS topic

## 💰 Cost

Estimated: < $1/month for typical usage
- Lambda: First 1M requests free
- SNS: First 1000 emails free
- EventBridge: First 14M events free

## 🆘 Troubleshooting

**Lambda doesn't trigger:**
- Check CloudTrail is enabled
- Check EventBridge rule is "Enabled"

**Email doesn't arrive:**
- Check SNS_TOPIC_ARN in Lambda code
- Check SNS subscription is "Confirmed"
- Check CloudWatch logs for errors

**Permission errors:**
- Verify Lambda has S3 and SNS permissions
- Check IAM role is attached to Lambda
