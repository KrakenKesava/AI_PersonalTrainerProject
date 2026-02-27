# exercises/base_exercise.py
import time

class BaseExercise:

    def __init__(self):
        self.reset()

    def reset(self):
        self.min_angle = 180.0
        self.max_angle = 0.0
        self.rep_start_time = None
        self.prev_angle = None
        self.angle_velocity_sum = 0.0
        self.frame_count = 0

    def update(self, angle):
        self.min_angle = min(self.min_angle, float(angle))
        self.max_angle = max(self.max_angle, float(angle))

        if self.prev_angle is not None:
            if self.rep_start_time is None:
                self.rep_start_time = time.time()

            velocity = abs(angle - self.prev_angle)
            self.angle_velocity_sum += velocity

        self.prev_angle = angle
        self.frame_count += 1

    def calculate_tempo(self):
        if self.rep_start_time:
            return round(time.time() - self.rep_start_time, 2)
        return 0

    def get_live_feedback(self, angle):
        return "Analyzing Form..."