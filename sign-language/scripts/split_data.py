import os, shutil, random

DATA_DIR = "data_record"
TRAIN_DIR = "keypoints_6/train"
TEST_DIR = "keypoints_6/test"
SPLIT = 0.8

os.makedirs(TRAIN_DIR, exist_ok=True)
os.makedirs(TEST_DIR, exist_ok=True)

for cls in os.listdir(DATA_DIR):
    class_dir = os.path.join(DATA_DIR, cls)
    if not os.path.isdir(class_dir):
        continue

    files = os.listdir(class_dir)
    random.shuffle(files)

    split_idx = int(len(files) * SPLIT)
    train_files = files[:split_idx]
    test_files = files[split_idx:]

    os.makedirs(os.path.join(TRAIN_DIR, cls), exist_ok=True)
    os.makedirs(os.path.join(TEST_DIR, cls), exist_ok=True)

    for f in train_files:
        shutil.copy(os.path.join(class_dir, f), os.path.join(TRAIN_DIR, cls, f))
    for f in test_files:
        shutil.copy(os.path.join(class_dir, f), os.path.join(TEST_DIR, cls, f))

print(" Split complete!")
