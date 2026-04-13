import boto3
from datetime import datetime, timezone, timedelta

# AWS Clients
s3 = boto3.client('s3')
ec2 = boto3.client('ec2')
cloudwatch = boto3.client('cloudwatch')

# Pricing
S3_STANDARD = 0.023
S3_IA = 0.0125
S3_GLACIER = 0.004
EBS_PRICE = 0.08

report = []


# ---------------- S3 SECTION ---------------- #

def get_s3_size(bucket_name):
    try:
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/S3',
            MetricName='BucketSizeBytes',
            Dimensions=[
                {'Name': 'BucketName', 'Value': bucket_name},
                {'Name': 'StorageType', 'Value': 'StandardStorage'}
            ],
           StartTime=datetime.now(timezone.utc) - timedelta(days=2),
EndTime=datetime.now(timezone.utc),
            Period=86400,
            Statistics=['Average']
        )

        datapoints = response['Datapoints']
        if datapoints:
            return datapoints[-1]['Average'] / (1024 ** 3)
        return 0
    except:
        return 0


def analyze_s3():
    report.append("\n===== S3 ANALYSIS =====\n")

    buckets = s3.list_buckets()['Buckets']

    for bucket in buckets:
        name = bucket['Name']
        report.append(f"\nBucket: {name}")

        size = get_s3_size(name)
        report.append(f"Size (GB): {round(size, 2)}")

        # Cost
        current = size * S3_STANDARD
        glacier = size * S3_GLACIER
        savings = current - glacier

        report.append(f"Current Cost: ${round(current,2)}")
        report.append(f"Glacier Cost: ${round(glacier,2)}")
        report.append(f"Potential Savings: ${round(savings,2)}")

        if savings > 1:
            report.append("Recommendation: Move to Glacier")
        else:
            report.append("Recommendation: Keep as is")


# ---------------- EBS SECTION ---------------- #

def analyze_ebs():
    report.append("\n===== EBS ANALYSIS =====\n")

    volumes = ec2.describe_volumes()['Volumes']

    for vol in volumes:
        vid = vol['VolumeId']
        size = vol['Size']
        report.append(f"\nVolume: {vid}")
        report.append(f"Size: {size} GB")

        if vol['Attachments']:
            status = "Attached"
        else:
            status = "Unattached"

        report.append(f"Status: {status}")

        cost = size * EBS_PRICE
        report.append(f"Monthly Cost: ${round(cost,2)}")

        if status == "Unattached":
            report.append("Recommendation: Delete volume")


def analyze_snapshots():
    report.append("\n===== SNAPSHOT ANALYSIS =====\n")

    snaps = ec2.describe_snapshots(OwnerIds=['self'])['Snapshots']

    for snap in snaps:
        sid = snap['SnapshotId']
        start = snap['StartTime']

        age = (datetime.now(timezone.utc) - start).days

        report.append(f"\nSnapshot: {sid}")
        report.append(f"Age: {age} days")

        if age > 30:
            report.append("Recommendation: Delete old snapshot")
        else:
            report.append("Recommendation: Keep snapshot")


# ---------------- REPORT ---------------- #

def save_report():
    filename = "storage_report.txt"

    with open(filename, "w") as f:
        for line in report:
            f.write(line + "\n")

    print(f"\nReport saved as {filename}")


# ---------------- MAIN ---------------- #

if __name__ == "__main__":
    print("\nRunning Storage Optimizer...\n")

    analyze_s3()
    analyze_ebs()
    analyze_snapshots()

    save_report()

    print("\nOptimization Complete!")