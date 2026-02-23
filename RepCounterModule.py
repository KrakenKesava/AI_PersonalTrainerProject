class Reps_Counter:
    def __init__(self):
        self.rep_count = 0
        self.directionOfExercise = 0  # 0 = going up, 1 = going down

    def update(self, per):
        rep_completed = False

        # Top reached
        if per >= 90:
            if self.directionOfExercise == 0:
                self.rep_count += 0.5
                self.directionOfExercise = 1

        # Bottom reached → FULL REP COMPLETE
        if per <= 20:
            if self.directionOfExercise == 1:
                self.rep_count += 0.5
                self.directionOfExercise = 0
                rep_completed = True   # 🔥 IMPORTANT

        return self.rep_count, self.directionOfExercise, rep_completed