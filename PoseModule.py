import time
import mediapipe as mp
import cv2
import math

class poseDetector():
    def __init__(self, mode=False, smooth=True, detectionCon=0.5, trackCon=0.5):
        self.mode = mode
        self.model_complexity = 1
        self.smooth_landmarks = smooth
        self.enable_segmentation = False
        self.smooth_segmentation = True
        self.detectionCon = detectionCon
        self.trackCon = trackCon
        self.mpDraw = mp.solutions.drawing_utils
        self.mpPose = mp.solutions.pose
        self.pose = self.mpPose.Pose(self.mode,self.model_complexity,self.smooth_landmarks,self.enable_segmentation,self.smooth_segmentation,self.detectionCon,self.trackCon)

    def findPose(self,image,draw=True):
        imageRGB = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        self.results = self.pose.process(imageRGB)
        # print(self.results.pose_landmarks)

        if draw and self.results.pose_landmarks :
            self.mpDraw.draw_landmarks(image, self.results.pose_landmarks,self.mpPose.POSE_CONNECTIONS)
        return image

    def findPosition(self,image,draw=True):
        self.lmList = []
        if self.results.pose_landmarks:
            for points ,lm in enumerate(self.results.pose_landmarks.landmark):
                h , w , c = image.shape
                cx , cy  = int(lm.x * w) , int(lm.y * h)
                self.lmList.append([points,cx,cy])
                if draw:
                    cv2.circle(image , (cx,cy) , 8 , (255,0,0) , cv2.FILLED)
        return self.lmList

    def findAngle(self, image , p1, p2 , p3 , draw = False):
        x1 , y1 = self.lmList[p1][1:]
        x2 , y2 = self.lmList[p2][1:]
        x3 , y3 = self.lmList[p3][1:]

        angle = math.degrees(math.atan2(y3 - y2, x3 - x2) - math.atan2(y1 - y2, x1 - x2))
        if angle < 0:
            angle += 360

        if angle > 180:
            angle = 360 - angle
        # print(angle)
        if draw :
            cv2.line(image,(x1,y1),(x2,y2),(255,255,0),3)
            cv2.line(image,(x3,y3),(x2,y2),(255,255,0),3)


            cv2.circle(image, (x1, y1), 10, (255, 0, 0), cv2.FILLED)
            cv2.circle(image, (x1, y1), 15, (255, 0, 0), 2)
            cv2.circle(image, (x2, y2), 10, (255, 0, 0), cv2.FILLED)
            cv2.circle(image, (x2, y2), 15, (255, 0, 0), 2)
            cv2.circle(image, (x3, y3), 10, (255, 0, 0), cv2.FILLED)
            cv2.circle(image, (x3, y3), 15, (255, 0, 0), 2)

            cv2.putText(image , str(int(angle)),(x2+25,y2+5),cv2.FONT_HERSHEY_PLAIN,2,(0,0,255),2)
        return angle
