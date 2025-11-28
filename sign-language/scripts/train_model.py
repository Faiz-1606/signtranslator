import os
import glob
import json
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm

# CONFIG
KEYPOINT_DIR = "./keypoints_np"
SEQ_LEN = 40
BATCH_SIZE = 8
EPOCHS = 50
LR = 1e-3
HIDDEN = 128
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
SAVE_PTH = "models/sign_model_normalized.pth"
SAVE_TORCHSCRIPT = "models/sign_model_mobile.pt"
CLASS_NAMES_JSON = "models/class_names.json"

os.makedirs("models", exist_ok=True)

def normalize_landmarks(seq):
    """
    Normalize landmarks relative to bounding box for each frame.
    Input: (SEQ_LEN, 126) where 126 = 21*3*2 (x,y,z for 2 hands)
    Output: (SEQ_LEN, 126) normalized
    """
    normalized = np.zeros_like(seq)
    
    for t in range(seq.shape[0]):
        frame = seq[t].reshape(2, 21, 3)  # (2 hands, 21 landmarks, 3 coords)
        
        for hand_idx in range(2):
            hand = frame[hand_idx]  # (21, 3)
            
            # Check if hand has data (not all zeros)
            if np.sum(np.abs(hand)) > 0:
                xs = hand[:, 0]
                ys = hand[:, 1]
                zs = hand[:, 2]
                
                # Get bounding box
                min_x, max_x = xs.min(), xs.max()
                min_y, max_y = ys.min(), ys.max()
                
                range_x = max_x - min_x
                range_y = max_y - min_y
                
                # Normalize x, y relative to bounding box
                if range_x > 0:
                    hand[:, 0] = (xs - min_x) / range_x
                if range_y > 0:
                    hand[:, 1] = (ys - min_y) / range_y
                # Keep z as is (or normalize if needed)
                
                frame[hand_idx] = hand
        
        normalized[t] = frame.reshape(126)
    
    return normalized

# Dataset with normalization
class KeypointDataset(Dataset):
    def __init__(self, split):
        self.files = []
        self.labels = []
        base = os.path.join(KEYPOINT_DIR, split)
        classes = sorted(os.listdir(base))
        self.classes = classes
        
        for idx, c in enumerate(classes):
            folder = os.path.join(base, c)
            for f in glob.glob(folder + "/*.npy"):
                self.files.append(f)
                self.labels.append(idx)
        
        print(f"{split} dataset: {len(self.files)} samples, {len(classes)} classes")
    
    def __len__(self):
        return len(self.files)
    
    def __getitem__(self, i):
        x = np.load(self.files[i]).astype(np.float32)
        
        # Pad or truncate to SEQ_LEN
        if x.shape[0] < SEQ_LEN:
            pad = np.zeros((SEQ_LEN - x.shape[0], x.shape[1]), dtype=np.float32)
            x = np.vstack([x, pad])
        else:
            x = x[:SEQ_LEN]
        
        # Normalize landmarks
        x = normalize_landmarks(x)
        
        return torch.from_numpy(x), torch.tensor(self.labels[i], dtype=torch.long)

# Load datasets
train_ds = KeypointDataset("train")
test_ds = KeypointDataset("test")
INPUT_SIZE = 126  # Fixed: 21 landmarks * 3 coords * 2 hands

print("\nClasses:", train_ds.classes)
print("Input size per frame:", INPUT_SIZE)

# Save class names for Android app
with open(CLASS_NAMES_JSON, 'w') as f:
    json.dump(train_ds.classes, f)
print(f"Saved class names to {CLASS_NAMES_JSON}")

train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
test_loader = DataLoader(test_ds, batch_size=BATCH_SIZE, num_workers=0)

