import os
import cv2
import numpy as np
import mediapipe as mp

INPUT_DIR = "keypoints_6"
CLASS_DIRS = ["train", "test"]
SEQ_LEN = 40

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=2,
    model_complexity=1,
    min_detection_confidence=0.4,
    min_tracking_confidence=0.4
)


def extract_frame_keypoints(results):
    points = []
    
    if results.multi_hand_landmarks:
        hands_found = results.multi_hand_landmarks
        # If 2 hands found
        if len(hands_found) == 2:
            for lm in hands_found[0].landmark:
                points.extend([lm.x, lm.y, lm.z])
            for lm in hands_found[1].landmark:
                points.extend([lm.x, lm.y, lm.z])
        else:  
            # Only 1 → Pad other hand with zeros
            for lm in hands_found[0].landmark:
                points.extend([lm.x, lm.y, lm.z])
            points.extend([0]*63)
    else:
        # No hands detected → all zeros
        points.extend([0]*126)

    return np.array(points, dtype=np.float32)


for split in CLASS_DIRS:
    print(f"\n📌 Processing: {split}")
    
    for cls in os.listdir(os.path.join(INPUT_DIR, split)):
        cls_dir = os.path.join(INPUT_DIR, split, cls)
        out_dir = os.path.join("keypoints_np", split, cls)

        os.makedirs(out_dir, exist_ok=True)

        for file in os.listdir(cls_dir):
            if not file.endswith(".mp4"):
                continue

            video_path = os.path.join(cls_dir, file)
            cap = cv2.VideoCapture(video_path)
            seq = []

            while len(seq) < SEQ_LEN:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = hands.process(frame_rgb)

                keypoints = extract_frame_keypoints(results)
                seq.append(keypoints)

            cap.release()
            
            seq = np.array(seq)
            if seq.shape[0] < SEQ_LEN:
                pad = np.zeros((SEQ_LEN - seq.shape[0], 126))
                seq = np.vstack((seq, pad))

            np.save(os.path.join(out_dir, file.replace(".mp4", ".npy")), seq)

    print(f"✅ Done {split}")

hands.close()
print("\n✅ Extraction completed successfully!")
