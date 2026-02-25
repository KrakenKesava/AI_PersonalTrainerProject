# RepCounter.py

class RepCounter:
    def __init__(self, top_threshold=60, bottom_threshold=150):
        self.rep_count = 0
        self.direction = 0
        self.top = top_threshold
        self.bottom = bottom_threshold

    def update(self, angle):
        rep_done = False

        if angle < self.top and self.direction == 0:
            self.direction = 1

        if angle > self.bottom and self.direction == 1:
            self.direction = 0
            self.rep_count += 1
            rep_done = True

        return self.rep_count, rep_done