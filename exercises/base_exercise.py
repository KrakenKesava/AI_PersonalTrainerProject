# exercises/base_exercise.py
import time

class BaseExercise:

    def __init__(self):
        self.reset()

    def reset(self):
        self.min_angle = 180
        self.max_angle = 0
        self.rep_start_time = None
        self.prev_angle = None
        self.angle_velocity_sum = 0
        self.frame_count = 0

    def update(self, angle):
        self.min_angle = min(self.min_angle, angle)
        self.max_angle = max(self.max_angle, angle)

        if self.prev_angle is not None:
            if angle < self.prev_angle and self.rep_start_time is None:
                self.rep_start_time = time.time()

            velocity = abs(angle - self.prev_angle)
            self.angle_velocity_sum += velocity

        self.prev_angle = angle
        self.frame_count += 1

    def calculate_tempo(self):
        if self.rep_start_time:
            return time.time() - self.rep_start_time
        return 0