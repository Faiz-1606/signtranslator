# Sign Language Recognition

Simple LSTM-based sign recognition using MediaPipe keypoints.

## Data and features
- Keypoints are extracted with MediaPipe Holistic: 33 pose + 21 left hand + 21 right hand landmarks.
- Each landmark contributes (x, y, z), so per-frame feature size = (33 + 21 + 21) × 3 = 225.
- Training sequences are padded/cropped to 40 frames.

## Training
1. Extract keypoints from videos:
   - Input videos under `data/train/<label>/*.mp4` and `data/test/<label>/*.mp4`.
   - Run `scripts/extract_keypoints.py` to generate `.npy` sequences under `keypoints/`.
2. Train the model:
   - Run `scripts/train_model.py`. The trained checkpoint is saved to `models/sign_model.pth`.

## Live inference
- Live webcam inference uses the same feature layout (225) and sequence length (40) as training.
- Start webcam demo: `python scripts/live_inference.py`
- Press `q` to quit.

## Notes
- Ensure your Python env has `torch`, `opencv-python`, and `mediapipe` installed.
- If you change the feature layout or sequence length, update both training and inference paths consistently.
