import requests
import json
import base64
from PIL import Image
import io

# Test 1: Health check
print("Testing health endpoint...")
try:
    response = requests.get('http://localhost:5000/api/health')
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print("✓ Health check passed\n")
except Exception as e:
    print(f"✗ Health check failed: {e}\n")
    exit(1)

# Test 2: Create a dummy image and send for prediction
print("Testing prediction endpoint...")
try:
    # Create a simple test image (black square)
    img = Image.new('RGB', (640, 480), color='black')
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    img_data = f"data:image/jpeg;base64,{img_base64}"
    
    # Send prediction request
    response = requests.post(
        'http://localhost:5000/api/predict',
        json={'image': img_data},
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("✓ Prediction endpoint working\n")
    else:
        print("✗ Prediction endpoint returned error\n")
        
except Exception as e:
    print(f"✗ Prediction test failed: {e}\n")
    import traceback
    traceback.print_exc()

print("Testing complete!")
