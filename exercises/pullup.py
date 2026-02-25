# pullup.py
import time

class PullupAnalyser:

    def __init__(self):
        self.min_angle = 180
        self.max_angle = 0
        self.rep_start_time = None
        self.prev_angle = None
        self.angle_velocity_sum = 0
        self.frame_count = 0

    def update(self, angle):
        """
        Call every frame to track motion and tempo
        """

        # Track ROM
        self.min_angle = min(self.min_angle, angle)
        self.max_angle = max(self.max_angle, angle)

        # Start timer when movement begins
        if self.rep_start_time is None:
            self.rep_start_time = time.time()

        # Track smoothness (velocity changes)
        if self.prev_angle is not None:
            velocity = abs(angle - self.prev_angle)
            self.angle_velocity_sum += velocity

        self.prev_angle = angle
        self.frame_count += 1

    def analyse_rep(self):
        """
        Call when rep_completed == True
        """

        feedback = []
        formCorrect = True

        # =========================
        # RANGE OF MOTION
        # =========================
        rom = self.max_angle - self.min_angle
        if rom < 90:
            feedback.append("Increase range of motion")
            formCorrect = False

        # =========================
        # TOP CHECK
        # =========================
        if self.min_angle > 55:
            feedback.append("Pull higher")
            formCorrect = False
        else:
            feedback.append("Good pull height")

        # =========================
        # BOTTOM CHECK
        # =========================
        if self.max_angle < 145:
            feedback.append("Extend fully")
            formCorrect = False
        else:
            feedback.append("Full extension correct")

        # =========================
        # TEMPO CHECK
        # =========================
        rep_time = time.time() - self.rep_start_time if self.rep_start_time else 0

        if rep_time < 0.8:
            feedback.append("Too fast - slow down")
            formCorrect = False
        elif rep_time > 4:
            feedback.append("Good control")
        else:
            feedback.append("Nice tempo")   # Tempo = The speed at which you perform one full repetition.

        # =========================
        # SMOOTHNESS CHECK
        # =========================
        if self.frame_count > 0:
            avg_velocity = self.angle_velocity_sum / self.frame_count
            if avg_velocity > 8:
                feedback.append("Reduce swinging")
                formCorrect = False

        if formCorrect:
            feedback.append("Perfect Pull-Up!")

        # RESET
        self.min_angle = 180
        self.max_angle = 0
        self.rep_start_time = None
        self.prev_angle = None
        self.angle_velocity_sum = 0
        self.frame_count = 0

        return {
            "formCorrect": formCorrect,
            "feedback": feedback,
            "rom": round(rom, 1),
            "repTime": round(rep_time, 2)
        }