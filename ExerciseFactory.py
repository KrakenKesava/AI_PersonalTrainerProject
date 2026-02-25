# ExerciseFactory.py
from exercises.pullup import PullupAnalyser

def get_exercise(name):

    if name.lower() == "pullup":
        return PullupAnalyser(), 60, 150

    # Future:
    # if name.lower() == "pushup":
    #     return PushUp(), 70, 160

    raise ValueError("Exercise not supported")