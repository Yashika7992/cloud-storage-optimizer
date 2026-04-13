import boto3
from datetime import datetime, timezone

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('storage-resources')

UNUSED_THRESHOLD_DAYS = 90
DELETE_CANDIDATE_DAYS = 180

def lambda_handler(event, context):
    try:
        response = table.scan()
        items = response.get('Items', [])

        unused_count = 0
        delete_candidate_count = 0
        active_count = 0

        now = datetime.now(timezone.utc)

        for item in items:
            resource_id = item.get('resource_id')
            last_accessed_str = item.get('last_accessed') or item.get('last_modified')

            if not last_accessed_str:
                print(f"Skipping {resource_id} - no date")
                continue

            try:
                last_accessed = datetime.fromisoformat(last_accessed_str)
                if last_accessed.tzinfo is None:
                    last_accessed = last_accessed.replace(tzinfo=timezone.utc)

                days_inactive = (now - last_accessed).days

                if days_inactive >= DELETE_CANDIDATE_DAYS:
                    new_status = 'DELETE_CANDIDATE'
                    delete_candidate_count += 1
                elif days_inactive >= UNUSED_THRESHOLD_DAYS:
                    new_status = 'UNUSED'
                    unused_count += 1
                else:
                    new_status = 'ACTIVE'
                    active_count += 1

                table.update_item(
                    Key={'resource_id': resource_id},
                    UpdateExpression='SET #s = :val, days_inactive = :d',
                    ExpressionAttributeNames={'#s': 'status'},
                    ExpressionAttributeValues={
                        ':val': new_status,
                        ':d': days_inactive
                    }
                )

                print(f"{resource_id} → {new_status}")

            except Exception as e:
                print(f"Error processing {resource_id}: {e}")

        return {
            'statusCode': 200,
            'body': f"UNUSED: {unused_count}, DELETE_CANDIDATE: {delete_candidate_count}, ACTIVE: {active_count}"
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'error': str(e)
        }