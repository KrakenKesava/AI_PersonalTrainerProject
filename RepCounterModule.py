                     

class RepCounter:
    def __init__(self, top_threshold=60, bottom_threshold=150):
        self.rep_count = 0
        self.direction = 0               
        self.top = top_threshold
        self.bottom = bottom_threshold
        self.max_angle_reached = 0
        self.min_angle_reached = 180

    def update(self, angle):
        rep_done = False
        
                      
        self.min_angle_reached = min(self.min_angle_reached, angle)
        self.max_angle_reached = max(self.max_angle_reached, angle)

                                  
        if angle < self.top and self.direction == 0:
            self.direction = 1 
            
                                    
        if angle > self.bottom and self.direction == 1:
            self.direction = 0 
            self.rep_count += 1
            rep_done = True
            
                   
            self.min_angle_reached = 180
            self.max_angle_reached = 0

        return self.rep_count, rep_done

    def set_thresholds(self, top, bottom):
        self.top = top
        self.bottom = bottom
        self.direction = 0 
