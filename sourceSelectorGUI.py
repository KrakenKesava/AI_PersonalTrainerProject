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
selected_exercise = None

SUPPORTED_VIDEO_FORMATS = ["mp4", "avi", "mov", "mkv"]
SUPPORTED_IMAGE_FORMATS = ["jpg", "jpeg", "png", "bmp", "webp"]

ALL_FORMATS = SUPPORTED_VIDEO_FORMATS + SUPPORTED_IMAGE_FORMATS
FORMAT_TEXT = " | ".join(ALL_FORMATS).upper()


class SourceSelector(TkinterDnD.Tk):

    def __init__(self):
        super().__init__()

        self.title("AI Trainer - Input Source")
        self.geometry("1280x720")
        self.resizable(False, False)

        self.configure(bg="#0f172a")

        self.build_ui()

    # =========================
    # UI BUILD
    # =========================
    def build_ui(self):

        # HEADER
        header = ctk.CTkFrame(self, height=80)
        header.pack(fill="x")

        ctk.CTkLabel(
            header,
            text="🤖 AI Fitness Trainer",
            font=ctk.CTkFont(size=26, weight="bold")
        ).pack(pady=(20, 5))

        ctk.CTkLabel(
            header,
            text="Select your input source to begin analysis",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        ).pack()

        # =========================
        # EXERCISE SELECTION
        # =========================
        exercise_frame = ctk.CTkFrame(self)
        exercise_frame.pack(fill="x", padx=20, pady=(10, 0))

        ctk.CTkLabel(
            exercise_frame,
            text="🏋 Select Exercise",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left", padx=10)

        self.exercise_var = ctk.StringVar(value="pullup")

        self.exercise_menu = ctk.CTkOptionMenu(
            exercise_frame,
            values=["pullup"],
            # values=["pullup", "pushup", "squat"],
            variable=self.exercise_var,
            width=150
        )
        self.exercise_menu.pack(side="left", padx=10)

        # =========================
        # MAIN LAYOUT
        # =========================
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        left_frame = ctk.CTkFrame(main_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=10)

        right_frame = ctk.CTkFrame(main_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=10)

        # =========================
        # LEFT → CAMERAS
        # =========================
        ctk.CTkLabel(
            left_frame,
            text="📷 Available Cameras",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=15)

        self.camera_frame = ctk.CTkScrollableFrame(left_frame)
        self.camera_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.load_cameras()

        # =========================
        # RIGHT → FILE INPUT
        # =========================
        ctk.CTkLabel(
            right_frame,
            text="📁 Upload Media",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=15)

        ctk.CTkButton(
            right_frame,
            text="Select Video / Image",
            height=45,
            corner_radius=12,
            command=self.choose_file
        ).pack(pady=10)

        ctk.CTkLabel(
            right_frame,
            text=f"Formats: {FORMAT_TEXT}",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(pady=5)

        # Drag & Drop
        self.drop_area = ctk.CTkFrame(
            right_frame,
            height=200,
            corner_radius=15,
            fg_color="#111827"
        )
        self.drop_area.pack(padx=20, pady=20, fill="x")

        ctk.CTkLabel(
            self.drop_area,
            text="⬇ Drag & Drop File Here",
            font=ctk.CTkFont(size=15)
        ).pack(expand=True)

        self.drop_area.drop_target_register(DND_FILES)
        self.drop_area.dnd_bind("<<Drop>>", self.drop_file)

        # FOOTER
        footer = ctk.CTkFrame(self, height=60)
        footer.pack(fill="x")

        ctk.CTkButton(
            footer,
            text="Exit",
            fg_color="#dc2626",
            hover_color="#ef4444",
            corner_radius=10,
            width=120,
            command=self.destroy
        ).pack(pady=10)

    # =========================
    # LOAD CAMERAS
    # =========================
    def load_cameras(self):

        indexes = cameraModule.list_cameras()
        names = cameraModule.get_camera_names()

        if not indexes:
            ctk.CTkLabel(
                self.camera_frame,
                text="No Cameras Detected",
                text_color="red"
            ).pack(pady=10)
            return

        for idx in indexes:
            cam_name = cameraModule.get_camera_name(idx, names)

            ctk.CTkButton(
                self.camera_frame,
                text=f"📷 {idx} • {cam_name}",
                height=40,
                corner_radius=10,
                command=lambda i=idx, n=cam_name: self.start_camera(i, n)
            ).pack(pady=5, padx=10, fill="x")

    # =========================
    # START CAMERA
    # =========================
    def start_camera(self, index, name):
        global selected_cap, selected_name, selected_exercise

        cap = cameraModule.open_camera(index)

        if cap is None:
            messagebox.showerror("Error", "Unable to open camera.")
            return

        selected_cap = cap
        selected_name = name
        selected_exercise = self.exercise_var.get()

        self.destroy()

    # =========================
    # FILE SELECT
    # =========================
    def choose_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[(
                "Media Files",
                "*.mp4 *.avi *.mov *.mkv *.jpg *.jpeg *.png *.bmp *.webp"
            )]
        )

        if not file_path:
            return

        self.process_file(file_path)

    # =========================
    # DRAG & DROP
    # =========================
    def drop_file(self, event):
        file_path = event.data.strip("{}")
        self.process_file(file_path)

    # =========================
    # FILE PROCESSING
    # =========================
    def process_file(self, file_path):
        global selected_cap, selected_name, selected_exercise

        ext = file_path.split(".")[-1].lower()

        # IMAGE
        if ext in SUPPORTED_IMAGE_FORMATS:
            img = cv2.imread(file_path)

            if img is None:
                messagebox.showerror("Error", "Unable to open image.")
                return

            selected_cap = img
            selected_name = os.path.basename(file_path)
            selected_exercise = self.exercise_var.get()
            self.destroy()
            return

        # VIDEO
        cap = cv2.VideoCapture(file_path)

        if not cap.isOpened():
            messagebox.showerror("Error", "Unable to open file.")
            return

        selected_cap = cap
        selected_name = os.path.basename(file_path)
        selected_exercise = self.exercise_var.get()
        self.destroy()


# =========================
# LAUNCH FUNCTION
# =========================
def launch_gui():
    global selected_cap, selected_name, selected_exercise

    selected_cap = None
    selected_name = None
    selected_exercise = None

    app = SourceSelector()
    app.mainloop()

    return selected_cap, selected_name, selected_exercise