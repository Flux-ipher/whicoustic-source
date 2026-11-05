import requests
import sys

# Configuration
API_URL = "http://localhost:8001/api/v1"
MOCK_TOKEN = "mock-token-123"

def test_mock_auth():
    print(f"Testing Mock Auth against {API_URL}...")
    
    headers = {
        "Authorization": f"Bearer {MOCK_TOKEN}"
    }
    
    try:
        # 1. Test /auth/profile (requires auth)
        print("\n1. Requesting User Profile...")
        response = requests.get(f"{API_URL}/auth/profile", headers=headers)
        
        if response.status_code == 200:
            user = response.json()
            print("[SUCCESS] Backend accepted mock token.")
            print(f"   User: {user.get('username')}")
            print(f"   Email: {user.get('email')}")
            print(f"   ID: {user.get('id')}")
        else:
            print(f"[FAILED] Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

        # 2. Test /dashboard/stats (requires auth)
        print("\n2. Requesting Dashboard Stats...")
        response = requests.get(f"{API_URL}/dashboard/stats", headers=headers)
        
        if response.status_code == 200:
            print("[SUCCESS] Accessed dashboard stats.")
        else:
            print(f"[FAILED] Status: {response.status_code}")
            print(f"   Response: {response.text}")
            # Dashboard might fail if DB is empty, but auth should pass
            
    except requests.exceptions.ConnectionError:
        print("[ERROR] Connection refused. Is the server running on port 8001?")
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False
        
    return True

if __name__ == "__main__":
    if test_mock_auth():
        sys.exit(0)
    else:
        sys.exit(1)
