import cv2
import os
import time

CLASSES = ["hello", "yes", "no", "eat", "drink", "help"]
SAVE_DIR = "data_record"
FPS = 30
VIDEO_DURATION = 3  # seconds
FRAMES_PER_VIDEO = FPS * VIDEO_DURATION

# Make folders
for cls in CLASSES:
    os.makedirs(os.path.join(SAVE_DIR, cls), exist_ok=True)

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FPS, FPS)

print("✅ Recording ready!")
print("Press SPACE to start recording each video")
print("Press ESC to exit")

for cls in CLASSES:
    print(f"\n📌 Class: {cls}")
    existing = len(os.listdir(os.path.join(SAVE_DIR, cls)))
    target = 20

    for idx in range(existing, target):
        print(f"➡ Recording sample {idx+1}/{target} for {cls}")
        print("👉 Press SPACE to start")

        # Wait for space
        while True:
            ret, frame = cap.read()
            cv2.putText(frame, f"CLASS: {cls} | Press SPACE to start",
                        (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
            cv2.imshow("Recorder", frame)

            if cv2.waitKey(1) & 0xFF == ord(' '):
                break
            if cv2.waitKey(1) & 0xFF == 27:
                cap.release()
                cv2.destroyAllWindows()
                exit()

        # Countdown
        for c in range(3, 0, -1):
            ret, frame = cap.read()
            cv2.putText(frame, f"Starting in {c}",
                        (200, 200), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,0,255), 3)
            cv2.imshow("Recorder", frame)
            cv2.waitKey(1000)

        # Recording
        video_path = os.path.join(SAVE_DIR, cls, f"{cls}_{idx}.mp4")
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(video_path, fourcc, FPS, (frame.shape[1], frame.shape[0]))

        frames = 0
        start_time = time.time()

        while frames < FRAMES_PER_VIDEO:
            ret, frame = cap.read()
            out.write(frame)
            cv2.putText(frame, f"Recording {cls} {frames}/{FRAMES_PER_VIDEO}",
                        (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,255), 2)
            cv2.imshow("Recorder", frame)
            frames += 1
            if cv2.waitKey(1) & 0xFF == 27:
                break

        out.release()
        print(f"✅ Saved: {video_path}")

cap.release()
cv2.destroyAllWindows()
print("✅ Finished all recordings!")
