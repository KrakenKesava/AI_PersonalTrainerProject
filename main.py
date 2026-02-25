import cv2
import numpy as np
import time
import sourceSelectorGUI as gui
import PoseModule as pm
import RepCounterModule as rep

# ==============================
# INIT
# ==============================

source, cam_name, exercise_name = gui.launch_gui()

if source is None:
    print("No source selected")
    exit()

print(f"Started Source: {cam_name}")
print(f"Selected Exercise: {exercise_name}")

detector = pm.poseDetector()
reps = rep.RepCounter()

# ==============================
# Exercise Selection
# ==============================

if exercise_name == "pullup":
    from exercises.pullup import PullupAnalyser
    analyser = PullupAnalyser()
    angle_points = (11, 13, 15)  # shoulder, elbow, wrist

# elif exercise_name == "pushup":
#     from exercises.pushup import PushupAnalyser
#     analyser = PushupAnalyser()
#     angle_points = (11, 13, 15)
#
# elif exercise_name == "squat":
#     from exercises.squat import SquatAnalyser
#     analyser = SquatAnalyser()
#     angle_points = (23, 25, 27)  # hip, knee, ankle

else:
    raise ValueError("Unsupported exercise selected")

last_feedback = "Start your workout"
pTime = 0


# ==============================
# PROCESS FRAME
# ==============================

def process_frame(img):
    global last_feedback

    img = detector.findPose(img)
    lmList = detector.findPosition(img, False)

    reps_count = reps.rep_count
    percentage = 0

    if len(lmList) != 0:

        angle = detector.findAngle(
            img,
            angle_points[0],
            angle_points[1],
            angle_points[2],
            True
        )

        analyser.update(angle)

        # UI percentage (for progress bar only)
        percentage = np.interp(angle, (50, 160), (100, 0))
        percentage = np.clip(percentage, 0, 100)

        # 🔥 IMPORTANT: Rep logic must use ANGLE
        reps_count, rep_done = reps.update(angle)

        if not rep_done:
            if hasattr(analyser, "get_live_feedback"):
                last_feedback = analyser.get_live_feedback(angle)
            else:
                last_feedback = "Analyzing..."

        if rep_done:
            result = analyser.analyse_rep()
            last_feedback = " | ".join(result["feedback"])
            print("REP RESULT:", result)

    return img, reps_count, percentage, last_feedback


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

        lines = feedback.split("|")

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

            cv2.rectangle(img,
                          (x - 10, y - text_h - 12 + i*40),
                          (x + text_w + 10, y + 8 + i*40),
                          (20, 20, 20),
                          cv2.FILLED)

            if "Good" in line or "correct" in line.lower():
                color = (0, 255, 0)
            elif "Pull" in line or "Extend" in line:
                color = (0, 0, 255)
            else:
                color = (0, 255, 255)

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