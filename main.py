import cv2
import numpy as np
import time
import sourceSelectorGUI as gui
import PoseModule as pm
import RepCounterModule as rep
# ==============================
# INIT
# ==============================
source, cam_name = gui.launch_gui()
detector = pm.poseDetector()
reps = rep.Reps_Counter()

if source is None:
    print("No source selected")
    exit()

print(f"Started Source: {cam_name}")

pTime = 0

# ==============================
# FUNCTION → PROCESS FRAME
# ==============================
def process_frame(img):
    img = detector.findPose(img)
    lmList = detector.findPosition(img, False)

    # print(lmList)
    if len(lmList) != 0:
        # rightArmAngle = detector.findAngle(img, 12, 14, 16, True)
        leftArmAngle = detector.findAngle(img, 11, 13, 15, True)

    leftArmPer = np.interp(leftArmAngle,(20,130) , (100,0))  # change the angles 20 -> 130 with respect to the exercise
    leftArmPer = np.clip(leftArmPer,0,100) # this exercise readings are for pull ups
    reps_count = reps.update(leftArmPer)
    print(str(int(reps_count)) ,leftArmAngle, leftArmPer)
    return img , reps_count , leftArmPer


# ==============================
# CASE 1 → IMAGE
# ==============================
if isinstance(source, np.ndarray):

    img = process_frame(source.copy())

    while True:
        cv2.imshow(f"AI Input - {cam_name}", img)

        if cv2.waitKey(1) & 0xFF == 27:
            break


# ==============================
# CASE 2 → CAMERA / VIDEO
# ==============================
else:
    cap = source

    while True:
        success, img = cap.read()

        if not success:
            print("Stream ended or failed.")
            break

        # Optional: Resize for speed
        # img = cv2.resize(img, (640, 360))

        img , reps_count , percentage = process_frame(img)

        # FPS Calculation (smoothed)
        cTime = time.time()
        fps = 1 / (cTime - pTime) if pTime != 0 else 0
        pTime = cTime

        # ===============================
        # TEXT POSITIONS
        # ===============================

        fps_x, fps_y = 30, 40
        reps_x, reps_y = 30, 90

        cv2.putText(img, f"FPS: {int(fps)}",
                    (fps_x, fps_y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0), 2)

        cv2.putText(img, f"Reps: {int(reps_count)}",
                    (reps_x, reps_y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.2,
                    (255, 0, 0), 3)

        # ===============================
        # VERTICAL PROGRESS BAR
        # ===============================

        # Bar size
        bar_height_total = 300  # total height of bar
        bar_width = 40  # width of bar

        # Position (below Reps)
        bar_x1 = 50
        bar_y1 = 150
        bar_x2 = bar_x1 + bar_width
        bar_y2 = bar_y1 + bar_height_total

        # Convert percentage to filled height
        filled_height = np.interp(percentage, (0, 100), (0, bar_height_total))

        # Calculate top of filled region (bottom-up fill)
        fill_y = int(bar_y2 - filled_height)

        # Draw outer border
        cv2.rectangle(img,
                      (bar_x1, bar_y1),
                      (bar_x2, bar_y2),
                      (0, 255, 0),
                      2)

        # Draw filled portion (BOTTOM → UP)
        cv2.rectangle(img,
                      (bar_x1, fill_y),
                      (bar_x2, bar_y2),
                      (0, 255, 0),
                      cv2.FILLED)

        # Percentage text ABOVE bar
        cv2.putText(img,
                    f"{int(percentage)}%",
                    (bar_x1 - 10, bar_y1 - 15),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (255, 255, 255),
                    2)

        cv2.imshow(f"AI Input - {cam_name}", img)

        if cv2.waitKey(10) & 0xFF == 27:
            break

    cap.release()

cv2.destroyAllWindows()