# pullup.py
import time
from .base_exercise import BaseExercise

class PullupAnalyser(BaseExercise):
    def __init__(self):
        super().__init__()

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
        
        # Specific Feedback for Pullups
        if rom < 85:
            feedback.append("Drastic partial range! Focus on full movement.")
            formCorrect = False
        elif rom < 110:
            feedback.append("Incomplete range - work on depth/height")
            formCorrect = False

        # =========================
        # TOP CHECK (Chin above bar)
        # =========================
        # Min angle 55 is good, but let's be more descriptive
        if self.min_angle > 65:
            feedback.append("PULL HIGHER: Chin not reaching the bar")
            formCorrect = False
        elif self.min_angle > 50:
            feedback.append("Close to top, but pull slightly higher")
        else:
            feedback.append("Great pull height - chin cleared!")

        # =========================
        # BOTTOM CHECK (Dead hang / Lockout)
        # =========================
        if self.max_angle < 140:
            feedback.append("EXTEND FULLY: Arm lockout missing at bottom")
            formCorrect = False
        elif self.max_angle < 155:
            feedback.append("Almost full extension - drop slightly lower")
        else:
            feedback.append("Full extension reached")

        # =========================
        # TEMPO CHECK
        # =========================
        rep_time = self.calculate_tempo()
        if rep_time < 0.7:
            feedback.append("Too explosive/fast - control the drop")
            formCorrect = False
        elif rep_time > 4.5:
            feedback.append("Good slow control")
        else:
            feedback.append("Stable tempo")

        # =========================
        # SMOOTHNESS CHECK
        # =========================
        if self.frame_count > 0:
            avg_velocity = self.angle_velocity_sum / self.frame_count
            if avg_velocity > 10:
                feedback.append("WARNING: Excessive swinging/kicking detected")
                formCorrect = False

        if formCorrect:
            feedback.append("PRO FORM: Perfect Pull-Up!")

        result = {
            "formCorrect": formCorrect,
            "feedback": feedback,
            "rom": round(rom, 1),
            "repTime": round(rep_time, 2)
        }
        
        self.reset()
        return result

    def get_live_feedback(self, angle):
        if angle > 150:
            return "PULL UP"
        elif angle < 60:
            return "GOOD TOP - LOWER FULLY"
        elif angle < 100:
            return "ALMOST AT TOP"
        return "KEEP MOVING"
