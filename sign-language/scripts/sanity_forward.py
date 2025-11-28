import torch
import numpy as np
from train_model import SignLSTM

# Load checkpoint
ckpt = torch.load("models/sign_model.pth", map_location="cpu")
model = SignLSTM(input_size=225, hidden_size=128, num_classes=len(ckpt["class_names"]))
model.load_state_dict(ckpt["model_state"])
model.eval()

# Dummy input: batch=1, seq_len=40, features=225
x = torch.zeros((1, 40, 225), dtype=torch.float32)

with torch.no_grad():
    out = model(x)
    print("Output shape:", tuple(out.shape))
