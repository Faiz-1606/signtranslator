# scripts/train_improved.py
import os, random, math, time
import numpy as np
from glob import glob
from tqdm import tqdm
from collections import Counter

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
import torch.optim as optim

# ---------- CONFIG ----------
KEYPOINT_DIR = "keypoints_small/train"
VAL_KEYPOINT_DIR = "keypoints_small/test"
SEQ_LEN = 40
BATCH_SIZE = 12
EPOCHS = 60
LR = 1e-3
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_OUT = "models/sign_model_improved.pth"
# ----------------------------

# ---------- Dataset ----------
def load_npy_list(base_dir):
    items = []
    classes = sorted([d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir,d))])
    for cls in classes:
        p = os.path.join(base_dir, cls)
        for f in os.listdir(p):
            if f.endswith(".npy"):
                items.append((os.path.join(p,f), cls))
    return items, classes

def resample_sequence(seq, target_len):
    # simple linear resample (time interpolation) to target_len
    if len(seq) == 0:
        return np.zeros((target_len, seq.shape[1]))
    if len(seq) == target_len:
        return seq
    idxs = np.linspace(0, len(seq)-1, num=target_len)
    out = np.array([ np.interp(idxs, np.arange(len(seq)), seq[:,i]) for i in range(seq.shape[1]) ]).T
    return out

def normalize_seq(seq):
    # per-sample mean/std normalization
    mean = seq.mean(axis=0, keepdims=True)
    std = seq.std(axis=0, keepdims=True)
    std[std==0] = 1.0
    return (seq - mean) / std

def augment_seq(seq):
    # simple augmentations: noise, small time warp, frame drop
    # gaussian noise
    if random.random() < 0.5:
        seq = seq + np.random.normal(0, 0.01, seq.shape)
    # temporal jitter: drop/duplicate small windows
    if random.random() < 0.3:
        L = len(seq)
        if L > 4:
            i = random.randint(0, L-4)
            if random.random() < 0.5:
                # drop
                seq = np.delete(seq, slice(i, i+2), axis=0)
            else:
                # duplicate
                seq = np.insert(seq, i, seq[i:i+2], axis=0)
    # horizontal flip: only if safe; comment if not desired
    if random.random() < 0.2:
        seq[:, ::3] = -seq[:, ::3]  # flip x coordinates assuming ordering x,y,z,x,y,z...
    return seq

class KeypointDataset(Dataset):
    def __init__(self, items, classes, seq_len=SEQ_LEN, augment=False):
        self.items = items
        self.classes = classes
        self.class_to_idx = {c:i for i,c in enumerate(classes)}
        self.seq_len = seq_len
        self.augment = augment

    def __len__(self):
        return len(self.items)

    def __getitem__(self, idx):
        path, cls = self.items[idx]
        seq = np.load(path)
        # if seq is (frames, features)
        seq = resample_sequence(seq, self.seq_len)
        seq = normalize_seq(seq)
        if self.augment:
            seq = augment_seq(seq)
            seq = resample_sequence(seq, self.seq_len)
        # return (seq, label)
        seq = torch.tensor(seq, dtype=torch.float32)
        label = torch.tensor(self.class_to_idx[cls], dtype=torch.long)
        return seq, label

# ---------- Model ----------
class BiLSTMAttn(nn.Module):
    def __init__(self, input_size, hidden_size, num_classes, bidirectional=True, dropout=0.3):
        super().__init__()
        self.hidden_size = hidden_size
        self.bidirectional = bidirectional
        self.lstm = nn.LSTM(input_size, hidden_size, batch_first=True, bidirectional=bidirectional)
        self.dropout = nn.Dropout(dropout)
        factor = 2 if bidirectional else 1
        self.attn = nn.Linear(hidden_size*factor, 1)
        self.fc = nn.Linear(hidden_size*factor, num_classes)

    def forward(self, x):
        # x: (B, T, F)
        out, (h_n, c_n) = self.lstm(x)  # out: (B, T, H*fact)
        # attention across time
        weights = torch.softmax(self.attn(out).squeeze(-1), dim=1)  # (B, T)
        context = torch.sum(out * weights.unsqueeze(-1), dim=1)  # (B, H*fact)
        context = self.dropout(context)
        logits = self.fc(context)
        return logits

# ---------- Prepare data ----------
train_items, classes = load_npy_list(KEYPOINT_DIR)
val_items, _ = load_npy_list(VAL_KEYPOINT_DIR)
print("Classes:", len(classes))
print("Train samples:", len(train_items), "Val samples:", len(val_items))

train_dataset = KeypointDataset(train_items, classes, augment=True)
val_dataset = KeypointDataset(val_items, classes, augment=False)

# Weighted sampler to combat imbalance
counts = Counter([cls for _,cls in train_items])
weights_per_class = {c: 1.0/max(1,counts[c]) for c in classes}
sample_weights = [weights_per_class[cls] for _,cls in train_items]
sampler = WeightedRandomSampler(sample_weights, num_samples=len(sample_weights), replacement=True)

train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, sampler=sampler, drop_last=False)
val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)

# model
example = np.load(train_items[0][0])
input_size = example.shape[1]
model = BiLSTMAttn(input_size=input_size, hidden_size=128, num_classes=len(classes)).to(DEVICE)

# loss with class weights
class_counts = np.array([counts[c] for c in classes], dtype=float)
inv_freq = 1.0 / (class_counts + 1e-6)
class_weights = torch.tensor(inv_freq / inv_freq.sum(), dtype=torch.float32).to(DEVICE)
criterion = nn.CrossEntropyLoss(weight=class_weights)
optimizer = optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-4)
scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=4)


# ---------- Train loop ----------
best_val = 1e9
patience = 10
no_improve = 0
for epoch in range(1, EPOCHS+1):
    model.train()
    total_loss = 0.0
    for X,y in tqdm(train_loader, desc=f"Epoch {epoch} train"):
        X,y = X.to(DEVICE), y.to(DEVICE)
        optimizer.zero_grad()
        preds = model(X)
        loss = criterion(preds, y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    avg_train = total_loss/len(train_loader)
    # validation
    model.eval()
    val_loss = 0.0
    correct = 0
    total = 0
    with torch.no_grad():
        for X,y in val_loader:
            X,y = X.to(DEVICE), y.to(DEVICE)
            preds = model(X)
            loss = criterion(preds, y)
            val_loss += loss.item()
            predicted = preds.argmax(dim=1)
            correct += (predicted==y).sum().item()
            total += y.size(0)
    val_loss /= max(1, len(val_loader))
    val_acc = correct/total if total>0 else 0.0
    print(f"Epoch {epoch}: train_loss={avg_train:.4f} val_loss={val_loss:.4f} val_acc={val_acc:.4f}")
    scheduler.step(val_loss)
    # save best
    if val_loss < best_val:
        best_val = val_loss
        torch.save({
            "model_state": model.state_dict(),
            "class_names": classes
        }, MODEL_OUT)
        print("Saved best model.")
        no_improve = 0
    else:
        no_improve += 1
        if no_improve >= patience:
            print("Early stopping.")
            break

print("Training finished. Best val_loss:", best_val)
