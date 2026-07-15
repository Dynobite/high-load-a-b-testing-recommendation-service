import sys
from datetime import datetime
from fastapi.testclient import TestClient
from app import app, get_exp_group

client = TestClient(app)

def test_get_exp_group():
    print("Testing get_exp_group...")
    # Check deterministic behavior
    assert get_exp_group(100) == get_exp_group(100)
    
    # Check 50/50 split
    controls = 0
    tests = 0
    for i in range(1000):
        if get_exp_group(i) == 'control':
            controls += 1
        else:
            tests += 1
    
    print(f"1000 users split: {{controls}} control, {{tests}} test")
    print(f"1000 users split: {controls} control, {tests} test")
    assert 400 < controls < 600, "Split is skewed"

def test_endpoint():
    print("Testing /post/recommendations/ endpoint with control group...")
    # Find a user mapped to 'control'
    control_user = next(i for i in range(100) if get_exp_group(i) == 'control')
    response = client.get(f"/post/recommendations/?user_id={control_user}&dt=2021-10-01T10:00:00&limit=3")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["exp_group"] == "control"
    assert "recommendations" in data
    print(f"Control Response: {data}")

    print("Testing /post/recommendations/ endpoint with test group...")
    # Find a user mapped to 'test'
    test_user = next(i for i in range(100) if get_exp_group(i) == 'test')
    response = client.get(f"/post/recommendations/?user_id={test_user}&dt=2021-10-01T10:00:00&limit=3")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["exp_group"] == "test"
    assert "recommendations" in data
    print(f"Test Response: {data}")

if __name__ == "__main__":
    test_get_exp_group()
    test_endpoint()
    print("All tests passed!")
