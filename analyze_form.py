import cv2
import os
import sys

# Add project root to path to import modules
sys.path.append('d:/Projects/AIPersonalTrainerProject')

import PoseModule as pm
import RepCounterModule as rep
from exercises.pullup import PullupAnalyser

def analyze_video(video_path):
    print(f"\nAnalyzing: {video_path}")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video {video_path}")
        return []

    detector = pm.poseDetector()
    counter = rep.RepCounter(top_threshold=100, bottom_threshold=115)
    analyser = PullupAnalyser()
    
    rep_results = []
    video_min = 180.0
    video_max = 0.0
    
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break
            
        frame = detector.findPose(frame, draw=False)
        lmList = detector.findPosition(frame, draw=False)
        
        if len(lmList) != 0:
            angle = detector.findAngle(frame, 11, 13, 15, draw=False)
            video_min = min(video_min, float(angle))
            video_max = max(video_max, float(angle))
            
            analyser.update(angle)
            reps_count, rep_done = counter.update(angle)
            
            if rep_done:
                result = analyser.analyse_rep()
                rep_results.append(result)
                print(f"Rep {reps_count}: {result['feedback']}")

    cap.release()
    print(f"Video ROM: Min={video_min:.1f}, Max={video_max:.1f}, Range={video_max-video_min:.1f}")
    
    if not rep_results:
        # Check what the analyser says about the partial movement
        result = analyser.analyse_rep()
        print(f"Final partial analysis: {result['feedback']}")
        rep_results.append(result)
        
    return rep_results

if __name__ == "__main__":
    videos = [
        "d:/Projects/AIPersonalTrainerProject/exerciseVideos/Pullups/Pullup_Front_Incorrect_2.mp4",
        "d:/Projects/AIPersonalTrainerProject/exerciseVideos/Pullups/Pullup_Front_Incorrect_3.mp4"
    ]
    
    all_feedback = {}
    for video in videos:
        if os.path.exists(video):
            results = analyze_video(video)
            all_feedback[os.path.basename(video)] = results
        else:
            print(f"File not found: {video}")
