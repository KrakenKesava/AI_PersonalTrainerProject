class Reps_Counter:
    def __init__(self):
        self.rep_count = 0
        self.directionOfExercise = 0

    def update(self,per):
        if per >= 90:
            if self.directionOfExercise == 0:
                self.rep_count += 0.5
                self.directionOfExercise = 1

        if per <= 20:
            if self.directionOfExercise == 1:
                self.rep_count += 0.5
                self.directionOfExercise = 0
        return self.rep_count