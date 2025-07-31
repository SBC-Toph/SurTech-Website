import requests

BASE_URL = "http://localhost:8000"

def test_api():
    print("Testing API...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print("API is working!")
        print(response.json())
    except:
        print("API not running or not accessible")

if __name__ == "__main__":
    test_api()