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

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")



SUPPORTED_VIDEO_FORMATS = ["mp4", "avi", "mov", "mkv"]
SUPPORTED_IMAGE_FORMATS = ["jpg", "jpeg", "png", "bmp", "webp"]

ALL_FORMATS = SUPPORTED_VIDEO_FORMATS + SUPPORTED_IMAGE_FORMATS
FORMAT_TEXT = " | ".join(ALL_FORMATS).upper()


class MainApp(TkinterDnD.Tk):

    def __init__(self):
        super().__init__()

        self.title("AI Fitness Trainer")
        self.geometry("1400x800")
        self.configure(bg="#0f172a")

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
        self.main_container = ctk.CTkFrame(self, fg_color="#0f172a", corner_radius=0)
        self.main_container.pack(fill="both", expand=True)

        # SIDEBAR
        self.sidebar = ctk.CTkFrame(self.main_container, width=280, corner_radius=0, fg_color="#1e293b")
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Sidebar Title
        ctk.CTkLabel(
            self.sidebar,
            text="AI PERSONAL TRAINER",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#38bdf8"
        ).pack(pady=(40, 20), padx=20)

        # Sidebar Buttons
        self.btn_trainer = self.create_sidebar_button("🏋 AI Personal Trainer", self.show_exercise_selection, active=True)
        self.btn_questions = self.create_sidebar_button("❓ Ask Questions", self.show_chat_interface)

        # Sidebar Footer
        footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        footer.pack(side="bottom", fill="x", pady=20)
        
        ctk.CTkButton(
            footer,
            text="Exit Application",
            fg_color="#ef4444",
            hover_color="#dc2626",
            command=self.quit
        ).pack(padx=20, fill="x")

        # CONTENT AREA
        self.content_area = ctk.CTkFrame(self.main_container, fg_color="#0f172a", corner_radius=0)
        self.content_area.pack(side="right", fill="both", expand=True, padx=40, pady=40)

    def create_sidebar_button(self, text, command, active=False):
        btn = ctk.CTkButton(
            self.sidebar,
            text=text,
            command=command,
            anchor="w",
            height=50,
            fg_color="#334155" if active else "transparent",
            hover_color="#334155",
            font=ctk.CTkFont(size=15)
        )
        btn.pack(fill="x", padx=15, pady=5)
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
            ("Pushup", "Place hands shoulder-width apart..."),
            ("Pullup", "Grab the bar and pull yourself up..."),
            ("Situp", "Lie on your back with knees bent..."),
            ("Squat", "Lower your hips from a standing position...")
        ]

        for i, (name, desc) in enumerate(exercises):
            row, col = divmod(i, 2)
            self.create_exercise_card(grid_frame, name, desc, row, col)

    def create_exercise_card(self, parent, name, desc, row, col):
        card = ctk.CTkFrame(parent, fg_color="#1e293b", corner_radius=20, cursor="hand2")
        card.grid(row=row, column=col, sticky="nsew", padx=15, pady=15)
        
        # Make card clickable
        card.bind("<Button-1>", lambda e, n=name.lower(): self.show_source_selection(n))

        ctk.CTkLabel(
            card,
            text=name,
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#38bdf8"
        ).pack(pady=(30, 10))

        ctk.CTkLabel(
            card,
            text=desc,
            font=ctk.CTkFont(size=14),
            text_color="gray",
            wraplength=250
        ).pack(pady=10, padx=20)

    # ==========================================
    # CHAT INTERFACE: ASK QUESTIONS
    # ==========================================
    def show_chat_interface(self):
        self.clear_content()
        self.is_running = False # Stop workout if running
        
        # Update Sidebar Highlighting
        self.btn_trainer.configure(fg_color="transparent")
        self.btn_questions.configure(fg_color="#334155")

        header_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            header_frame,
            text="Ask Your AI Trainer",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color="white"
        ).pack(anchor="w")

        # Chat Container
        self.chat_container = ctk.CTkFrame(self.content_area, fg_color="#1e293b", corner_radius=20)
        self.chat_container.pack(fill="both", expand=True)

        # Chat History
        self.chat_history = ctk.CTkScrollableFrame(self.chat_container, fg_color="transparent")
        self.chat_history.pack(fill="both", expand=True, padx=20, pady=20)

        # Input Area
        input_frame = ctk.CTkFrame(self.chat_container, fg_color="#0f172a", height=80, corner_radius=0)
        input_frame.pack(fill="x", side="bottom")

        self.msg_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Type your question here...",
            height=50,
            fg_color="#1e293b",
            border_width=0,
            font=ctk.CTkFont(size=14)
        )
        self.msg_entry.pack(side="left", fill="x", expand=True, padx=(20, 10), pady=15)
        self.msg_entry.bind("<Return>", lambda e: self.send_chat_message())

        ctk.CTkButton(
            input_frame,
            text="Send",
            width=100,
            height=50,
            command=self.send_chat_message,
            fg_color="#38bdf8",
            hover_color="#0284c7"
        ).pack(side="right", padx=(10, 20), pady=15)

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
        
        # Sort by date (filename has timestamp)
        files.sort(reverse=True)
        summary = "User's Recent Workout History:\n"
        
        for f in files[:3]: # Take last 3 sessions
            try:
                with open(os.path.join(session_dir, f), 'r') as file:
                    data = json.load(file)
                    summary += f"- {data.get('date')}: {data.get('exercise')} session, {data.get('total_reps')} reps.\n"
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
                You are a professional AI Personal Trainer. 
                Your goal is to provide technical, motivational, and safe advice about gym exercises.
                
                {context}
                
                Rules:
                1. If asked about form, be detailed (Pushups, Pullups, Squats, Situps).
                2. If the user mentions their history, use the context provided.
                3. Be motivational but focus on safety.
                4. Keep responses concise (under 100 words).
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
        bg_color = "#38bdf8" if is_user else "#334155"
        text_color = "white"
        
        # Container for the bulb and text
        inner_bubble = ctk.CTkFrame(bubble_frame, fg_color=bg_color, corner_radius=15)
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
            text_color=text_color,
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
            text="← Back",
            width=80,
            command=self.show_exercise_selection,
            fg_color="transparent",
            hover_color="#1e293b"
        ).pack(side="left")

        ctk.CTkLabel(
            header_frame,
            text=f"Step 2: Source Selection for {exercise.capitalize()}",
            font=ctk.CTkFont(size=28, weight="bold"),
            padx=20
        ).pack(side="left")

        split_container = ctk.CTkFrame(self.content_area, fg_color="transparent")
        split_container.pack(fill="both", expand=True, pady=20)

        # LEFT - CAMERAS
        left_side = ctk.CTkFrame(split_container, fg_color="#1e293b", corner_radius=15)
        left_side.pack(side="left", fill="both", expand=True, padx=(0, 10))

        ctk.CTkLabel(left_side, text="Available Cameras", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)
        
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
                    text=f"Camera {idx}: {cam_name}",
                    command=lambda i=idx, n=cam_name: self.start_workout(cameraModule.open_camera(i), n),
                    height=50,
                    corner_radius=10
                ).pack(fill="x", pady=5)

        # RIGHT - FILE UPLOAD
        right_side = ctk.CTkFrame(split_container, fg_color="#1e293b", corner_radius=15)
        right_side.pack(side="right", fill="both", expand=True, padx=(10, 0))

        ctk.CTkLabel(right_side, text="Upload Media", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)

        ctk.CTkButton(
            right_side,
            text="Choose Video/Image",
            command=self.choose_file_and_start,
            height=50
        ).pack(pady=20)

        # Drag & Drop Area
        self.drop_area = ctk.CTkFrame(right_side, height=200, fg_color="#0f172a", corner_radius=15)
        self.drop_area.pack(fill="x", padx=30, pady=20)
        
        ctk.CTkLabel(self.drop_area, text="Drag & Drop Here").pack(expand=True)
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
        if self.selected_exercise == "pullup":
            from exercises.pullup import PullupAnalyser
            self.analyser = PullupAnalyser()
            self.angle_points = (11, 13, 15)
        # Add other exercises here...
        else:
            self.analyser = None
            self.angle_points = (11, 13, 15) # Default

        # UI for Step 3
        header = ctk.CTkFrame(self.content_area, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))

        ctk.CTkButton(header, text="← Back", width=80, command=self.stop_workout_and_back).pack(side="left")
        ctk.CTkLabel(header, text=f"Workout Session: {self.selected_exercise.capitalize()}", font=ctk.CTkFont(size=24, weight="bold"), padx=20).pack(side="left")

        # Layout for video and stats
        main_workout_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        main_workout_frame.pack(fill="both", expand=True)

        # Video Canvas
        self.video_label = ctk.CTkLabel(main_workout_frame, text="")
        self.video_label.pack(side="left", fill="both", expand=True, padx=20)

        # Stats Panel
        stats_panel = ctk.CTkFrame(main_workout_frame, width=300, fg_color="#1e293b", corner_radius=15)
        stats_panel.pack(side="right", fill="y")
        stats_panel.pack_propagate(False)

        ctk.CTkLabel(stats_panel, text="STATISTICS", font=ctk.CTkFont(size=18, weight="bold"), text_color="#38bdf8").pack(pady=20)
        
        self.rep_label = ctk.CTkLabel(stats_panel, text="Reps: 0", font=ctk.CTkFont(size=32, weight="bold"))
        self.rep_label.pack(pady=10)

        self.feedback_label = ctk.CTkLabel(stats_panel, text="Analyzing...", font=ctk.CTkFont(size=14), wraplength=250, text_color="yellow")
        self.feedback_label.pack(pady=10, padx=20)

        # New: History Scrollable Frame
        ctk.CTkLabel(stats_panel, text="HISTORY", font=ctk.CTkFont(size=14, weight="bold"), text_color="gray").pack(pady=(20, 5))
        self.history_scroll = ctk.CTkScrollableFrame(stats_panel, fg_color="#0f172a", height=300)
        self.history_scroll.pack(fill="both", expand=True, padx=10, pady=10)

        self.is_running = True
        self.update_frame()

    def stop_workout_and_back(self):
        self.is_running = False
        if self.update_job:
            self.after_cancel(self.update_job)
        
        self.save_session() # New: Save data
        
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
        color = "#10b981" if rep_data["success"] else "#ef4444"
        
        item = ctk.CTkFrame(self.history_scroll, fg_color="#1e293b", height=40)
        item.pack(fill="x", pady=2, padx=5)
        
        ctk.CTkLabel(item, text=f"Rep {rep_data['rep_num']}", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=10)
        ctk.CTkLabel(item, text=f"{rep_data['tempo']}s", text_color=color).pack(side="right", padx=10)

    def save_session(self):
        if not self.session_data:
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

