# plank.py
import time
from .base_exercise import BaseExercise

class PlankAnalyser(BaseExercise):
    def __init__(self):
        super().__init__()

    def analyse_rep(self):
        """
        Since Plank is a static hold, this may only be called if the user wobbles and triggers the rep counter.
        It returns an assessment of the body angle during the hold.
        """
        feedback = []
        formCorrect = True

        # For plank, the shoulder-hip-ankle angle should be fairly straight (~160-180 degrees)
        if self.min_angle < 150:
            feedback.append("HIPS TOO LOW: Keep your core tight and body straight")
            formCorrect = False
        else:
            feedback.append("Good straight posture maintained")

        rep_time = self.calculate_tempo()
        if formCorrect:
            feedback.append("PRO FORM: Solid Plank Hold!")

        result = {
            "formCorrect": formCorrect,
            "feedback": feedback,
            "rom": round(self.max_angle - self.min_angle, 1),
            "repTime": round(rep_time, 2)
        }

        self.reset()
        return result

    def get_live_feedback(self, angle):
        if angle < 150:
            return "HIPS TOO LOW - KEEP BODY STRAIGHT"
        elif angle > 185:
            return "HIPS TOO HIGH - LOWER SLIGHTLY"
        return "GREAT FORM - HOLD IT"
