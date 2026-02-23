import cv2
import numpy as np
import time
import sourceSelectorGUI as gui
import PoseModule as pm
import RepCounterModule as rep
import ExercisesAnalyser as ea

# ==============================
# INIT
# ==============================
source, cam_name = gui.launch_gui()
detector = pm.poseDetector()
reps = rep.Reps_Counter()

min_angle = 180
max_angle = 0
last_feedback = "Start your workout 💪"

if source is None:
    print("No source selected")
    exit()

print(f"Started Source: {cam_name}")

pTime = 0

# ==============================
# PROCESS FRAME
# ==============================
def process_frame(img):
    global min_angle, max_angle, last_feedback

    img = detector.findPose(img)
    lmList = detector.findPosition(img, False)

    leftArmAngle = 0
    leftArmPer = 0
    reps_count = reps.rep_count

    if len(lmList) != 0:
        leftArmAngle = detector.findAngle(img, 11, 13, 15, True)

        # Track motion
        min_angle = min(min_angle, leftArmAngle)
        max_angle = max(max_angle, leftArmAngle)

        leftArmPer = np.interp(leftArmAngle, (50, 160), (100, 0))
        leftArmPer = np.clip(leftArmPer, 0, 100)

        reps_count, direction, rep_done = reps.update(leftArmPer)

        # =========================
        # LIVE FEEDBACK
        # =========================
        if leftArmPer < 30:
            live_feedback = "Pull up"
        elif leftArmPer > 80:
            live_feedback = "Almost there"
        else:
            live_feedback = "Good motion"

        if not rep_done:
            last_feedback = live_feedback

        # =========================
        # REP FEEDBACK
        # =========================
        if rep_done:
            result_top = ea.analyse_pullup(min_angle, 0)
            result_bottom = ea.analyse_pullup(max_angle, 1)

            feedback_list = result_top["feedback"] + result_bottom["feedback"]
            last_feedback = " | ".join(feedback_list)

            print("REP RESULT:", feedback_list)

            min_angle = 180
            max_angle = 0

    return img, reps_count, leftArmPer, last_feedback


# ==============================
# IMAGE MODE
# ==============================
if isinstance(source, np.ndarray):

    img, _, _, _ = process_frame(source.copy())

    while True:
        cv2.imshow(f"AI Input - {cam_name}", img)

        if cv2.waitKey(1) & 0xFF == 27:
            break


# ==============================
# VIDEO / CAMERA MODE
# ==============================
else:
    cap = source

    while True:
        success, img = cap.read()

        if not success:
            print("Stream ended or failed.")
            break

        img, reps_count, percentage, feedback = process_frame(img)

        # ===============================
        # FPS
        # ===============================
        cTime = time.time()
        fps = 1 / (cTime - pTime) if pTime != 0 else 0
        pTime = cTime

        # ===============================
        # TOP LEFT STATS
        # ===============================
        cv2.putText(img, f"FPS: {int(fps)}",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0), 2)

        cv2.putText(img, f"Reps: {int(reps_count)}",
                    (20, 90),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.2,
                    (255, 0, 0), 3)

        # ===============================
        # PROGRESS BAR
        # ===============================
        bar_height_total = 300
        bar_width = 40

        bar_x1 = 50
        bar_y1 = 150
        bar_x2 = bar_x1 + bar_width
        bar_y2 = bar_y1 + bar_height_total

        filled_height = np.interp(percentage, (0, 100), (0, bar_height_total))
        fill_y = int(bar_y2 - filled_height)

        cv2.rectangle(img,
                      (bar_x1, bar_y1),
                      (bar_x2, bar_y2),
                      (0, 255, 0), 2)

        cv2.rectangle(img,
                      (bar_x1, fill_y),
                      (bar_x2, bar_y2),
                      (0, 255, 0),
                      cv2.FILLED)

        cv2.putText(img,
                    f"{int(percentage)}%",
                    (bar_x1 - 10, bar_y1 - 15),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (255, 255, 255),
                    2)

        # ===============================
        # FEEDBACK BELOW BAR
        # ===============================
        x = bar_x1
        y = bar_y2 + 40

        display_feedback = feedback if feedback else "Analyzing..."
        lines = display_feedback.split("|")

        # prevent overflow
        if y + (len(lines) * 40) > img.shape[0]:
            y = img.shape[0] - (len(lines) * 40) - 10

        for i, line in enumerate(lines):
            line = line.strip()

            (text_w, text_h), _ = cv2.getTextSize(
                line,
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                2
            )

            # background
            cv2.rectangle(img,
                          (x - 10, y - text_h - 12 + i*40),
                          (x + text_w + 10, y + 8 + i*40),
                          (20, 20, 20),
                          cv2.FILLED)

            # color logic
            if "Good" in line or "correct" in line.lower():
                color = (0, 255, 0)
            elif "Pull" in line or "Extend" in line:
                color = (0, 0, 255)
            else:
                color = (0, 255, 255)

            # text
            cv2.putText(img,
                        line,
                        (x, y + i*40),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        color,
                        2)

        cv2.imshow(f"AI Input - {cam_name}", img)

        if cv2.waitKey(10) & 0xFF == 27:
            break

    cap.release()

cv2.destroyAllWindows()