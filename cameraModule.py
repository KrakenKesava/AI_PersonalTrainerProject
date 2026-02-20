# cameraModule.py

import cv2

try:
    from pygrabber.dshow_graph import FilterGraph
    WINDOWS_SUPPORT = True
except:
    WINDOWS_SUPPORT = False


def list_cameras(max_tested=5):
    available = []
    for i in range(max_tested):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.read()[0]:
            available.append(i)
        cap.release()
    return available


def get_camera_names():
    if WINDOWS_SUPPORT:
        graph = FilterGraph()
        return graph.get_input_devices()
    return None


def choose_camera():
    indexes = list_cameras()
    names = get_camera_names()

    if not indexes:
        print("No cameras detected!")
        return None, None

    print("\nAvailable Cameras:")
    for idx in indexes:
        if names and idx < len(names):
            print(f"{idx}: {names[idx]}")
        else:
            print(f"{idx}: Camera {idx}")

    cam_index = int(input("\nEnter camera index: "))

    if cam_index not in indexes:
        print("Invalid selection. Using default camera 0.")
        cam_index = 0

    cap = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW)
    cam_name = names[cam_index] if names and cam_index < len(names) else f"Camera {cam_index}"

    return cap, cam_name
