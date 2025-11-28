import os, numpy as np
from collections import Counter

# 1. Are there .npy files?
for split in ("keypoints/train","keypoints/test"):
    count = 0
    for root,_,files in os.walk(split):
        for f in files:
            if f.endswith(".npy"):
                count += 1
    print(split, "files:", count)

# 2. Example shape check (print one sample shape)
sample = None
for root,_,files in os.walk("keypoints/train"):
    for f in files:
        if f.endswith(".npy"):
            sample = os.path.join(root,f); break
    if sample: break
print("example file:", sample)
d = np.load(sample)
print("shape:", d.shape)  # (frames, features)

# 3. class distribution
labels = []
for label in os.listdir("keypoints/train"):
    p = os.path.join("keypoints/train", label)
    if os.path.isdir(p):
        files = [f for f in os.listdir(p) if f.endswith(".npy")]
        labels += [label] * len(files)
print("train counts:", Counter(labels))
