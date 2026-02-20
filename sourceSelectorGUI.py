# sourceSelectorGUI.py

import customtkinter as ctk
from tkinter import filedialog, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES
import cv2
import cameraModule
import os

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

selected_cap = None
selected_name = None

SUPPORTED_VIDEO_FORMATS = ["mp4", "avi", "mov", "mkv"]
SUPPORTED_IMAGE_FORMATS = ["jpg", "jpeg", "png", "bmp", "webp"]

ALL_FORMATS = SUPPORTED_VIDEO_FORMATS + SUPPORTED_IMAGE_FORMATS
FORMAT_TEXT = " | ".join(ALL_FORMATS).upper()


class SourceSelector(TkinterDnD.Tk):

    def __init__(self):
        super().__init__()

        self.title("AI Camera Launcher")
        self.geometry("500x520")
        self.resizable(False, False)

        self.configure(bg="#1a1a1a")

        self.build_ui()

    def build_ui(self):

        title = ctk.CTkLabel(
            self,
            text="🎥 Select Input Source",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title.pack(pady=20)

        subtitle = ctk.CTkLabel(
            self,
            text="Choose a camera or video file to begin",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        subtitle.pack(pady=5)

        self.camera_frame = ctk.CTkFrame(self, corner_radius=15)
        self.camera_frame.pack(pady=20, padx=20, fill="both")

        self.load_cameras()
        video_btn = ctk.CTkButton(
            self,
            text="📁 Select Video File",
            height=45,
            corner_radius=12,
            command=self.choose_video
        )
        video_btn.pack(pady=(15, 5))

        format_label = ctk.CTkLabel(
            self,
            text=f"Supported formats: {FORMAT_TEXT}",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        format_label.pack(pady=(0, 10))

        self.drop_area = ctk.CTkFrame(
            self,
            height=100,
            corner_radius=15
        )
        self.drop_area.pack(padx=30, fill="x")

        drop_label = ctk.CTkLabel(
            self.drop_area,
            text="🖱 Drag & Drop Video Here",
            font=ctk.CTkFont(size=14)
        )
        drop_label.pack(expand=True)

        self.drop_area.drop_target_register(DND_FILES)
        self.drop_area.dnd_bind("<<Drop>>", self.drop_video)

        exit_btn = ctk.CTkButton(
            self,
            text="Exit",
            fg_color="#aa2e2e",
            hover_color="#cc3b3b",
            corner_radius=12,
            command=self.destroy
        )
        exit_btn.pack(pady=20)

    def load_cameras(self):

        indexes = cameraModule.list_cameras()
        names = cameraModule.get_camera_names()

        if not indexes:
            no_cam = ctk.CTkLabel(
                self.camera_frame,
                text="No Cameras Detected",
                text_color="red"
            )
            no_cam.pack(pady=10)
            return

        for idx in indexes:
            cam_name = (
                names[idx] if names and idx < len(names)
                else f"Camera {idx}"
            )

            btn = ctk.CTkButton(
                self.camera_frame,
                text=f"{idx} • {cam_name}",
                height=40,
                corner_radius=12,
                command=lambda i=idx, n=cam_name: self.start_camera(i, n)
            )
            btn.pack(pady=6, padx=10, fill="x")

    def start_camera(self, index, name):
        global selected_cap, selected_name

        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)

        if not cap.isOpened():
            messagebox.showerror("Error", "Unable to open camera.")
            return

        selected_cap = cap
        selected_name = name
        self.destroy()

    def choose_video(self):
        global selected_cap, selected_name

        file_path = filedialog.askopenfilename(
            filetypes=[(
                "Media Files",
                "*.mp4 *.avi *.mov *.mkv *.jpg *.jpeg *.png *.bmp *.webp"
            )]
        )

        if not file_path:
            return

        ext = file_path.split(".")[-1].lower()

        # If image → load as static frame
        if ext in SUPPORTED_IMAGE_FORMATS:
            img = cv2.imread(file_path)

            if img is None:
                messagebox.showerror("Error", "Unable to open image.")
                return

            selected_cap = img  # store image directly
            selected_name = os.path.basename(file_path)
            self.destroy()
            return

        # If video → open normally
        cap = cv2.VideoCapture(file_path)

        if not cap.isOpened():
            messagebox.showerror("Error", "Unable to open video.")
            return

        selected_cap = cap
        selected_name = os.path.basename(file_path)
        self.destroy()

    def drop_video(self, event):
        global selected_cap, selected_name

        import os

        file_path = event.data.strip("{}")
        ext = file_path.split(".")[-1].lower()

        if ext in SUPPORTED_IMAGE_FORMATS:
            img = cv2.imread(file_path)

            if img is None:
                messagebox.showerror("Error", "Unable to open image.")
                return

            selected_cap = img
            selected_name = os.path.basename(file_path)
            self.destroy()
            return

        cap = cv2.VideoCapture(file_path)

        if not cap.isOpened():
            messagebox.showerror("Error", "Unable to open file.")
            return

        selected_cap = cap
        selected_name = os.path.basename(file_path)
        self.destroy()

def launch_gui():
    app = SourceSelector()
    app.mainloop()
    return selected_cap, selected_name
