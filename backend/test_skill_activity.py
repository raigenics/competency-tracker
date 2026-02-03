"""
Test script for skill update activity endpoint
"""
import requests

BASE_URL = "http://localhost:8000"

def test_skill_update_activity():
    """Test the skill update activity endpoint"""
    print("Testing /dashboard/skill-update-activity endpoint...")
    
    # Test with default parameters
    response = requests.get(f"{BASE_URL}/dashboard/skill-update-activity")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {data}")
        print(f"Total Updates: {data.get('total_updates')}")
        print(f"Active Learners: {data.get('active_learners')}")
        print(f"Low Activity: {data.get('low_activity')}")
        print(f"Stagnant 180+ days: {data.get('stagnant_180_days')}")
    else:
        print(f"Error: {response.text}")
    
    # Test with different days parameter
    print("\n\nTesting with days=30...")
    response = requests.get(f"{BASE_URL}/dashboard/skill-update-activity?days=30")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {data}")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_skill_update_activity()
