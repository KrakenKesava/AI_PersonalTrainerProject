import cv2

# Try to get camera names (Windows only)
try:
    from pygrabber.dshow_graph import FilterGraph
    WINDOWS_SUPPORT = True
except:
    WINDOWS_SUPPORT = False


# ==============================
# LIST AVAILABLE CAMERAS
# ==============================
def list_cameras(max_tested=5):
    available = []

    for i in range(max_tested):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW if WINDOWS_SUPPORT else 0)

        if cap.isOpened():
            available.append(i)

        cap.release()

    return available


# ==============================
# GET CAMERA NAMES (Windows)
# ==============================
def get_camera_names():
    if WINDOWS_SUPPORT:
        try:
            graph = FilterGraph()
            return graph.get_input_devices()
        except:
            return None
    return None


# ==============================
# OPEN CAMERA SAFELY
# ==============================
def open_camera(index):
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW if WINDOWS_SUPPORT else 0)

    if not cap.isOpened():
        return None

    # 🔥 Warm-up camera (important)
    for _ in range(5):
        cap.read()

    return cap


# ==============================
# GET CAMERA NAME SAFELY
# ==============================
def get_camera_name(index, names):
    if names and index < len(names):
        return names[index]
    return f"Camera {index}"


# ==============================
# CLI CAMERA SELECTOR (Optional)
# ==============================
def choose_camera():
    indexes = list_cameras()
    names = get_camera_names()

    if not indexes:
        print("❌ No cameras detected!")
        return None, None

    print("\n📷 Available Cameras:")
    for idx in indexes:
        cam_name = get_camera_name(idx, names)
        print(f"{idx}: {cam_name}")

    try:
        cam_index = int(input("\nEnter camera index: "))
    except:
        print("Invalid input. Using default camera 0.")
        cam_index = 0

    if cam_index not in indexes:
        print("Invalid selection. Using default camera 0.")
        cam_index = 0

    cap = open_camera(cam_index)

    if cap is None:
        print("❌ Failed to open camera.")
        return None, None

    cam_name = get_camera_name(cam_index, names)

    return cap, cam_name