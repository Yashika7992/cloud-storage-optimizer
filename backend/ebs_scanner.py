import boto3
from datetime import datetime, timezone

# AWS Client
ec2 = boto3.client('ec2')

# Pricing
EBS_PRICE_PER_GB = 0.08


def list_volumes():
    print("\nEBS Volume Analysis\n")

    response = ec2.describe_volumes()

    volumes = response['Volumes']

    if not volumes:
        print("No EBS volumes found.")
        return

    for vol in volumes:
        print("=" * 50)

        volume_id = vol['VolumeId']
        size = vol['Size']
        state = vol['State']
        create_time = vol['CreateTime']

        print("Volume ID:", volume_id)
        print("Size (GB):", size)
        print("State:", state)

        # Attachment check
        if vol['Attachments']:
            print("Attached to instance")
            status = "ATTACHED"
        else:
            print("Unattached (Unused)")
            status = "UNATTACHED"

        # Cost calculation
        cost = size * EBS_PRICE_PER_GB
        print("Estimated Monthly Cost: $", round(cost, 2))

        # Age
        age_days = (datetime.now(timezone.utc) - create_time).days
        print("Age (days):", age_days)

        # Recommendation
        recommendation = get_recommendation(status, age_days)
        print("Recommendation:", recommendation)


def list_snapshots():
    print("\nEBS Snapshot Analysis\n")

    response = ec2.describe_snapshots(OwnerIds=['self'])

    snapshots = response['Snapshots']

    if not snapshots:
        print("No snapshots found.")
        return

    for snap in snapshots:
        print("=" * 50)

        snapshot_id = snap['SnapshotId']
        volume_id = snap.get('VolumeId', 'N/A')
        start_time = snap['StartTime']

        print("Snapshot ID:", snapshot_id)
        print("Volume ID:", volume_id)

        # Age
        age_days = (datetime.now(timezone.utc) - start_time).days
        print("Age (days):", age_days)

        # Recommendation
        if age_days > 30:
            print("Recommendation: Delete old snapshot to save cost")
        else:
            print("Recommendation: Keep snapshot")


def get_recommendation(status, age_days):
    if status == "UNATTACHED":
        return "Delete unused volume to save cost"
    elif age_days > 30:
        return "Review old volume for cleanup"
    else:
        return "No action needed"


if __name__ == "__main__":
    list_volumes()
    list_snapshots()