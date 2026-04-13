import boto3
from datetime import datetime, timezone, timedelta

# AWS Clients
s3 = boto3.client('s3')
cloudwatch = boto3.client('cloudwatch')


def list_buckets():
    print("\nScanning S3 Buckets...\n")

    response = s3.list_buckets()

    for bucket in response['Buckets']:
        bucket_name = bucket['Name']
        creation_date = bucket['CreationDate']

        print("=" * 50)
        print("Bucket:", bucket_name)

        # Age calculation
        age_days = (datetime.now(timezone.utc) - creation_date).days
        print("Age (days):", age_days)

        # Size
        size_bytes = get_bucket_size(bucket_name)
        size_gb = size_bytes / (1024 ** 3)
        print("Size (GB):", round(size_gb, 2))

        # Last Activity
        last_modified = get_last_modified(bucket_name)

        if last_modified:
            days_inactive = (datetime.now(timezone.utc) - last_modified).days
            print("Last Activity:", last_modified)
        else:
            days_inactive = 999
            print("Last Activity: No objects")

        # Classification
        status = classify_bucket(days_inactive, size_gb)

        print("Status:", status)

        # Recommendation
        suggestion = recommend_action(status)
        print("Recommendation:", suggestion)


def get_bucket_size(bucket_name):
    try:
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/S3',
            MetricName='BucketSizeBytes',
            Dimensions=[
                {'Name': 'BucketName', 'Value': bucket_name},
                {'Name': 'StorageType', 'Value': 'StandardStorage'}
            ],
            StartTime=datetime.utcnow() - timedelta(days=2),
            EndTime=datetime.utcnow(),
            Period=86400,
            Statistics=['Average']
        )

        datapoints = response['Datapoints']

        if datapoints:
            return datapoints[-1]['Average']
        return 0

    except:
        return 0


def get_last_modified(bucket_name):
    try:
        objects = s3.list_objects_v2(Bucket=bucket_name)

        if 'Contents' not in objects:
            return None

        latest = max(obj['LastModified'] for obj in objects['Contents'])
        return latest

    except:
        return None


def classify_bucket(days_inactive, size_gb):
    if days_inactive > 30:
        return "INACTIVE"
    elif size_gb > 1:
        return "EXPENSIVE"
    else:
        return "ACTIVE"


def recommend_action(status):
    if status == "INACTIVE":
        return "Move to Glacier or delete unused data"
    elif status == "EXPENSIVE":
        return "Apply lifecycle policy to reduce cost"
    else:
        return "No action needed"


if __name__ == "__main__":
    list_buckets()