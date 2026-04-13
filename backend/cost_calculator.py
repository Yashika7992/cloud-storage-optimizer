import boto3
from datetime import datetime, timedelta

# AWS Clients
s3 = boto3.client('s3')
cloudwatch = boto3.client('cloudwatch')

# Pricing (USD per GB/month)
STANDARD_PRICE = 0.023
IA_PRICE = 0.0125
GLACIER_PRICE = 0.004


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
            return datapoints[-1]['Average'] / (1024 ** 3)  # Convert to GB
        return 0

    except:
        return 0


def calculate_cost(size_gb):
    current_cost = size_gb * STANDARD_PRICE
    ia_cost = size_gb * IA_PRICE
    glacier_cost = size_gb * GLACIER_PRICE

    return current_cost, ia_cost, glacier_cost


def analyze_costs():
    print("\nS3 Cost Analysis\n")

    response = s3.list_buckets()

    for bucket in response['Buckets']:
        bucket_name = bucket['Name']
        print("=" * 50)
        print("Bucket:", bucket_name)

        size_gb = get_bucket_size(bucket_name)
        print("Size (GB):", round(size_gb, 2))

        current, ia, glacier = calculate_cost(size_gb)

        print("Current Cost (Standard): $", round(current, 2))
        print("Standard-IA Cost: $", round(ia, 2))
        print("Glacier Cost: $", round(glacier, 2))

        # Savings
        savings_ia = current - ia
        savings_glacier = current - glacier

        print("Savings (IA): $", round(savings_ia, 2))
        print("Savings (Glacier): $", round(savings_glacier, 2))

        # Recommendation
        recommendation = get_recommendation(size_gb, savings_glacier)
        print("Recommendation:", recommendation)


def get_recommendation(size_gb, savings):
    if size_gb == 0:
        return "No data in bucket"

    elif savings > 1:
        return "Move data to Glacier for maximum savings"

    elif savings > 0.5:
        return "Move to Standard-IA"

    else:
        return "Keep in Standard storage"


if __name__ == "__main__":
    analyze_costs()