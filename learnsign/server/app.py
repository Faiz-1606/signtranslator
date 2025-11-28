from flask import Flask, request, jsonify
from flask_cors import CORS
import torch
import torch.nn as nn
from PIL import Image
import io
import base64
import json
import numpy as np
import cv2
import mediapipe as mp

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Load class names
with open('../client/src/Assets/class_names.json', 'r') as f:
    class_names = json.load(f)

# Load the model
MODEL_PATH = '../client/src/Assets/sign_model_mobile.pt'
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = None

# MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=True,
    max_num_hands=2,
    min_detection_confidence=0.5
)

# Parameters from training
SEQ_LEN = 40
INPUT_SIZE = 126  # 21 landmarks * 3 coords * 2 hands

# Buffer to store keypoint sequences
keypoint_buffer = []

def normalize_landmarks(seq):
    """Normalize landmarks relative to bounding box for each frame."""
    normalized = np.zeros_like(seq)
    
    for t in range(seq.shape[0]):
        frame = seq[t].reshape(2, 21, 3)  # (2 hands, 21 landmarks, 3 coords)
        
        for hand_idx in range(2):
            hand = frame[hand_idx]  # (21, 3)
            
            if np.sum(np.abs(hand)) > 0:
                xs = hand[:, 0]
                ys = hand[:, 1]
                
                min_x, max_x = xs.min(), xs.max()
                min_y, max_y = ys.min(), ys.max()
                
                range_x = max_x - min_x
                range_y = max_y - min_y
                
                if range_x > 0:
                    hand[:, 0] = (xs - min_x) / range_x
                if range_y > 0:
                    hand[:, 1] = (ys - min_y) / range_y
                
                frame[hand_idx] = hand
        
        normalized[t] = frame.reshape(126)
    
    return normalized

def extract_keypoints(image):
    """Extract hand keypoints from image using MediaPipe."""
    # Convert PIL to CV2
    image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    results = hands.process(cv2.cvtColor(image_cv, cv2.COLOR_BGR2RGB))
    
    # Initialize keypoints array (2 hands, 21 landmarks, 3 coords)
    keypoints = np.zeros((2, 21, 3), dtype=np.float32)
    
    if results.multi_hand_landmarks:
        for idx, hand_landmarks in enumerate(results.multi_hand_landmarks[:2]):  # Max 2 hands
            for i, landmark in enumerate(hand_landmarks.landmark):
                keypoints[idx, i] = [landmark.x, landmark.y, landmark.z]
    
    return keypoints.reshape(126)  # Flatten to (126,)

def load_model():
    global model
    try:
        # Load TorchScript model with weights_only=False
        model = torch.jit.load(MODEL_PATH, map_location=device)
        model.eval()
        print(f"Model loaded successfully on {device}")
        return True
    except Exception as e:
        print(f"Error loading with torch.jit.load: {e}")
        # Try regular torch.load with weights_only=False
        try:
            model = torch.load(MODEL_PATH, map_location=device, weights_only=False)
            model.eval()
            print(f"Model loaded successfully on {device}")
            return True
        except Exception as e2:
            print(f"Error loading model: {e2}")
            return False

# Load model on startup
load_model()

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'model_loaded': model is not None,
        'device': str(device),
        'classes': class_names
    })

@app.route('/api/predict', methods=['POST'])
def predict():
    global keypoint_buffer
    
    if model is None:
        return jsonify({'error': 'Model not loaded'}), 500
    
    try:
        # Get image from request
        data = request.json
        image_data = data.get('image', '')
        
        # Remove data URL prefix if present
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        # Decode base64 image
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        
        # Extract keypoints from current frame
        keypoints = extract_keypoints(image)
        
        # Check if hands detected
        has_hands = np.sum(np.abs(keypoints)) > 0
        
        if not has_hands:
            return jsonify({
                'success': False,
                'message': 'No hands detected',
                'confidence': 0.0
            })
        
        # Add to buffer
        keypoint_buffer.append(keypoints)
        
        # Keep only last SEQ_LEN frames
        if len(keypoint_buffer) > SEQ_LEN:
            keypoint_buffer = keypoint_buffer[-SEQ_LEN:]
        
        # Need at least 20 frames for prediction
        if len(keypoint_buffer) < 20:
            return jsonify({
                'success': False,
                'message': f'Collecting frames... ({len(keypoint_buffer)}/{SEQ_LEN})',
                'confidence': 0.0
            })
        
        # Prepare sequence
        sequence = np.array(keypoint_buffer, dtype=np.float32)
        
        # Pad if needed
        if sequence.shape[0] < SEQ_LEN:
            pad = np.zeros((SEQ_LEN - sequence.shape[0], INPUT_SIZE), dtype=np.float32)
            sequence = np.vstack([sequence, pad])
        else:
            sequence = sequence[-SEQ_LEN:]  # Take last SEQ_LEN frames
        
        # Normalize
        sequence = normalize_landmarks(sequence)
        
        # Convert to tensor
        input_tensor = torch.from_numpy(sequence).unsqueeze(0).to(device)  # (1, SEQ_LEN, 126)
        
        # Make prediction
        with torch.no_grad():
            outputs = model(input_tensor)
            probabilities = torch.nn.functional.softmax(outputs, dim=1)[0]
            
            confidence, predicted_idx = torch.max(probabilities, 0)
            
            predicted_class = class_names[predicted_idx.item()]
            confidence_score = confidence.item()
            
            # Get top 3 predictions
            top_probs, top_indices = torch.topk(probabilities, min(3, len(class_names)))
            top_predictions = [
                {
                    'class': class_names[idx.item()],
                    'confidence': prob.item()
                }
                for prob, idx in zip(top_probs, top_indices)
            ]
            
            print(f"Prediction: {predicted_class} with confidence: {confidence_score:.2f}")
        
        return jsonify({
            'success': True,
            'prediction': predicted_class,
            'confidence': confidence_score,
            'top_predictions': top_predictions,
            'buffer_size': len(keypoint_buffer)
        })
    
    except Exception as e:
        import traceback
        print(f"Prediction error: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/reset', methods=['POST'])
def reset_buffer():
    global keypoint_buffer
    keypoint_buffer = []
    return jsonify({'success': True, 'message': 'Buffer reset'})

@app.route('/api/classes', methods=['GET'])
def get_classes():
    return jsonify({'classes': class_names})

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting HTTP server on http://0.0.0.0:{port}")
    print(f"📱 Access from phone: http://192.168.210.53:{port}")
    app.run(debug=False, host='0.0.0.0', port=port)
