import boto3
from datetime import datetime, timezone, timedelta

# Initialize AWS clients
s3 = boto3.client('s3')
cloudwatch = boto3.client('cloudwatch')


def list_buckets():
    print("\n Scanning S3 Buckets...\n")

    try:
        response = s3.list_buckets()
        buckets = response['Buckets']

        if not buckets:
            print("No S3 buckets found.")
            return

        for bucket in buckets:
            bucket_name = bucket['Name']
            creation_date = bucket['CreationDate']

            print(f"\n Bucket: {bucket_name}")

            # Calculate age
            age_days = (datetime.now(timezone.utc) - creation_date).days
            print(f" Created On: {creation_date}")
            print(f"Age: {age_days} days")

            # Get bucket size from CloudWatch
            size_bytes = get_bucket_size(bucket_name)
            size_gb = size_bytes / (1024 ** 3)

            print(f" Size: {size_gb:.2f} GB")

    except Exception as e:
        print(f" Error: {str(e)}")


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
        else:
            return 0

    except Exception as e:
        print(f" Could not fetch size for {bucket_name}: {str(e)}")
        return 0


if __name__ == "__main__":
    list_buckets()