from backend.access_analyzer import classify_bucket, recommend_action

def test_inactive_bucket():
    assert classify_bucket(40, 0.5) == "INACTIVE"

def test_expensive_bucket():
    assert classify_bucket(10, 2) == "EXPENSIVE"

def test_active_bucket():
    assert classify_bucket(5, 0.5) == "ACTIVE"

def test_recommend_inactive():
    assert recommend_action("INACTIVE") == "Move to Glacier or delete unused data"

def test_recommend_expensive():
    assert recommend_action("EXPENSIVE") == "Apply lifecycle policy to reduce cost"

def test_recommend_active():
    assert recommend_action("ACTIVE") == "No action needed"