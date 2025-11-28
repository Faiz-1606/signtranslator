import cv2
import torch
import numpy as np
import mediapipe as mp
import json
import os       

# ---------------- CONFIG ---------------- #
MODEL_PATH = "models/sign_model_mobile.pt"
CLASS_PATH = "models/class_names.json"
SEQ_LEN = 40
CONF_THRESHOLD = 0.50
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

#Load Model #
with open(CLASS_PATH, "r") as f:
    class_names = json.load(f)

model = torch.jit.load(MODEL_PATH, map_location=DEVICE)
model.eval()

print("TorchScript model loaded!")

# Mediapipe hands #
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7,
)
mp_draw = mp.solutions.drawing_utils


def extract_hand_keypoints(results):
    keypoints = []

    if results.multi_hand_landmarks:
        for hand in results.multi_hand_landmarks[:2]:  # Take up to 2 hands
            for lm in hand.landmark:
                keypoints.extend([lm.x, lm.y, lm.z])

        if len(results.multi_hand_landmarks) == 1:
            keypoints.extend([0] * (21 * 3))  # Pad missing hand
    else:
        keypoints.extend([0] * (21 * 3 * 2))  # No hands

    return np.array(keypoints, dtype=np.float32)


# ---------------- Webcam Loop ---------------- #
cap = cv2.VideoCapture(0)
sequence = []
pred_text = ""

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    keypoints = extract_hand_keypoints(results)
    sequence.append(keypoints)
    sequence = sequence[-SEQ_LEN:]

    if len(sequence) == SEQ_LEN:
        seq = torch.tensor([sequence], dtype=torch.float32).to(DEVICE)

        with torch.no_grad():
            preds = model(seq)
            probs = torch.softmax(preds, dim=1)[0]
            max_prob, pred_class = torch.max(probs, dim=0)

        if max_prob > CONF_THRESHOLD:
            pred_text = class_names[pred_class]

    if results.multi_hand_landmarks:
        for hand in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

    cv2.putText(frame, pred_text, (25, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)

    cv2.imshow("Live ASL Recognition - Press Q to Quit", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
hands.close()
cv2.destroyAllWindows()
