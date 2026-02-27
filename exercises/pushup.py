# pushup.py
import time
from .base_exercise import BaseExercise

class PushupAnalyser(BaseExercise):
    def __init__(self):
        super().__init__()

    def analyse_rep(self):
        """
        Call when rep_completed == True
        """
        feedback = []
        formCorrect = True

        # =========================
        # RANGE OF MOTION (ROM)
        # =========================
        rom = self.max_angle - self.min_angle
        if rom < 60:
            feedback.append("Drastic partial range! Move deeper between top and bottom.")
            formCorrect = False
        elif rom < 80:
            feedback.append("Increase range of motion for better chest engagement")
            formCorrect = False

        # =========================
        # TOP CHECK (Lockout)
        # =========================
        if self.max_angle < 150:
            feedback.append("LOCKOUT ERROR: Fully straighten arms at the top")
            formCorrect = False
        elif self.max_angle < 165:
            feedback.append("Almost full lockout - push all the way up")
        else:
            feedback.append("Good full lockout reached")

        # =========================
        # BOTTOM CHECK (Depth)
        # =========================
        if self.min_angle > 95:
            feedback.append("DEPTH ERROR: Go lower, chest closer to floor")
            formCorrect = False
        elif self.min_angle > 80:
            feedback.append("Good depth, but can go slightly lower")
        else:
            feedback.append("Excellent depth reached")

        # =========================
        # TEMPO CHECK
        # =========================
        rep_time = self.calculate_tempo()
        if rep_time < 0.9:
            feedback.append("Too fast - control the descent and push")
            formCorrect = False
        elif rep_time > 3.5:
            feedback.append("Great steady control")
        else:
            feedback.append("Solid tempo")

        if formCorrect:
            feedback.append("PRO FORM: Perfect Push-up!")

        # Capture results before reset
        result = {
            "formCorrect": formCorrect,
            "feedback": feedback,
            "rom": round(rom, 1),
            "repTime": round(rep_time, 2)
        }
        
        self.reset()
        return result

    def get_live_feedback(self, angle):
        if angle > 160:
            return "LOWER YOUR CHEST"
        elif angle < 75:
            return "GREAT DEPTH - PUSH UP"
        elif angle < 110:
            return "ALMOST AT BOTTOM"
        return "KEEP MOVING"
