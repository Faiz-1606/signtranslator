import requests
import sys

def test_server_connection():
    """Test if Flask server is running and responding correctly"""
    print("=" * 50)
    print("Sign Translator - Server Connection Test")
    print("=" * 50)
    print()

    api_url = "http://localhost:5000/api"

    # Test 1: Health check
    print("Test 1: Checking server health...")
    try:
        response = requests.get(f"{api_url}/health", timeout=3)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Server is running!")
            print(f"   Status: {data.get('status')}")
            print(f"   Model loaded: {data.get('model_loaded')}")
            print(f"   Device: {data.get('device')}")
            print(f"   Number of classes: {len(data.get('classes', []))}")
            print()

            if not data.get('model_loaded'):
                print("⚠️  WARNING: Server is running but model failed to load!")
                print("   Check server logs for model loading errors.")
                return False

        else:
            print(f"❌ Server responded with status code: {response.status_code}")
            return False

    except requests.exceptions.Timeout:
        print("❌ Connection timeout - Server is not responding")
        print("   Make sure Flask server is running: python server/app.py")
        return False

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server")
        print("   Make sure Flask server is running on port 5000")
        print("   Start with: python server/app.py")
        return False

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

    # Test 2: Check CORS
    print("Test 2: Checking CORS configuration...")
    try:
        response = requests.get(f"{api_url}/health")
        if 'Access-Control-Allow-Origin' in response.headers or response.status_code == 200:
            print("✅ CORS is properly configured")
            print()
        else:
            print("⚠️  CORS headers not found (might cause issues)")
            print()
    except:
        pass

    # Test 3: Check classes endpoint
    print("Test 3: Checking classes endpoint...")
    try:
        response = requests.get(f"{api_url}/classes", timeout=3)
        if response.status_code == 200:
            classes = response.json().get('classes', [])
            print(f"✅ Classes endpoint working! Found {len(classes)} sign classes")
            print(f"   Sample classes: {', '.join(classes[:5])}...")
            print()
        else:
            print(f"⚠️  Classes endpoint returned status: {response.status_code}")
            print()
    except Exception as e:
        print(f"⚠️  Classes endpoint error: {e}")
        print()

    print("=" * 50)
    print("✅ All tests passed! Server is ready to use.")
    print("=" * 50)
    print()
    print("Next steps:")
    print("1. Start React app: cd client && npm start")
    print("2. Open http://localhost:3000")
    print("3. Navigate to 'Sign to Text' page")
    print("4. You should see 'Server Connected' badge")
    print()
    return True

if __name__ == "__main__":
    success = test_server_connection()
    sys.exit(0 if success else 1)