# Model: BiLSTM with Attention
class BiLSTMAttn(nn.Module):
    def __init__(self, input_size, hidden_size, num_classes, dropout=0.4):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size, 
            hidden_size, 
            num_layers=2,
            batch_first=True, 
            bidirectional=True,
            dropout=dropout
        )
        self.attn = nn.Linear(hidden_size * 2, 1)
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_size * 2, num_classes)
        self.bn = nn.BatchNorm1d(hidden_size * 2)
    
    def forward(self, x):
        # x: (B, T, F)
        out, _ = self.lstm(x)  # (B, T, H*2)
        
        # Attention mechanism
        attn_weights = torch.softmax(self.attn(out), dim=1)  # (B, T, 1)
        context = torch.sum(attn_weights * out, dim=1)  # (B, H*2)
        
        # Batch norm + dropout + FC
        context = self.bn(context)
        context = self.dropout(context)
        logits = self.fc(context)
        
        return logits


if __name__ == '__main__':
    # Initialize model
    model = BiLSTMAttn(INPUT_SIZE, HIDDEN, len(train_ds.classes)).to(DEVICE)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=LR, weight_decay=1e-5)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='max', factor=0.5, patience=5)

    print(f"\nModel parameters: {sum(p.numel() for p in model.parameters()):,}")
    print(f"Training on: {DEVICE}\n")

    # Training loop
    best_acc = 0.0
    patience_counter = 0
    EARLY_STOP_PATIENCE = 15

    for epoch in range(1, EPOCHS + 1):
        # Train
        model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0
        
        for X, y in tqdm(train_loader, desc=f"Epoch {epoch}/{EPOCHS}"):
            X, y = X.to(DEVICE), y.to(DEVICE)
            
            optimizer.zero_grad()
            logits = model(X)
            loss = criterion(logits, y)
            loss.backward()
            
            # Gradient clipping
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            
            optimizer.step()
            
            train_loss += loss.item()
            preds = logits.argmax(dim=1)
            train_correct += (preds == y).sum().item()
            train_total += y.size(0)
        
        train_acc = train_correct / train_total
        avg_train_loss = train_loss / len(train_loader)
        
        # Validation
        model.eval()
        val_correct = 0
        val_total = 0
        val_loss = 0.0
        
        with torch.no_grad():
            for X, y in test_loader:
                X, y = X.to(DEVICE), y.to(DEVICE)
                logits = model(X)
                loss = criterion(logits, y)
                val_loss += loss.item()
                
                preds = logits.argmax(dim=1)
                val_correct += (preds == y).sum().item()
                val_total += y.size(0)
        
        val_acc = val_correct / val_total
        avg_val_loss = val_loss / len(test_loader)
        
        print(f"Epoch {epoch:3d} | Train Loss: {avg_train_loss:.4f} | Train Acc: {train_acc*100:.2f}% | "
              f"Val Loss: {avg_val_loss:.4f} | Val Acc: {val_acc*100:.2f}%")
        
        # Learning rate scheduling
        scheduler.step(val_acc)
        
        # Save best model
        if val_acc > best_acc:
            best_acc = val_acc
            patience_counter = 0
            
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_acc': val_acc,
                'class_names': train_ds.classes
            }, SAVE_PTH)
            print(f"✅ Saved best model with val_acc: {val_acc*100:.2f}%")
        else:
            patience_counter += 1
        
        # Early stopping
        if patience_counter >= EARLY_STOP_PATIENCE:
            print(f"\n⚠️ Early stopping triggered after {epoch} epochs")
            break

    print(f"\n🎉 Training completed!")
    print(f"Best validation accuracy: {best_acc*100:.2f}%")

    # Export to TorchScript for Android
    print("\n📱 Exporting to TorchScript for Android...")

    # Load best model
    checkpoint = torch.load(SAVE_PTH, map_location='cpu')
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    model.cpu()

    # Trace model
    example_input = torch.randn(1, SEQ_LEN, INPUT_SIZE)
    traced_model = torch.jit.trace(model, example_input)

    # Optimize for mobile
    traced_model_optimized = torch.jit.optimize_for_inference(traced_model)

    # Save
    traced_model_optimized.save(SAVE_TORCHSCRIPT)
    print(f"✅ Saved TorchScript model to {SAVE_TORCHSCRIPT}")
    print(f"✅ Model ready for Android integration!")

    # Test the exported model
    print("\n🧪 Testing exported model...")
    test_output = traced_model_optimized(example_input)
    print(f"Test output shape: {test_output.shape}")
    print(f"Expected: (1, {len(train_ds.classes)})")