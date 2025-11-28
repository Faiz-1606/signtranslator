import os
import torch
import numpy as np
from train_model import SignLSTM


def load_and_prepare_sequence(npy_path, seq_len=40):
    seq = np.load(npy_path, allow_pickle=True)
    # Pad or crop to fixed length
    if len(seq) < seq_len:
        pad = np.zeros((seq_len - len(seq), seq.shape[1]), dtype=np.float32)
        seq = np.vstack((seq, pad))
    else:
        seq = seq[:seq_len, :]
    return seq.reshape(1, seq_len, -1).astype(np.float32)


if __name__ == "__main__":
    checkpoint = torch.load("models/sign_model_normalized.pth", map_location="cpu")
    class_names = checkpoint["class_names"]

    model = SignLSTM(input_size=225, hidden_size=128, num_classes=len(class_names))
    model.load_state_dict(checkpoint["model_state"])
    model.eval()
    print("✅ Model loaded successfully.")

    # Pick any test file under keypoints/test/<label>/*.npy
    test_root = os.path.join("keypoints", "test")
    npy_path = None
    for label in os.listdir(test_root):
        label_dir = os.path.join(test_root, label)
        if not os.path.isdir(label_dir):
            continue
        files = [f for f in os.listdir(label_dir) if f.endswith('.npy')]
        if files:
            npy_path = os.path.join(label_dir, files[0])
            break

    if not npy_path:
        raise FileNotFoundError("No .npy files found under keypoints/test/. Run extract_keypoints.py first.")

    seq_array = load_and_prepare_sequence(npy_path, seq_len=40)
    x = torch.tensor(seq_array, dtype=torch.float32)

    with torch.no_grad():
        output = model(x)
        predicted_class = torch.argmax(output, dim=1).item()

    print(f" File: {npy_path}")
    print(f" Predicted word: {class_names[predicted_class]}")
