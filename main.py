import cv2
import numpy as np
import time
import sourceSelectorGUI as gui
import PoseModule as pm

# ==============================
# INIT
# ==============================
source, cam_name = gui.launch_gui()
detector = pm.poseDetector()

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
        rightArmAngle = detector.findAngle(img, 12, 14, 16, True)
        leftArmAngle = detector.findAngle(img, 11, 13, 15, True)

    leftArmPer = np.interp(leftArmAngle,(20,130) , (100,0))
    leftArmPer = np.clip(leftArmPer,0,100)
    print(leftArmAngle, leftArmPer)
    return img


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

        img = process_frame(img)

        # FPS Calculation (smoothed)
        cTime = time.time()
        fps = 1 / (cTime - pTime) if pTime != 0 else 0
        pTime = cTime

        cv2.putText(img, f"FPS: {int(fps)}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1,
                    (0, 255, 0), 2)

        cv2.imshow(f"AI Input - {cam_name}", img)

        if cv2.waitKey(10) & 0xFF == 27:
            break

    cap.release()

cv2.destroyAllWindows()