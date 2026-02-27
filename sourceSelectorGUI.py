import os
import json
import time
import cv2
import threading
import numpy as np
import customtkinter as ctk
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime
from PIL import Image, ImageTk
from tkinter import filedialog, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES

import cameraModule
import PoseModule as pm
import RepCounterModule as rep

# Futuristic Color Palette
BG_COLOR = "#020617"
ACCENT_COLOR = "#22d3ee"
SECONDARY_ACCENT = "#818cf8"
SIDEBAR_COLOR = "#0f172a"
CARD_BG = "#1e293b"
TEXT_COLOR = "#f8fafc"

SUPPORTED_VIDEO_FORMATS = ["mp4", "avi", "mov", "mkv"]
SUPPORTED_IMAGE_FORMATS = ["jpg", "jpeg", "png", "bmp", "webp"]

ALL_FORMATS = SUPPORTED_VIDEO_FORMATS + SUPPORTED_IMAGE_FORMATS
FORMAT_TEXT = " | ".join(ALL_FORMATS).upper()


class MainApp(TkinterDnD.Tk):

    def __init__(self):
        super().__init__()

        self.title("AI Fitness Trainer Pro")
        self.geometry("1400x850")
        self.configure(bg=BG_COLOR)

        # Application State
        self.selected_exercise = "pullup"  # Default
        self.selected_source = None
        self.selected_name = ""
        self.is_running = False
        self.session_data = [] # New: Store all rep data

        # CV Components
        self.detector = pm.poseDetector()
        self.reps = rep.RepCounter()
        self.analyser = None
        self.angle_points = (11, 13, 15)
        self.last_feedback = "Start your workout"
        self.pTime = 0.0
        self.update_job = None

        # AI State
        load_dotenv()
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = None
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-flash-latest')
        
        self.build_layout()
        self.show_exercise_selection()

    def build_layout(self):
        # MAIN CONTAINER
        self.main_container = ctk.CTkFrame(self, fg_color=BG_COLOR, corner_radius=0)
        self.main_container.pack(fill="both", expand=True)

        # SIDEBAR
        self.sidebar = ctk.CTkFrame(self.main_container, width=280, corner_radius=0, fg_color=SIDEBAR_COLOR, border_width=2, border_color="#1e293b")
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Sidebar Title with Glow Effect
        title_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        title_frame.pack(pady=(40, 40), padx=20, fill="x")

        ctk.CTkLabel(
            title_frame,
            text="AI TRAINER PRO",
            font=ctk.CTkFont(size=24, weight="bold", family="Orbitron"),
            text_color=ACCENT_COLOR
        ).pack()
        
        # Decorative line
        ctk.CTkFrame(title_frame, height=2, fg_color=ACCENT_COLOR, width=150).pack(pady=5)

        # Sidebar Buttons
        self.btn_trainer = self.create_sidebar_button("🏋 WORKOUT HUB", self.show_exercise_selection, active=True)
        self.btn_questions = self.create_sidebar_button("❓ AI ASSISTANT", self.show_chat_interface)

        # Sidebar Footer
        footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        footer.pack(side="bottom", fill="x", pady=30)
        
        ctk.CTkButton(
            footer,
            text="TERMINATE SESSION",
            fg_color="#ef4444",
            hover_color="#991b1b",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=40,
            command=self.quit
        ).pack(padx=20, fill="x")

        # CONTENT AREA
        self.content_area = ctk.CTkFrame(self.main_container, fg_color=BG_COLOR, corner_radius=0)
        self.content_area.pack(side="right", fill="both", expand=True, padx=40, pady=40)

    def create_sidebar_button(self, text, command, active=False):
        btn = ctk.CTkButton(
            self.sidebar,
            text=text,
            command=command,
            anchor="w",
            height=55,
            fg_color=ACCENT_COLOR if active else "transparent",
            text_color="white" if active else "#94a3b8",
            hover_color="#1e293b",
            font=ctk.CTkFont(size=14, weight="bold" if active else "normal"),
            corner_radius=10,
            border_width=1 if active else 0,
            border_color=ACCENT_COLOR if active else SIDEBAR_COLOR
        )
        btn.pack(fill="x", padx=20, pady=8)
        return btn

    def clear_content(self):
        for widget in self.content_area.winfo_children():
            widget.destroy()

    # ==========================================
    # STEP 1: EXERCISE SELECTION
    # ==========================================
    def show_exercise_selection(self):
        self.clear_content()
        self.selected_exercise = "pullup" # Reset to default string
        
        header_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 40))

        ctk.CTkLabel(
            header_frame,
            text="Step 1: Select Your Exercise",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color="white"
        ).pack(anchor="w")

        # Grid for Exercises
        grid_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True)
        grid_frame.grid_columnconfigure((0, 1), weight=1, pad=20)
        grid_frame.grid_rowconfigure((0, 1), weight=1, pad=20)

        exercises = [
            ("Pushups", "Place hands shoulder-width apart...", "exerciseVideos/Pushups/pushup.png"),
            ("Pullups", "Grab the bar and pull yourself up...", "exerciseVideos/Pullups/pullup.png"),
            ("Squads", "Lower your hips from a standing position...", "exerciseVideos/Squads/Squads.png"),
            ("Situps", "Lie on your back with knees bent...", None) # Placeholder if no image
        ]

        for i, (name, desc, img_path) in enumerate(exercises):
            row, col = divmod(i, 2)
            self.create_exercise_card(grid_frame, name, desc, img_path, row, col)

    def create_exercise_card(self, parent, name, desc, img_path, row, col):
        # Base container for card with a neon border effect
        card_container = ctk.CTkFrame(parent, fg_color="transparent")
        card_container.grid(row=row, column=col, sticky="nsew", padx=20, pady=20)
        
        card = ctk.CTkFrame(
            card_container, 
            fg_color=CARD_BG, 
            corner_radius=20, 
            cursor="hand2",
            border_width=1,
            border_color="#334155"
        )
        card.pack(fill="both", expand=True)
        
        # Load Image if exists
        logo_label = None
        if img_path and os.path.exists(img_path):
            try:
                img = Image.open(img_path)
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(120, 120))
                logo_label = ctk.CTkLabel(card, image=ctk_img, text="")
                logo_label.pack(pady=(20, 10))
            except Exception as e:
                print(f"Error loading logo {img_path}: {e}")
        
        if not logo_label:
            ctk.CTkLabel(card, text="🏋️", font=ctk.CTkFont(size=60)).pack(pady=(20, 10))

        ctk.CTkLabel(
            card,
            text=name.upper(),
            font=ctk.CTkFont(size=22, weight="bold", family="Orbitron"),
            text_color=ACCENT_COLOR
        ).pack(pady=(10, 5))

        ctk.CTkLabel(
            card,
            text=desc,
            font=ctk.CTkFont(size=14),
            text_color="#94a3b8",
            wraplength=280
        ).pack(pady=10, padx=20)

        # Interaction effects
        def on_enter(e):
            card.configure(border_color=ACCENT_COLOR, border_width=2)
            card.configure(fg_color="#1e293b") # Slightly lighter
            
        def on_leave(e):
            card.configure(border_color="#334155", border_width=1)
            card.configure(fg_color=CARD_BG)

        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)
        card.bind("<Button-1>", lambda e, n=name.lower(): self.show_source_selection(n))
        
        # Ensure children also trigger the click
        for child in card.winfo_children():
            child.bind("<Enter>", on_enter)
            child.bind("<Leave>", on_leave)
            child.bind("<Button-1>", lambda e, n=name.lower(): self.show_source_selection(n))

    # ==========================================
    # CHAT INTERFACE: ASK QUESTIONS
    # ==========================================
    def show_chat_interface(self):
        self.clear_content()
        self.is_running = False # Stop workout if running
        
        # Update Sidebar Highlighting
        self.btn_trainer.configure(fg_color="transparent", text_color="#94a3b8", border_width=0)
        self.btn_questions.configure(fg_color=ACCENT_COLOR, text_color="white", border_width=1, border_color=ACCENT_COLOR)

        header_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            header_frame,
            text="AI ASSISTANT",
            font=ctk.CTkFont(size=32, weight="bold", family="Orbitron"),
            text_color=ACCENT_COLOR
        ).pack(anchor="w")

        # Chat Container
        self.chat_container = ctk.CTkFrame(self.content_area, fg_color=SIDEBAR_COLOR, corner_radius=20, border_width=1, border_color="#334155")
        self.chat_container.pack(fill="both", expand=True)

        # Chat History
        self.chat_history = ctk.CTkScrollableFrame(self.chat_container, fg_color="transparent")
        self.chat_history.pack(fill="both", expand=True, padx=20, pady=20)

        # Input Area
        input_frame = ctk.CTkFrame(self.chat_container, fg_color=BG_COLOR, height=80, corner_radius=15)
        input_frame.pack(fill="x", side="bottom", padx=10, pady=10)

        self.msg_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Enter command or question...",
            height=50,
            fg_color=SIDEBAR_COLOR,
            border_width=1,
            border_color="#334155",
            font=ctk.CTkFont(size=14)
        )
        self.msg_entry.pack(side="left", fill="x", expand=True, padx=(15, 10), pady=10)
        self.msg_entry.bind("<Return>", lambda e: self.send_chat_message())

        ctk.CTkButton(
            input_frame,
            text="SEND",
            width=100,
            height=50,
            command=self.send_chat_message,
            fg_color=ACCENT_COLOR,
            text_color="black",
            hover_color=SECONDARY_ACCENT,
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="right", padx=(10, 15), pady=10)

        # Initial Welcome Message
        self.add_chat_bubble("AI Trainer", "Hello! I'm your AI Personal Trainer. How can I help you today?", is_user=False)

    def get_session_summary(self):
        """Aggregate session data for context injection."""
        session_dir = "sessions"
        if not os.path.exists(session_dir):
            return "No previous session data found."
        
        files = [f for f in os.listdir(session_dir) if f.endswith(".json")]
        if not files:
            return "No previous sessions recorded."
        
        files.sort(reverse=True)
        summary = "User's Recent Workout History (Context for AI):\n"
        
        for f in files[:3]: # Take last 3 sessions
            try:
                with open(os.path.join(session_dir, f), 'r') as file:
                    data = json.load(file)
                    reps = data.get('reps', [])
                    total_reps = len(reps)
                    failed_reps = [r for r in reps if not r.get('success', True)]
                    
                    # Collect unique feedback from failed reps
                    all_feedback = []
                    for r in failed_reps:
                        all_feedback.extend(r.get('feedback', []))
                    unique_feedback = list(set(all_feedback))
                    
                    summary += f"- {data.get('date')}: {data.get('exercise')} ({total_reps} total)."
                    if failed_reps:
                        summary += f" ISSUES: {', '.join(unique_feedback)}. "
                        summary += f"Success rate: {int((total_reps - len(failed_reps))/total_reps * 100)}%.\n"
                    else:
                        summary += " Perfect form achieved!\n"
            except:
                continue
        return summary

    def send_chat_message(self):
        msg = self.msg_entry.get().strip()
        if not msg:
            return

        self.msg_entry.delete(0, 'end')
        self.add_chat_bubble("You", msg, is_user=True)

        # Show typing indicator
        self.typing_bubble = self.add_chat_bubble("AI Trainer", "...", is_user=False)
        
        # Call AI in separate thread to avoid freezing GUI
        import threading
        threading.Thread(target=self.generate_ai_response, args=(msg,), daemon=True).start()

    def generate_ai_response(self, user_msg):
        if not self.model:
            response = "I don't have an API key! Please add GEMINI_API_KEY to your .env file to enable smart chat."
        else:
            try:
                context = self.get_session_summary()
                system_prompt = f"""
                You are a professional AI Personal Trainer Pro. 
                Your goal is to provide technical, motivational, and safe advice about gym exercises.
                
                CURRENT USER DATA:
                {context}
                
                Rules:
                1. If asked about form, be detailed (Pushups, Pullups, Squats).
                2. If the user mentions their history or "how did I do?", use the context provided above.
                3. Be motivational but focus on safety. Use terms like "Range of Motion", "Tempo", and "Lockout".
                4. If the user had "Pull higher" issues, explain that they aren't getting their chin above the bar.
                5. If they had "Extend fully" issues, explain they aren't dropping low enough to the dead-hang position.
                6. Keep responses futuristic, helpful, and concise (under 100 words).
                """
                
                full_prompt = f"{system_prompt}\n\nUser Question: {user_msg}"
                ai_res = self.model.generate_content(full_prompt)
                response = ai_res.text
            except Exception as e:
                response = f"Sorry, I encountered an error: {str(e)}"

        # Remove typing indicator and add real response
        self.after(0, lambda: self.finalize_chat(response))

    def finalize_chat(self, response):
        if hasattr(self, 'typing_bubble'):
            self.typing_bubble.destroy()
        self.add_chat_bubble("AI Trainer", response, is_user=False)

    def add_chat_bubble(self, sender, text, is_user=True):
        bubble_frame = ctk.CTkFrame(self.chat_history, fg_color="transparent")
        bubble_frame.pack(fill="x", pady=10)

        align = "right" if is_user else "left"
        bg_color = "#1e293b" if is_user else "transparent"
        border_color = ACCENT_COLOR if is_user else SECONDARY_ACCENT
        txt_color = TEXT_COLOR
        
        # Container for the bulb and text
        inner_bubble = ctk.CTkFrame(
            bubble_frame, 
            fg_color=bg_color, 
            corner_radius=15,
            border_width=1,
            border_color=border_color
        )
        inner_bubble.pack(side=align, padx=10)

        ctk.CTkLabel(
            inner_bubble,
            text=f"[{sender}]",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#cbd5e1"
        ).pack(anchor="w", padx=15, pady=(8, 2))

        ctk.CTkLabel(
            inner_bubble,
            text=text,
            font=ctk.CTkFont(size=14),
            text_color=txt_color,
            wraplength=400,
            justify="left"
        ).pack(anchor="w", padx=15, pady=(0, 10))

        # Scroll to bottom
        self.chat_history._parent_canvas.yview_moveto(1.0)
        return bubble_frame

    # ==========================================
    # STEP 2: SOURCE SELECTION
    # ==========================================
    def show_source_selection(self, exercise):
        self.selected_exercise = exercise
        self.clear_content()

        header_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        ctk.CTkButton(
            header_frame, 
            text="← BACK", 
            width=100, 
            command=self.show_exercise_selection,
            fg_color="transparent",
            hover_color=SIDEBAR_COLOR,
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left")

        ctk.CTkLabel(
            header_frame,
            text=f"SOURCE SELECTION",
            font=ctk.CTkFont(size=28, weight="bold", family="Orbitron"),
            text_color=ACCENT_COLOR,
            padx=20
        ).pack(side="left")

        split_container = ctk.CTkFrame(self.content_area, fg_color="transparent")
        split_container.pack(fill="both", expand=True, pady=20)

        # LEFT - CAMERAS
        left_side = ctk.CTkFrame(split_container, fg_color=SIDEBAR_COLOR, corner_radius=15, border_width=1, border_color="#334155")
        left_side.pack(side="left", fill="both", expand=True, padx=(0, 10))

        ctk.CTkLabel(left_side, text="AVAILABLE CAMERAS", font=ctk.CTkFont(size=18, weight="bold", family="Orbitron"), text_color=SECONDARY_ACCENT).pack(pady=20)
        
        cam_scroll = ctk.CTkScrollableFrame(left_side, fg_color="transparent")
        cam_scroll.pack(fill="both", expand=True, padx=15, pady=15)

        indexes = cameraModule.list_cameras()
        names = cameraModule.get_camera_names()

        if not indexes:
            ctk.CTkLabel(cam_scroll, text="No Cameras Found", text_color="#ef4444").pack(pady=20)
        else:
            for idx in indexes:
                cam_name = cameraModule.get_camera_name(idx, names)
                ctk.CTkButton(
                    cam_scroll,
                    text=f"CAM-{idx}: {cam_name}",
                    command=lambda i=idx, n=cam_name: self.start_workout(cameraModule.open_camera(i), n),
                    height=55,
                    corner_radius=10,
                    fg_color="#1e293b",
                    hover_color=ACCENT_COLOR,
                    text_color="white",
                    font=ctk.CTkFont(size=13, weight="bold")
                ).pack(fill="x", pady=8)

        # RIGHT - FILE UPLOAD
        right_side = ctk.CTkFrame(split_container, fg_color=SIDEBAR_COLOR, corner_radius=15, border_width=1, border_color="#334155")
        right_side.pack(side="right", fill="both", expand=True, padx=(10, 0))

        ctk.CTkLabel(right_side, text="UPLOAD MEDIA", font=ctk.CTkFont(size=18, weight="bold", family="Orbitron"), text_color=SECONDARY_ACCENT).pack(pady=20)

        ctk.CTkButton(
            right_side,
            text="BROWSE FILES",
            command=self.choose_file_and_start,
            height=55,
            fg_color=ACCENT_COLOR,
            text_color="black",
            hover_color=SECONDARY_ACCENT,
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=20, padx=30, fill="x")

        # Drag & Drop Area
        self.drop_area = ctk.CTkFrame(right_side, height=200, fg_color=BG_COLOR, corner_radius=15, border_width=2, border_color="#334155")
        self.drop_area.pack(fill="x", padx=30, pady=20)
        
        ctk.CTkLabel(self.drop_area, text="DROP MEDIA HERE", font=ctk.CTkFont(size=14, weight="bold"), text_color="#64748b").pack(expand=True)
        self.drop_area.drop_target_register(DND_FILES)
        self.drop_area.dnd_bind("<<Drop>>", self.drop_file_and_start)

    def choose_file_and_start(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Media Files", "*.mp4 *.avi *.mov *.mkv *.jpg *.jpeg *.png")]
        )
        if file_path:
            self.process_selected_file(file_path)

    def drop_file_and_start(self, event):
        file_path = event.data.strip("{}")
        self.process_selected_file(file_path)

    def process_selected_file(self, path):
        ext = path.split(".")[-1].lower()
        if ext in ["jpg", "jpeg", "png", "bmp"]:
            img = cv2.imread(path)
            if img is not None:
                self.start_workout(img, os.path.basename(path))
        else:
            cap = cv2.VideoCapture(path)
            if cap.isOpened():
                self.start_workout(cap, os.path.basename(path))

    # ==========================================
    # STEP 3: WORKOUT SESSION
    # ==========================================
    def start_workout(self, source, name):
        self.selected_source = source
        self.selected_name = name
        self.session_data = [] # Reset for new session
        self.reps = rep.RepCounter() # Reset rep counter for new session
        self.clear_content()

        # Init Exercise Analyser
        if self.selected_exercise == "pullups":
            from exercises.pullup import PullupAnalyser
            self.analyser = PullupAnalyser()
            self.angle_points = (11, 13, 15) # Shoulder, Elbow, Wrist
            self.reps.set_thresholds(100, 115) # Universal attempt detection for Pullups
        elif self.selected_exercise == "pushups":
            from exercises.pushup import PushupAnalyser
            self.analyser = PushupAnalyser()
            self.angle_points = (11, 13, 15) # Same as pullup essentially
            self.reps.set_thresholds(110, 140) # Lenient: Capture partial pushups
        elif self.selected_exercise == "squats":
            from exercises.squat import SquatAnalyser
            self.analyser = SquatAnalyser()
            self.angle_points = (23, 25, 27) # Hip, Knee, Ankle
            self.reps.set_thresholds(115, 145) # Lenient: Capture shallow squats
        else:
            self.analyser = None
            self.angle_points = (11, 13, 15) # Default
            self.reps.set_thresholds(60, 150) # Standard default

        # UI for Step 3
        header = ctk.CTkFrame(self.content_area, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))

        ctk.CTkButton(
            header, 
            text="← ABORT SESSION", 
            width=150, 
            command=self.stop_workout_and_back,
            fg_color="transparent",
            hover_color="#ef4444",
            border_width=1,
            border_color="#ef4444",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left")
        
        ctk.CTkLabel(
            header, 
            text=f"ACTIVE SESSION: {self.selected_exercise.upper()}", 
            font=ctk.CTkFont(size=24, weight="bold", family="Orbitron"), 
            text_color=ACCENT_COLOR,
            padx=20
        ).pack(side="left")

        # Layout for video and stats
        main_workout_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        main_workout_frame.pack(fill="both", expand=True)

        # Video Canvas with Neon border
        video_container = ctk.CTkFrame(main_workout_frame, fg_color=BG_COLOR, border_width=2, border_color=ACCENT_COLOR, corner_radius=10)
        video_container.pack(side="left", fill="both", expand=True, padx=(0, 20))

        self.video_label = ctk.CTkLabel(video_container, text="INITIALIZING SYSTEM...")
        self.video_label.pack(fill="both", expand=True, padx=2, pady=2)

        # Stats Panel (HUD Style)
        stats_panel = ctk.CTkFrame(main_workout_frame, width=320, fg_color=SIDEBAR_COLOR, corner_radius=15, border_width=1, border_color="#334155")
        stats_panel.pack(side="right", fill="y")
        stats_panel.pack_propagate(False)

        ctk.CTkLabel(stats_panel, text="HUD - TELEMETRY", font=ctk.CTkFont(size=18, weight="bold", family="Orbitron"), text_color=SECONDARY_ACCENT).pack(pady=20)
        
        # Rep Counter Card
        rep_card = ctk.CTkFrame(stats_panel, fg_color=BG_COLOR, corner_radius=10, border_width=1, border_color=ACCENT_COLOR)
        rep_card.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(rep_card, text="TOTAL REPS", font=ctk.CTkFont(size=12, weight="bold"), text_color="#64748b").pack(pady=(10, 0))
        self.rep_label = ctk.CTkLabel(rep_card, text="0", font=ctk.CTkFont(size=48, weight="bold", family="Orbitron"), text_color=ACCENT_COLOR)
        self.rep_label.pack(pady=(0, 10))

        # Feedback Card
        feedback_card = ctk.CTkFrame(stats_panel, fg_color=BG_COLOR, corner_radius=10, border_width=1, border_color=SECONDARY_ACCENT)
        feedback_card.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(feedback_card, text="LIVE ANALYSIS", font=ctk.CTkFont(size=12, weight="bold"), text_color="#64748b").pack(pady=(10, 0))
        self.feedback_label = ctk.CTkLabel(feedback_card, text="WAITING FOR POSE...", font=ctk.CTkFont(size=14, weight="bold"), wraplength=250, text_color="yellow")
        self.feedback_label.pack(pady=(0, 15), padx=20)

        # History Section
        ctk.CTkLabel(stats_panel, text="SESSION LOGS", font=ctk.CTkFont(size=14, weight="bold", family="Orbitron"), text_color="#64748b").pack(pady=(20, 5))
        self.history_scroll = ctk.CTkScrollableFrame(stats_panel, fg_color=BG_COLOR, height=350, corner_radius=10)
        self.history_scroll.pack(fill="both", expand=True, padx=15, pady=10)

        self.is_running = True
        self.update_frame()

    def stop_workout_and_back(self):
        self.is_running = False
        if self.update_job:
            self.after_cancel(self.update_job)
        
        # Save session before exiting
        self.save_session()
        
        if self.selected_source is not None and isinstance(self.selected_source, cv2.VideoCapture):
            self.selected_source.release()
        
        self.show_exercise_selection()

    def update_frame(self):
        if not self.is_running:
            return

        if self.selected_source is not None and isinstance(self.selected_source, np.ndarray):
            # Image mode
            frame = self.selected_source.copy()
            processed_frame = self.process_cv_logic(frame)
            self.display_frame(processed_frame)
            # No update loop for static images
        else:
            # Video/Camera mode
            success, frame = self.selected_source.read() if self.selected_source is not None else (False, None)
            if success:
                processed_frame = self.process_cv_logic(frame)
                self.display_frame(processed_frame)
                self.update_job = self.after(10, self.update_frame)
            else:
                self.stop_workout_and_back()

    def process_cv_logic(self, img):
        img_h, img_w = img.shape[:2]
        
        # Scaling factor and safety margins
        scale = img_w / 1280
        font_scale = max(0.6, 0.8 * scale)
        thickness = max(1, int(2 * scale))
        
        # Use wider margins to prevent clipping in GUI
        margin_x = int(img_w * 0.10)
        margin_y = int(img_h * 0.15)
        
        # FPS Calculation
        cTime = time.time()
        fps = 1 / (cTime - self.pTime) if self.pTime != 0 else 0
        self.pTime = cTime

        # 1. FPS Overlay (Top Left)
        cv2.putText(img, f"FPS: {int(fps)}", (margin_x, margin_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 255, 0), thickness)

        img = self.detector.findPose(img)
        lmList = self.detector.findPosition(img, False)

        reps_count = self.reps.rep_count
        percentage = 0

        if len(lmList) != 0:
            angle = self.detector.findAngle(img, self.angle_points[0], self.angle_points[1], self.angle_points[2], True)
            
            if self.analyser:
                self.analyser.update(angle)

            # 2. Progress Percentage Calculation
            percentage = np.interp(angle, (50, 160), (100, 0))
            percentage = np.clip(percentage, 0, 100)

            reps_count, rep_done = self.reps.update(angle)
            self.rep_label.configure(text=f"Reps: {reps_count}")

            if rep_done and self.analyser:
                result = self.analyser.analyse_rep()
                
                rep_entry = {
                    "rep_num": reps_count,
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "rom": result.get("rom", 0),
                    "tempo": result.get("repTime", 0),
                    "feedback": result.get("feedback", []),
                    "success": result.get("formCorrect", False)
                }
                self.session_data.append(rep_entry)
                self.add_history_item(rep_entry)

                self.last_feedback = " | ".join(result["feedback"])
                print(f"--- REP {reps_count} FEEDBACK: {self.last_feedback} ---") # Added terminal print
                self.feedback_label.configure(text=self.last_feedback.replace(" | ", "\n"))
            elif not rep_done:
                if hasattr(self.analyser, "get_live_feedback"):
                    self.last_feedback = self.analyser.get_live_feedback(angle)
                else:
                    self.last_feedback = "Analyzing..."
                self.feedback_label.configure(text=self.last_feedback)

        # 3. Reps & Tempo Overlay
        cv2.putText(img, f"Reps: {int(reps_count)}", (margin_x, margin_y + int(60 * scale)), cv2.FONT_HERSHEY_SIMPLEX, 1.2 * scale, (255, 0, 0), int(3 * scale))
        
        # Show last rep tempo if exists
        last_tempo = self.session_data[-1]["tempo"] if self.session_data else 0
        cv2.putText(img, f"Tempo: {last_tempo}s", (margin_x, margin_y + int(110 * scale)), cv2.FONT_HERSHEY_SIMPLEX, 0.8 * scale, (255, 255, 0), int(2 * scale))

        # 4. Progress Bar Overlay
        bar_x1, bar_y1 = margin_x, margin_y + int(160 * scale)
        bar_height = int(300 * scale)
        bar_width = int(40 * scale)
        
        cv2.rectangle(img, (bar_x1, bar_y1), (bar_x1 + bar_width, bar_y1 + bar_height), (0, 255, 0), thickness)
        filled_h = int(np.interp(percentage, (0, 100), (0, bar_height)))
        cv2.rectangle(img, (bar_x1, bar_y1 + bar_height - filled_h), (bar_x1 + bar_width, bar_y1 + bar_height), (0, 255, 0), cv2.FILLED)
        cv2.putText(img, f"{int(percentage)}%", (bar_x1, bar_y1 - int(15 * scale)), cv2.FONT_HERSHEY_SIMPLEX, 0.8 * scale, (255, 255, 255), thickness)

        # 5. Live Feedback Overlay (Bottom Left)
        feedback_lines = self.last_feedback.split("|")
        y_offset = img_h - int(120 * scale)
        for i, line in enumerate(feedback_lines):
            line = line.strip()
            (text_w, text_h), _ = cv2.getTextSize(line, cv2.FONT_HERSHEY_SIMPLEX, 0.7 * scale, thickness)
            cv2.rectangle(img, (margin_x - 10, y_offset - text_h - 10 + i * int(45 * scale)), (margin_x + text_w + 10, y_offset + 10 + i * int(45 * scale)), (20, 20, 20), cv2.FILLED)
            cv2.putText(img, line, (margin_x, y_offset + i * int(45 * scale)), cv2.FONT_HERSHEY_SIMPLEX, 0.7 * scale, (255, 255, 0), thickness)

        return img

    def add_history_item(self, rep_data):
        success_color = "#10b981" if rep_data["success"] else "#ef4444"
        
        item = ctk.CTkFrame(self.history_scroll, fg_color=SIDEBAR_COLOR, height=45, corner_radius=8, border_width=1, border_color="#334155")
        item.pack(fill="x", pady=4, padx=5)
        
        ctk.CTkLabel(
            item, 
            text=f"REP {rep_data['rep_num']}", 
            font=ctk.CTkFont(size=12, weight="bold", family="Orbitron"),
            text_color=ACCENT_COLOR
        ).pack(side="left", padx=15)
        
        ctk.CTkLabel(
            item, 
            text=f"{rep_data['tempo']}s", 
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=success_color
        ).pack(side="right", padx=15)

    def save_session(self):
        if not self.session_data:
            print("Session not saved: No reps completed.")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sessions/session_{self.selected_exercise}_{timestamp}.json"
        
        summary = {
            "exercise": self.selected_exercise,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_reps": len(self.session_data),
            "reps": self.session_data
        }

        try:
            if not os.path.exists("sessions"):
                os.makedirs("sessions")
            with open(filename, 'w') as f:
                json.dump(summary, f, indent=4)
            print(f"Session saved to {filename}")
        except Exception as e:
            print(f"Error saving session: {e}")

    def display_frame(self, frame):
        # Resize for GUI while maintaining aspect ratio
        h, w = frame.shape[:2]
        target_h = 600
        aspect = w / h
        target_w = int(target_h * aspect)
        
        frame_resized = cv2.resize(frame, (target_w, target_h))
        frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
        
        img_pil = Image.fromarray(frame_rgb)
        img_tk = ImageTk.PhotoImage(image=img_pil)
        
        self.video_label.configure(image=img_tk)
        self.video_label.image = img_tk

def launch_gui():
    app = MainApp()
    app.mainloop()

