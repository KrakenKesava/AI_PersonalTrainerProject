# squat.py
import time
from .base_exercise import BaseExercise

class SquatAnalyser(BaseExercise):
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
        if rom < 70:
            feedback.append("Drastic partial range! Squat deeper for effective results.")
            formCorrect = False
        elif rom < 95:
            feedback.append("Incomplete range - focus on hip-to-knee depth")
            formCorrect = False

        # =========================
        # TOP CHECK (Lockout)
        # =========================
        if self.max_angle < 155:
            feedback.append("LOCKOUT ERROR: Stand up fully at the top")
            formCorrect = False
        elif self.max_angle < 170:
            feedback.append("Almost full stand - push hips forward at top")
        else:
            feedback.append("Good full lockout reached")

        # =========================
        # BOTTOM CHECK (Parallel)
        # =========================
        if self.min_angle > 90:
            feedback.append("DEPTH ERROR: Hips must reach at least knee level")
            formCorrect = False
        elif self.min_angle > 75:
            feedback.append("Good depth, parallel point achieved")
        else:
            feedback.append("Excellent depth - below parallel!")

        # =========================
        # TEMPO CHECK
        # =========================
        rep_time = self.calculate_tempo()
        if rep_time < 1.1:
            feedback.append("Too fast - control the descent to avoid injury")
            formCorrect = False
        elif rep_time > 4.2:
            feedback.append("Great steady control")
        else:
            feedback.append("Solid tempo")

        if formCorrect:
            feedback.append("PRO FORM: Perfect Squat!")

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
        if angle > 165:
            return "SQUAT DOWN"
        elif angle < 85:
            return "EXCELLENT DEPTH - STAND UP"
        elif angle < 110:
            return "ALMOST AT PARALLEL"
        return "KEEP MOVING"
