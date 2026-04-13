from unittest.mock import patch

@patch("backend.s3_scanner.boto3.client")
def test_list_buckets(mock_boto):
    mock_s3 = mock_boto.return_value

    mock_s3.list_buckets.return_value = {
        "Buckets": [
            {"Name": "test-bucket", "CreationDate": "2024-01-01"}
        ]
    }

    response = mock_s3.list_buckets()

    assert len(response["Buckets"]) == 1
    assert response["Buckets"][0]["Name"] == "test-bucket"