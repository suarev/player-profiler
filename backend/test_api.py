"""Test script to verify API is working"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_api():
    print("Testing LENS API...")
    
    # Test root endpoint
    print("\n1. Testing root endpoint...")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test health check
    print("\n2. Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test forward metrics
    print("\n3. Testing forward metrics...")
    response = requests.get(f"{BASE_URL}/api/forwards/metrics")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        metrics = response.json()
        print(f"Found {len(metrics)} metrics:")
        for m in metrics:
            print(f"  - {m['name']}: {m['description']}")
    
    # Test algorithms
    print("\n4. Testing algorithms...")
    response = requests.get(f"{BASE_URL}/api/algorithms/list")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        algorithms = response.json()
        print(f"Found {len(algorithms)} algorithms:")
        for a in algorithms:
            print(f"  - {a['name']}: {a['description']}")
    
    # Test recommendations
    print("\n5. Testing recommendations...")
    request_data = {
        "weights": [
            {"metric": "finishing", "weight": 80},
            {"metric": "physical", "weight": 60},
            {"metric": "creativity", "weight": 40},
            {"metric": "pace_dribbling", "weight": 50},
            {"metric": "work_rate", "weight": 30},
            {"metric": "positioning", "weight": 85},
            {"metric": "linkup", "weight": 45}
        ],
        "algorithm": "weighted_score",
        "limit": 3
    }
    
    response = requests.post(
        f"{BASE_URL}/api/forwards/recommend",
        json=request_data
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Algorithm used: {result['algorithm_used']}")
        print("Top recommendations:")
        for i, rec in enumerate(result['recommendations'], 1):
            print(f"\n  {i}. {rec['name']} ({rec['team']})")
            print(f"     Match Score: {rec['match_score']:.1f}")
            print(f"     Key Stats: {rec['key_stats']}")

if __name__ == "__main__":
    test_api()