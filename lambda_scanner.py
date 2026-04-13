import json
import boto3
import uuid
from datetime import datetime

# AWS Clients (Region must match your tables)
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
s3 = boto3.client('s3')

# DynamoDB Tables
storage_table = dynamodb.Table('storage-resources')
scan_table = dynamodb.Table('scan-history')


# 🔍 Function to scan a single S3 bucket
def scan_s3_bucket(bucket_name):
    response = s3.list_objects_v2(Bucket=bucket_name)

    results = []

    if 'Contents' in response:
        for obj in response['Contents']:
            results.append({
                "file_name": obj['Key'],
                "size_bytes": obj['Size'],
                "last_accessed": obj['LastModified'].isoformat()
            })

    return results


# 🧠 Format data for storage-resources table
def format_storage_data(scan_results):
    formatted = []

    for file in scan_results:
        item = {
            "resource_id": str(uuid.uuid4()),  # Primary Key
            "resource_type": "S3_OBJECT",
            "region": "us-east-1",
            "size_bytes": file["size_bytes"],
            "last_accessed": file["last_accessed"],
            "status": "ACTIVE",
            "created_at": datetime.utcnow().isoformat(),
            "owner": file.get("bucket_name", "unknown")  # storing bucket name
        }
        formatted.append(item)

    return formatted


# 💾 Save data to storage-resources table
def save_storage_resources(data):
    for item in data:
        storage_table.put_item(Item=item)


# 📊 Save scan history to scan-history table
def save_scan_history(scan_results, duration_ms, status="SUCCESS", error_message=""):
    scan_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()

    scan_table.put_item(
        Item={
            "scan_id": scan_id,
            "scan_timestamp": timestamp,  # Sort Key
            "triggered_by": "lambda",
            "status": status,
            "resources_found": len(scan_results),
            "resources_flagged": 0,
            "duration_ms": duration_ms,
            "error_message": error_message
        }
    )


# 🚀 MAIN Lambda Handler (Multi-Bucket Support)
def lambda_handler(event, context):
    start_time = datetime.utcnow()

    try:
        # Get list of buckets from event
        bucket_names = event.get("bucket_names", [])

        all_results = []

        # 🔁 Loop through all buckets
        for bucket in bucket_names:
            print(f"Scanning bucket: {bucket}")

            results = scan_s3_bucket(bucket)

            # Add bucket name to each file (important)
            for r in results:
                r["bucket_name"] = bucket

            all_results.extend(results)

        # 🧠 Format data for DynamoDB
        formatted_data = format_storage_data(all_results)

        # 💾 Save to DynamoDB
        save_storage_resources(formatted_data)

        # ⏱️ Calculate execution time
        duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        # 📊 Save scan history
        save_scan_history(all_results, duration)

        return {
            "statusCode": 200,
            "body": json.dumps(f"Scanned {len(bucket_names)} buckets successfully")
        }

    except Exception as e:
        duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        save_scan_history([], duration, status="FAILED", error_message=str(e))

        return {
            "statusCode": 500,
            "body": json.dumps(str(e))
        }


# 🧪 LOCAL TESTING (only for VS Code)
if __name__ == "__main__":
    test_event = {
        "bucket_names": ["bucket-1", "bucket-2", "bucket-3"]
    }

    print(lambda_handler(test_event, None))