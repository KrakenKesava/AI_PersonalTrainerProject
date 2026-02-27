# RepCounterModule.py

class RepCounter:
    def __init__(self, top_threshold=60, bottom_threshold=150):
        self.rep_count = 0
        self.direction = 0 # 0 = Going UP (angle decreasing), 1 = Going DOWN (angle increasing)
        self.top = top_threshold
        self.bottom = bottom_threshold
        self.max_angle_reached = 0
        self.min_angle_reached = 180

    def update(self, angle):
        rep_done = False
        
        # Track angles within the current rep cycle if needed
        self.min_angle_reached = min(self.min_angle_reached, angle)
        self.max_angle_reached = max(self.max_angle_reached, angle)

        # Logic: 
        # For Pullups: Top is e.g. 70 (chin over barish), Bottom is 150 (arms straight)
        # Movement: Starts at Bottom (150). Goes UP to Top (70). Then DOWN to Bottom (150).
        
        # 1. Detect UPWARD movement completed (reaching or passing the top threshold)
        if angle < self.top and self.direction == 0:
            self.direction = 1 # Now looking for the return to bottom
            
        # 2. Detect DOWNWARD movement completed (reaching or passing the bottom threshold)
        if angle > self.bottom and self.direction == 1:
            self.direction = 0 # Reset for next rep
            self.rep_count += 1
            rep_done = True
            # Reset local rep tracking
            self.min_angle_reached = 180
            self.max_angle_reached = 0

        return self.rep_count, rep_done

    def set_thresholds(self, top, bottom):
        self.top = top
        self.bottom = bottom
        # Reset state on significant threshold change to avoid stuck counters
        self.direction = 0 