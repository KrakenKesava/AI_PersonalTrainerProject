                    
from exercises.pullup import PullupAnalyser

def get_exercise(name):

    if name.lower() == "pullup":
        return PullupAnalyser(), 60, 150

             
    raise ValueError("Exercise not supported")