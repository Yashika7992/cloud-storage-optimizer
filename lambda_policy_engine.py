import boto3
from datetime import datetime, timezone

dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

table = dynamodb.Table('storage-resources')

def lambda_handler(event, context):
    try:
        response = table.scan()
        items = response.get('Items', [])

        applied_count = 0

        for item in items:
            resource_id = item.get('resource_id')
            status = item.get('status')

            # ✅ FIX: Use resource_id if bucket_name not present
            bucket_name = item.get('bucket_name') or resource_id

            print(f"Checking bucket: {bucket_name}, status: {status}")

            # ✅ Skip if still no bucket name
            if not bucket_name:
                print(f"Skipping {resource_id} - no bucket_name")
                continue

            # ✅ Handle ARN format
            if bucket_name.startswith("arn:aws:s3:::"):
                bucket_name = bucket_name.split(":::")[-1]

            # ✅ Apply only for correct statuses
            if status not in ["UNUSED", "DELETE_CANDIDATE"]:
                print(f"Skipping {bucket_name} - status is {status}")
                continue

            # ✅ Lifecycle rule
            lifecycle_config = {
                'Rules': [
                    {
                        'ID': 'AutoCleanupRule',
                        'Status': 'Enabled',
                        'Filter': {'Prefix': ''},
                        'Expiration': {
                            'Days': 30 if status == "UNUSED" else 7
                        }
                    }
                ]
            }

            try:
                # ✅ Apply lifecycle policy
                s3.put_bucket_lifecycle_configuration(
                    Bucket=bucket_name,
                    LifecycleConfiguration=lifecycle_config
                )

                print(f"Policy applied to {bucket_name}")

                # ✅ Update DynamoDB
                table.update_item(
                    Key={'resource_id': resource_id},
                    UpdateExpression="""
                        SET policy_applied = :p,
                            policy_applied_at = :t
                    """,
                    ExpressionAttributeValues={
                        ':p': True,
                        ':t': datetime.now(timezone.utc).isoformat()
                    }
                )

                applied_count += 1

            except Exception as e:
                print(f"Error applying policy to {bucket_name}: {str(e)}")

        return {
            "statusCode": 200,
            "body": f"Policies applied to {applied_count} buckets"
        }

    except Exception as e:
        print(str(e))
        return {
            "statusCode": 500,
            "error": str(e)
        }