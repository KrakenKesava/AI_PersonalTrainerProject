# sourceSelectorGUI.py
"""
AI Fitness Trainer Pro — Main GUI
Dark navy theme · CustomTkinter · tkinterdnd2
Screens: Exercise Select → Source Select → Live Workout → Session Review
"""

import os, json, time, threading
import cv2
import numpy as np
import customtkinter as ctk
from datetime import datetime
from PIL import Image, ImageTk
from tkinter import messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES
from dotenv import load_dotenv

import cameraModule
import PoseModule as pm
import RepCounterModule as rep

from ui import theme
from ui.components import (
    SidebarButton, SessionListItem, ExerciseCard,
    StatCard, AnimatedRepCounter, FeedbackBar,
    LabeledProgressBar, CameraCard, DropZone,
    RepHistoryItem, StyledButton, SectionLabel, Divider
)
from ui.session_review_page import SessionReviewPage

# ─────────────────────────────────────────────────────────────────────────────
# Supported formats
# ─────────────────────────────────────────────────────────────────────────────
VIDEO_FORMATS = ("mp4", "avi", "mov", "mkv")
IMAGE_FORMATS = ("jpg", "jpeg", "png", "bmp", "webp")


class MainApp(TkinterDnD.Tk):
    # ─────────────────────────────────────────────────────────────────────────
    # Init
    # ─────────────────────────────────────────────────────────────────────────
    def __init__(self):
        super().__init__()
        theme.apply()

        self.title("AI Fitness Trainer Pro")
        self.geometry("1440x860")
        self.minsize(1100, 700)
        self.configure(bg=theme.BACKGROUND)

        # ── App state ────────────────────────────────────────────────────────
        self.selected_exercise = "pullup"
        self.selected_source   = None
        self.selected_name     = ""
        self.is_running        = False
        self.session_data      = []
        self.update_job        = None
        self.pTime             = 0.0
        self.last_feedback     = "Start your workout"
        self._pending_review   = None   # session dict to show after workout ends

        # ── CV components ────────────────────────────────────────────────────
        self.detector  = pm.poseDetector()
        self.reps      = rep.RepCounter()
        self.analyser  = None
        self.angle_pts = (11, 13, 15)

        # ── AI ───────────────────────────────────────────────────────────────
        load_dotenv()
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model   = None
        self._init_gemini()

        # ── Build UI ─────────────────────────────────────────────────────────
        self._build_layout()
        self.show_exercise_selection()

    def _init_gemini(self):
        if not self.api_key:
            return
        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            self.model  = "gemini-3.1-flash-lite-previewS"

        except Exception as e:
            print(f"[Gemini] init failed: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # Layout skeleton
    # ─────────────────────────────────────────────────────────────────────────
    def _build_layout(self):
        self.main_container = ctk.CTkFrame(self, fg_color=theme.BACKGROUND, corner_radius=0)
        self.main_container.pack(fill="both", expand=True)

        self._build_sidebar()

        self.content_area = ctk.CTkFrame(self.main_container, fg_color=theme.BACKGROUND, corner_radius=0)
        self.content_area.pack(side="right", fill="both", expand=True)

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self.main_container, width=220, corner_radius=0,
            fg_color=theme.SIDEBAR,
            border_width=1, border_color=theme.BORDER
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=16, pady=(28, 20))

        ctk.CTkLabel(
            logo_frame, text="AI TRAINER PRO",
            font=theme.get_font(18, "bold"),
            text_color=theme.ACCENT
        ).pack(anchor="w")

        ctk.CTkLabel(
            logo_frame, text="Fitness coach",
            font=theme.get_font(10),
            text_color=theme.SUBTEXT
        ).pack(anchor="w")

        ctk.CTkFrame(logo_frame, fg_color=theme.ACCENT, height=2, width=120).pack(anchor="w", pady=(6, 0))

        # Nav buttons
        SectionLabel(self.sidebar, "Menu").pack(anchor="w", padx=16, pady=(12, 4))

        self.btn_workout = SidebarButton(self.sidebar, "🏋  Workout hub",    self.show_exercise_selection, active=True)
        self.btn_ai      = SidebarButton(self.sidebar, "✦  AI assistant",   self.show_chat_interface)

        # Session history
        SectionLabel(self.sidebar, "Recent sessions").pack(anchor="w", padx=16, pady=(16, 4))

        self.history_sidebar = ctk.CTkScrollableFrame(
            self.sidebar, fg_color="transparent",
            scrollbar_button_color=theme.BORDER,
            scrollbar_button_hover_color=theme.ACCENT
        )
        self.history_sidebar.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self._refresh_sidebar_history()

        # Footer
        footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        footer.pack(side="bottom", fill="x", padx=16, pady=16)

        StyledButton(
            footer, text="Terminate session",
            command=self._safe_quit, type="danger", height=38
        ).pack(fill="x")

    def _refresh_sidebar_history(self):
        for w in self.history_sidebar.winfo_children():
            w.destroy()

        sessions_dir = "sessions"
        if not os.path.exists(sessions_dir):
            ctk.CTkLabel(
                self.history_sidebar, text="No sessions yet",
                font=theme.get_font(11), text_color=theme.SUBTEXT
            ).pack(pady=8)
            return

        files = sorted(
            [f for f in os.listdir(sessions_dir) if f.endswith(".json")],
            reverse=True
        )[:10]

        if not files:
            ctk.CTkLabel(
                self.history_sidebar, text="No sessions yet",
                font=theme.get_font(11), text_color=theme.SUBTEXT
            ).pack(pady=8)
            return

        for fname in files:
            try:
                with open(os.path.join(sessions_dir, fname)) as f:
                    data = json.load(f)
                reps_list = data.get("reps", [])
                total = len(reps_list)
                good  = sum(1 for r in reps_list if r.get("success"))
                rate  = int(good / total * 100) if total else 0
                date_str = data.get("date", "")[:10]

                SessionListItem(
                    self.history_sidebar,
                    exercise    = data.get("exercise", "?"),
                    date_str    = date_str,
                    total_reps  = total,
                    success_rate= rate,
                    command     = lambda d=data: self._show_review_from_sidebar(d)
                ).pack(fill="x", pady=3)
            except Exception:
                continue

    def _show_review_from_sidebar(self, session_data: dict):
        self._nav_set_active("ai")
        self._show_review(session_data)

    # ─────────────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────────────
    def _clear_content(self):
        for w in self.content_area.winfo_children():
            w.destroy()

    def _nav_set_active(self, which: str):
        self.btn_workout.set_active(which == "workout")
        self.btn_ai.set_active(which == "ai")

    def _topbar(self, title: str, badge_text: str = "", badge_color=None, back_cmd=None):
        bar = ctk.CTkFrame(self.content_area, fg_color="transparent")
        bar.pack(fill="x", padx=28, pady=(22, 8))

        if back_cmd:
            StyledButton(bar, text="← Back", command=back_cmd, type="secondary", width=90, height=32).pack(side="left")

        ctk.CTkLabel(
            bar, text=title,
            font=theme.get_font(22, "bold"),
            text_color=theme.TEXT
        ).pack(side="left", padx=(12 if back_cmd else 0, 0))

        if badge_text:
            ctk.CTkLabel(
                bar, text=badge_text,
                font=theme.get_font(10, "bold"),
                text_color=badge_color or theme.ACCENT,
                fg_color=theme.CARD,
                corner_radius=8, padx=10, pady=3
            ).pack(side="right")

        return bar

    def _safe_quit(self):
        self.is_running = False
        if self.update_job:
            self.after_cancel(self.update_job)
        if isinstance(self.selected_source, cv2.VideoCapture):
            self.selected_source.release()
        self.quit()

    # ─────────────────────────────────────────────────────────────────────────
    # SCREEN 1 — Exercise Selection
    # ─────────────────────────────────────────────────────────────────────────
    def show_exercise_selection(self):
        self._stop_workout_quietly()
        self._clear_content()
        self._nav_set_active("workout")

        self._topbar("Select your exercise", badge_text="Step 1 of 3", badge_color=theme.SECONDARY)

        # Step breadcrumb
        self._step_indicator(1)

        grid = ctk.CTkFrame(self.content_area, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=28, pady=(8, 24))
        grid.grid_columnconfigure((0, 1), weight=1, pad=12)
        grid.grid_rowconfigure((0, 1), weight=1, pad=12)

        exercises = [
            (
                "Pushups",
                "Place hands shoulder-width apart...",
                "exerciseVideos/Pushups/pushup.png",
                "exerciseVideos/Pushups/Pushups_Side_Correct.mp4"
            ),
            (
                "Pullups",
                "Grab the bar and pull yourself up...",
                "exerciseVideos/Pullups/pullup.png",
                "exerciseVideos/Pullups/Pullup_Side_Correct.mp4"
            ),
            (
                "Squads",
                "Lower your hips from a standing position...",
                "exerciseVideos/Squads/Squads.png",
                "exerciseVideos/Squads/Squads_Side_Correct.mp4"
            ),
            (
                "Situps",
                "Lie on your back with knees bent...",
                "exerciseVideos/Situps/situps.png",
                "exerciseVideos/Situps/Situps_Side_Correct.mp4"
            ),
        ]

        for i, (name, desc, img, vid) in enumerate(exercises):
            r, c = divmod(i, 2)
            card = ExerciseCard(
                grid, name=name, desc=desc, img_path=img,
                video_path=vid,
                command=lambda n=name.lower(): self.show_source_selection(n)
            )
            card.grid(row=r, column=c, sticky="nsew", padx=10, pady=10)

    # ─────────────────────────────────────────────────────────────────────────
    # SCREEN 2 — Source Selection
    # ─────────────────────────────────────────────────────────────────────────
    def show_source_selection(self, exercise: str):
        self.selected_exercise = exercise
        self._clear_content()
        self._nav_set_active("workout")

        self._topbar(
            f"Input source — {exercise.capitalize()}",
            badge_text="Step 2 of 3",
            badge_color=theme.SECONDARY,
            back_cmd=self.show_exercise_selection
        )
        self._step_indicator(2)

        # Tab bar
        tab_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        tab_frame.pack(fill="x", padx=28, pady=(4, 0))

        self._src_tab_var = ctk.StringVar(value="camera")

        tab_bg = ctk.CTkFrame(tab_frame, fg_color=theme.CARD, corner_radius=10)
        tab_bg.pack(side="left")

        self._tab_cam_btn = ctk.CTkButton(
            tab_bg, text="Live camera", width=130, height=34,
            fg_color=theme.ACCENT, text_color=theme.TEXT_ON_ACCENT,
            hover_color=theme.SECONDARY, corner_radius=8,
            font=theme.get_font(12, "bold"),
            command=lambda: self._switch_src_tab("camera")
        )
        self._tab_cam_btn.pack(side="left", padx=4, pady=4)

        self._tab_vid_btn = ctk.CTkButton(
            tab_bg, text="Upload video", width=130, height=34,
            fg_color="transparent", text_color=theme.SUBTEXT,
            hover_color=theme.CARD_HOVER, corner_radius=8,
            font=theme.get_font(12),
            command=lambda: self._switch_src_tab("video")
        )
        self._tab_vid_btn.pack(side="left", padx=4, pady=4)

        # Panel container
        self._src_panel_container = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self._src_panel_container.pack(fill="both", expand=True, padx=28, pady=12)

        self._camera_panel = self._build_camera_panel(self._src_panel_container)
        self._video_panel  = self._build_video_panel(self._src_panel_container)

        self._switch_src_tab("camera")

        # Footer
        src_footer = ctk.CTkFrame(self.content_area, fg_color="transparent")
        src_footer.pack(fill="x", padx=28, pady=(0, 20))

        StyledButton(src_footer, text="← Back", command=self.show_exercise_selection, type="secondary", width=100, height=38).pack(side="left")
        self._src_ready_label = ctk.CTkLabel(src_footer, text="Built-in webcam selected — ready", font=theme.get_font(11), text_color=theme.SUCCESS)
        self._src_ready_label.pack(side="left", padx=16)

    def _build_camera_panel(self, parent):
        panel = ctk.CTkFrame(parent, fg_color="transparent")

        # Camera cards row
        cards_row = ctk.CTkFrame(panel, fg_color="transparent")
        cards_row.pack(fill="x", pady=(0, 12))

        indexes = cameraModule.list_cameras()
        names   = cameraModule.get_camera_names()

        if not indexes:
            ctk.CTkLabel(cards_row, text="No cameras detected.", font=theme.get_font(13), text_color=theme.DANGER).pack(pady=20)
        else:
            for idx in indexes:
                cam_name = cameraModule.get_camera_name(idx, names)
                CameraCard(
                    cards_row,
                    index=idx, name=cam_name, is_active=(idx == 0),
                    command=lambda i=idx, n=cam_name: self._select_camera(i, n)
                ).pack(side="left", padx=6, ipadx=8, ipady=4)

        # Settings row
        settings = ctk.CTkFrame(panel, fg_color=theme.CARD, corner_radius=12, border_width=1, border_color=theme.BORDER)
        settings.pack(fill="x", pady=4)

        inner = ctk.CTkFrame(settings, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        self._res_var = ctk.StringVar(value="1280×720 (HD)")
        self._fps_var = ctk.StringVar(value="30 fps")

        for label, var, options in [
            ("Resolution", self._res_var, ["1280×720 (HD)", "1920×1080 (Full HD)", "640×480"]),
            ("Frame rate", self._fps_var, ["30 fps", "60 fps", "15 fps"]),
        ]:
            row = ctk.CTkFrame(inner, fg_color="transparent")
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(row, text=label, font=theme.get_font(12), text_color=theme.SUBTEXT).pack(side="left")
            ctk.CTkOptionMenu(row, values=options, variable=var, width=180, fg_color=theme.BACKGROUND,
                              button_color=theme.BORDER, button_hover_color=theme.ACCENT,
                              font=theme.get_font(12)).pack(side="right")

        # Start button
        StyledButton(
            panel, text="Start workout →", type="primary", height=44,
            command=lambda: self._launch_from_camera()
        ).pack(fill="x", pady=(12, 0))

        return panel

    def _build_video_panel(self, parent):
        panel = ctk.CTkFrame(parent, fg_color="transparent")

        self._drop_zone = DropZone(panel, on_file_selected=self._on_video_file_selected)
        self._drop_zone.pack(fill="x")

        self._video_start_btn = StyledButton(
            panel, text="Start workout →", type="primary", height=44,
            command=lambda: self._launch_from_file()
        )
        self._video_start_btn.pack(fill="x", pady=12)
        self._video_start_btn.configure(state="disabled")

        self._pending_video_path = None
        return panel

    def _on_video_file_selected(self, path: str):
        self._pending_video_path = path
        self._video_start_btn.configure(state="normal")
        self._src_ready_label.configure(text=f"{os.path.basename(path)} — ready", text_color=theme.SUCCESS)

    def _switch_src_tab(self, tab: str):
        is_cam = (tab == "camera")
        self._tab_cam_btn.configure(
            fg_color=theme.ACCENT if is_cam else "transparent",
            text_color=theme.TEXT_ON_ACCENT if is_cam else theme.SUBTEXT,
            font=theme.get_font(12, "bold" if is_cam else "normal")
        )
        self._tab_vid_btn.configure(
            fg_color=theme.ACCENT if not is_cam else "transparent",
            text_color=theme.TEXT_ON_ACCENT if not is_cam else theme.SUBTEXT,
            font=theme.get_font(12, "bold" if not is_cam else "normal")
        )
        if is_cam:
            self._video_panel.pack_forget()
            self._camera_panel.pack(fill="both", expand=True)
        else:
            self._camera_panel.pack_forget()
            self._video_panel.pack(fill="both", expand=True)

    def _select_camera(self, idx: int, name: str):
        self._pending_camera_idx  = idx
        self._pending_camera_name = name
        self._src_ready_label.configure(text=f"{name} selected — ready", text_color=theme.SUCCESS)

    def _launch_from_camera(self):
        idx  = getattr(self, "_pending_camera_idx",  0)
        name = getattr(self, "_pending_camera_name", "Webcam 0")
        cap  = cameraModule.open_camera(idx)
        if cap is None or not cap.isOpened():
            messagebox.showerror("Camera error", f"Could not open camera {idx}.")
            return
        self.start_workout(cap, name)

    def _launch_from_file(self):
        path = getattr(self, "_pending_video_path", None)
        if not path:
            return
        ext = path.rsplit(".", 1)[-1].lower()
        if ext in IMAGE_FORMATS:
            img = cv2.imread(path)
            if img is not None:
                self.start_workout(img, os.path.basename(path))
        else:
            cap = cv2.VideoCapture(path)
            if cap.isOpened():
                self.start_workout(cap, os.path.basename(path))
            else:
                messagebox.showerror("File error", "Could not open video file.")

    # ─────────────────────────────────────────────────────────────────────────
    # SCREEN 3 — Live Workout
    # ─────────────────────────────────────────────────────────────────────────
    def start_workout(self, source, name: str):
        self.selected_source = source
        self.selected_name   = name
        self.session_data    = []
        self.reps            = rep.RepCounter()
        self._clear_content()
        self._nav_set_active("workout")
        self._init_analyser()

        # ── Header ───────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self.content_area, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(16, 8))

        StyledButton(
            header, text="✕  Abort session",
            command=self.stop_workout_and_back,
            type="danger", width=140, height=34
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text=f"Live — {self.selected_exercise.capitalize()}",
            font=theme.get_font(20, "bold"),
            text_color=theme.TEXT
        ).pack(side="left", padx=16)

        self._session_timer_label = ctk.CTkLabel(
            header, text="00:00",
            font=theme.mono(14, "bold"),
            text_color=theme.SUBTEXT
        )
        self._session_timer_label.pack(side="right")
        self._session_start = time.time()
        self._tick_timer()

        Divider(self.content_area)

        # ── Body: video feed + stats ──────────────────────────────────────────
        body = ctk.CTkFrame(self.content_area, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        # Video column
        vid_col = ctk.CTkFrame(body, fg_color=theme.BACKGROUND,
                               border_width=2, border_color=theme.ACCENT, corner_radius=12)
        vid_col.pack(side="left", fill="both", expand=True, padx=(0, 16))

        self.video_label = ctk.CTkLabel(vid_col, text="Initialising camera...")
        self.video_label.pack(fill="both", expand=True, padx=2, pady=2)

        # Stats column
        stats_col = ctk.CTkFrame(body, width=240, fg_color=theme.SIDEBAR,
                                 corner_radius=14, border_width=1, border_color=theme.BORDER)
        stats_col.pack(side="right", fill="y")
        stats_col.pack_propagate(False)

        SectionLabel(stats_col, "Telemetry").pack(anchor="w", padx=16, pady=(16, 8))

        # Animated rep counter
        self._rep_counter_widget = AnimatedRepCounter(stats_col)
        self._rep_counter_widget.pack(pady=(0, 8))

        Divider(stats_col)

        # Metric cards
        mc_frame = ctk.CTkFrame(stats_col, fg_color="transparent")
        mc_frame.pack(fill="x", padx=12, pady=4)
        mc_frame.grid_columnconfigure((0, 1), weight=1, pad=6)

        self._rom_card   = StatCard(mc_frame, "ROM",   "–°",  color=theme.SECONDARY)
        self._tempo_card = StatCard(mc_frame, "Tempo", "–s",  color=theme.WARNING)
        self._rom_card.grid(row=0, column=0, sticky="nsew", padx=3, pady=3)
        self._tempo_card.grid(row=0, column=1, sticky="nsew", padx=3, pady=3)

        Divider(stats_col)

        # Feedback bar
        SectionLabel(stats_col, "Form feedback").pack(anchor="w", padx=16, pady=(4, 4))
        self._feedback_bar = FeedbackBar(stats_col)
        self._feedback_bar.pack(fill="x", padx=12, pady=(0, 8))

        Divider(stats_col)

        # Rep history log
        SectionLabel(stats_col, "Session log").pack(anchor="w", padx=16, pady=(4, 4))
        self._history_scroll = ctk.CTkScrollableFrame(
            stats_col, fg_color="transparent",
            scrollbar_button_color=theme.BORDER,
            scrollbar_button_hover_color=theme.ACCENT
        )
        self._history_scroll.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # Footer
        StyledButton(
            self.content_area, text="End session & review →",
            command=self.stop_workout_and_review,
            type="primary", height=40
        ).pack(fill="x", padx=24, pady=(0, 16))

        self.is_running = True
        self.update_frame()

    def _init_analyser(self):
        ex = self.selected_exercise
        self.analyser = None
        if ex in ("pullup", "pullups"):
            from exercises.pullup import PullupAnalyser
            self.analyser  = PullupAnalyser()
            self.angle_pts = (11, 13, 15)
            self.reps.set_thresholds(100, 115)
        elif ex in ("pushup", "pushups"):
            from exercises.pushup import PushupAnalyser
            self.analyser  = PushupAnalyser()
            self.angle_pts = (11, 13, 15)
            self.reps.set_thresholds(110, 140)
        elif ex in ("squat", "squads", "squats"):
            from exercises.squat import SquatAnalyser
            self.analyser  = SquatAnalyser()
            self.angle_pts = (23, 25, 27)
            self.reps.set_thresholds(115, 145)
        else:
            self.angle_pts = (11, 13, 15)
            self.reps.set_thresholds(60, 150)

    def _tick_timer(self):
        if not self.is_running:
            return
        elapsed = int(time.time() - self._session_start)
        m, s = divmod(elapsed, 60)
        self._session_timer_label.configure(text=f"{m:02d}:{s:02d}")
        self.after(1000, self._tick_timer)

    def stop_workout_and_back(self):
        self._stop_workout_quietly()
        self.save_session()
        self._refresh_sidebar_history()
        self.show_exercise_selection()

    def stop_workout_and_review(self):
        self._stop_workout_quietly()
        self.save_session()
        self._refresh_sidebar_history()
        session = self._build_session_dict()
        self._show_review(session)

    def _stop_workout_quietly(self):
        self.is_running = False
        if self.update_job:
            try:
                self.after_cancel(self.update_job)
            except Exception:
                pass
            self.update_job = None
        if isinstance(self.selected_source, cv2.VideoCapture):
            self.selected_source.release()
            self.selected_source = None

    def update_frame(self):
        if not self.is_running:
            return

        if isinstance(self.selected_source, np.ndarray):
            frame = self.selected_source.copy()
            self.display_frame(self.process_cv_logic(frame))
            return

        if self.selected_source is None:
            return

        success, frame = self.selected_source.read()
        if success:
            self.display_frame(self.process_cv_logic(frame))
            self.update_job = self.after(10, self.update_frame)
        else:
            self.stop_workout_and_review()

    def process_cv_logic(self, img):
        img_h, img_w = img.shape[:2]
        scale       = img_w / 1280
        font_scale  = max(0.6, 0.8 * scale)
        thickness   = max(1, int(2 * scale))
        margin_x    = int(img_w * 0.10)
        margin_y    = int(img_h * 0.15)

        cTime = time.time()
        fps   = 1 / (cTime - self.pTime) if self.pTime else 0
        self.pTime = cTime

        cv2.putText(img, f"FPS: {int(fps)}", (margin_x, margin_y),
                    cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 255, 0), thickness)

        img    = self.detector.findPose(img)
        lmList = self.detector.findPosition(img, False)

        reps_count = self.reps.rep_count
        percentage = 0

        if lmList:
            angle = self.detector.findAngle(
                img, self.angle_pts[0], self.angle_pts[1], self.angle_pts[2], True
            )

            if self.analyser:
                self.analyser.update(angle)

            percentage = float(np.clip(np.interp(angle, (50, 160), (100, 0)), 0, 100))
            reps_count, rep_done = self.reps.update(angle)

            # Update animated rep counter
            self._rep_counter_widget.set_reps(reps_count)

            if rep_done and self.analyser:
                result = self.analyser.analyse_rep()
                entry = {
                    "rep_num":   reps_count,
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "rom":       result.get("rom", 0),
                    "tempo":     result.get("repTime", 0),
                    "feedback":  result.get("feedback", []),
                    "success":   result.get("formCorrect", False),
                }
                self.session_data.append(entry)
                self._add_history_item(entry)

                self.last_feedback = " | ".join(result["feedback"])
                level = "good" if result.get("formCorrect") else "warning"
                self._feedback_bar.set_text(self.last_feedback.replace(" | ", "\n"), level)
                self._rom_card.set_value(f"{result.get('rom', 0):.1f}°")
                self._tempo_card.set_value(f"{result.get('repTime', 0):.2f}s")

            elif not rep_done and self.analyser and hasattr(self.analyser, "get_live_feedback"):
                live_fb = self.analyser.get_live_feedback(angle)
                self._feedback_bar.set_text(live_fb, "info")

        # CV overlays
        cv2.putText(img, f"Reps: {int(reps_count)}",
                    (margin_x, margin_y + int(60 * scale)),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2 * scale, (255, 0, 0), int(3 * scale))

        last_tempo = self.session_data[-1]["tempo"] if self.session_data else 0
        cv2.putText(img, f"Tempo: {last_tempo:.2f}s",
                    (margin_x, margin_y + int(110 * scale)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8 * scale, (255, 255, 0), int(2 * scale))

        # Progress bar
        bx, by    = margin_x, margin_y + int(160 * scale)
        bar_h     = int(300 * scale)
        bar_w     = int(40 * scale)
        filled    = int(np.interp(percentage, (0, 100), (0, bar_h)))
        cv2.rectangle(img, (bx, by), (bx + bar_w, by + bar_h), (0, 255, 0), thickness)
        cv2.rectangle(img, (bx, by + bar_h - filled), (bx + bar_w, by + bar_h), (0, 255, 0), cv2.FILLED)
        cv2.putText(img, f"{int(percentage)}%", (bx, by - int(15 * scale)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8 * scale, (255, 255, 255), thickness)

        # Feedback overlay
        feedback_lines = self.last_feedback.split("|")
        y_off = img_h - int(120 * scale)
        for i, line in enumerate(feedback_lines):
            line = line.strip()
            (tw, th), _ = cv2.getTextSize(line, cv2.FONT_HERSHEY_SIMPLEX, 0.7 * scale, thickness)
            y = y_off + i * int(45 * scale)
            cv2.rectangle(img, (margin_x - 10, y - th - 10), (margin_x + tw + 10, y + 10), (20, 20, 20), cv2.FILLED)
            cv2.putText(img, line, (margin_x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7 * scale, (255, 255, 0), thickness)

        return img

    def _add_history_item(self, rep_data: dict):
        item = RepHistoryItem(self._history_scroll, rep_data)
        item.pack(fill="x", pady=3)
        # Auto-scroll to bottom
        self._history_scroll._parent_canvas.yview_moveto(1.0)

    def display_frame(self, frame):
        h, w  = frame.shape[:2]
        target_h = 580
        target_w = int(target_h * w / h)
        resized  = cv2.resize(frame, (target_w, target_h))
        rgb      = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        img_pil  = Image.fromarray(rgb)
        img_tk   = ImageTk.PhotoImage(image=img_pil)
        self.video_label.configure(image=img_tk, text="")
        self.video_label.image = img_tk

    # ─────────────────────────────────────────────────────────────────────────
    # SCREEN 4 — Session Review
    # ─────────────────────────────────────────────────────────────────────────
    def _show_review(self, session: dict):
        self._clear_content()
        self._nav_set_active("ai")

        page = SessionReviewPage(
            self.content_area,
            session           = session,
            gemini_client     = getattr(self, "client", None),
            gemini_model_name = self.model,
            on_back           = self.show_exercise_selection
        )
        page.pack(fill="both", expand=True)

        # Wire follow-up button → opens chat with context
        page.bind("<<AskFollowup>>", lambda e: self._open_chat_with_context(session))

    def _build_session_dict(self) -> dict:
        return {
            "exercise":   self.selected_exercise,
            "date":       datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_reps": len(self.session_data),
            "reps":       self.session_data,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Save session
    # ─────────────────────────────────────────────────────────────────────────
    def save_session(self):
        if not self.session_data:
            return
        os.makedirs("sessions", exist_ok=True)
        ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sessions/session_{self.selected_exercise}_{ts}.json"
        try:
            with open(filename, "w") as f:
                json.dump(self._build_session_dict(), f, indent=4)
            print(f"[Session] saved → {filename}")
        except Exception as e:
            print(f"[Session] save error: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # AI ASSISTANT (chat screen)
    # ─────────────────────────────────────────────────────────────────────────
    def show_chat_interface(self, prefill: str = ""):
        self._stop_workout_quietly()
        self._clear_content()
        self._nav_set_active("ai")

        self._topbar("AI Assistant", badge_text="Gemini powered", badge_color=theme.SECONDARY)
        Divider(self.content_area)

        chat_outer = ctk.CTkFrame(
            self.content_area, fg_color=theme.SIDEBAR,
            corner_radius=14, border_width=1, border_color=theme.BORDER
        )
        chat_outer.pack(fill="both", expand=True, padx=24, pady=(8, 16))

        self.chat_history = ctk.CTkScrollableFrame(
            chat_outer, fg_color="transparent",
            scrollbar_button_color=theme.BORDER,
            scrollbar_button_hover_color=theme.ACCENT
        )
        self.chat_history.pack(fill="both", expand=True, padx=16, pady=16)

        # Input row
        input_row = ctk.CTkFrame(chat_outer, fg_color=theme.BACKGROUND, corner_radius=10)
        input_row.pack(fill="x", padx=12, pady=(0, 12))

        self.msg_entry = ctk.CTkEntry(
            input_row,
            placeholder_text="Ask about your form, session, or technique...",
            height=44, fg_color=theme.SIDEBAR,
            border_width=1, border_color=theme.BORDER,
            font=theme.get_font(13)
        )
        self.msg_entry.pack(side="left", fill="x", expand=True, padx=(12, 8), pady=8)
        self.msg_entry.bind("<Return>", lambda e: self.send_chat_message())

        if prefill:
            self.msg_entry.insert(0, prefill)

        StyledButton(
            input_row, text="Send →", command=self.send_chat_message,
            type="primary", width=90, height=44
        ).pack(side="right", padx=(0, 12), pady=8)

        self._add_chat_bubble(
            "AI Trainer",
            "Hello! I'm your AI Personal Trainer. Ask me about your form, recent sessions, or how to improve.",
            is_user=False
        )

    def _open_chat_with_context(self, session: dict):
        reps = session.get("reps", [])
        total = len(reps)
        good  = sum(1 for r in reps if r.get("success"))
        ex    = session.get("exercise", "exercise")
        prefill = (
            f"Based on my {ex} session ({good}/{total} successful reps), "
            f"what specific drills should I focus on to improve?"
        )
        self.show_chat_interface(prefill=prefill)

    def _get_session_summary(self) -> str:
        sd = "sessions"
        if not os.path.exists(sd):
            return "No previous session data found."
        files = sorted([f for f in os.listdir(sd) if f.endswith(".json")], reverse=True)
        if not files:
            return "No previous sessions recorded."
        summary = "User's recent workout history:\n"
        for fname in files[:3]:
            try:
                with open(os.path.join(sd, fname)) as f:
                    data = json.load(f)
                reps_list = data.get("reps", [])
                total = len(reps_list)
                failed = [r for r in reps_list if not r.get("success")]
                all_fb = []
                for r in failed:
                    all_fb.extend(r.get("feedback", []))
                unique_fb = list(set(all_fb))
                rate = int((total - len(failed)) / total * 100) if total else 0
                summary += f"- {data.get('date')}: {data.get('exercise')} ({total} reps, {rate}% success)."
                if unique_fb:
                    summary += f" Issues: {', '.join(unique_fb[:3])}.\n"
                else:
                    summary += " Perfect form!\n"
            except Exception:
                continue
        return summary

    def send_chat_message(self):
        msg = self.msg_entry.get().strip()
        if not msg:
            return
        self.msg_entry.delete(0, "end")
        self._add_chat_bubble("You", msg, is_user=True)
        self._typing_bubble = self._add_chat_bubble("AI Trainer", "Thinking...", is_user=False)
        threading.Thread(target=self._generate_ai_response, args=(msg,), daemon=True).start()

    def _generate_ai_response(self, user_msg: str):
        if not self.model:
            response = "No API key found. Add GEMINI_API_KEY to your .env file."
        else:
            try:
                context = self._get_session_summary()
                prompt = f"""You are a professional AI Personal Trainer.
            Give technical, motivational, and safe advice about gym exercises.

            USER DATA:
            {context}

            Rules:
            1. Be specific about form: Pushups, Pullups, Squats.
            2. If the user mentions their history, use the context above.
            3. Use terms like Range of Motion, Tempo, Lockout.
            4. Keep responses concise (under 100 words).

            User: {user_msg}"""
                result = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt
                )
                response = result.text
            except Exception as e:
                response = f"Error: {e}"
        self.after(0, lambda: self._finalize_chat(response))

    def _finalize_chat(self, response: str):
        if hasattr(self, "_typing_bubble"):
            self._typing_bubble.destroy()
        clean = response.replace("**", "").replace("__", "").replace("*", "").replace("_", " ")
        self._add_chat_bubble("AI Trainer", clean, is_user=False)

    def _add_chat_bubble(self, sender: str, text: str, is_user: bool = True):
        frame = ctk.CTkFrame(self.chat_history, fg_color="transparent")
        frame.pack(fill="x", pady=8)

        align = "right" if is_user else "left"
        bg    = theme.CARD if is_user else "transparent"
        bc    = theme.ACCENT if is_user else theme.SECONDARY

        bubble = ctk.CTkFrame(frame, fg_color=bg, corner_radius=14, border_width=1, border_color=bc)
        bubble.pack(side=align, padx=12)

        ctk.CTkLabel(
            bubble, text=f"[{sender}]",
            font=theme.get_font(10, "bold"),
            text_color=theme.SUBTEXT
        ).pack(anchor="w", padx=14, pady=(8, 2))

        ctk.CTkLabel(
            bubble, text=text,
            font=theme.get_font(13),
            text_color=theme.TEXT,
            wraplength=460, justify="left"
        ).pack(anchor="w", padx=14, pady=(0, 10))

        self.chat_history._parent_canvas.yview_moveto(1.0)
        return frame

    # ─────────────────────────────────────────────────────────────────────────
    # Step indicator breadcrumb
    # ─────────────────────────────────────────────────────────────────────────
    def _step_indicator(self, current: int):
        steps = ["Select exercise", "Input source", "Live workout"]
        bar = ctk.CTkFrame(self.content_area, fg_color="transparent")
        bar.pack(fill="x", padx=28, pady=(0, 12))

        for i, label in enumerate(steps, 1):
            is_done   = i < current
            is_active = i == current
            color = theme.SUCCESS if is_done else (theme.ACCENT if is_active else theme.SUBTEXT)
            ctk.CTkLabel(
                bar,
                text=f"{'✓' if is_done else str(i)}. {label}",
                font=theme.get_font(11, "bold" if is_active else "normal"),
                text_color=color
            ).pack(side="left")
            if i < len(steps):
                ctk.CTkLabel(bar, text="  ›  ", font=theme.get_font(11), text_color=theme.BORDER).pack(side="left")


# ─────────────────────────────────────────────────────────────────────────────
def launch_gui():
    theme.apply()
    app = MainApp()
    app.mainloop()