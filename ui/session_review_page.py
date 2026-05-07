                           
"""
Session Review Page
Loaded after a workout ends OR when clicking a session from sidebar history.
Accepts a session dict (same shape as your JSON files).
"""
import threading
import customtkinter as ctk
from ui import theme
from ui.components import (
    StyledButton, SectionLabel, Divider,
    LabeledProgressBar, StatCard
)


class SessionReviewPage(ctk.CTkFrame):
    def __init__(self, parent, session: dict, gemini_client, gemini_model_name, on_back, **kwargs):
        """
        session           – the parsed JSON dict
        gemini_client     – google.genai.Client instance (or None)
        gemini_model_name – model name string e.g. "gemini-2.0-flash"
        on_back           – callback to return to exercise selection
        """
        super().__init__(parent, fg_color=theme.BACKGROUND, corner_radius=0, **kwargs)
        self._session     = session
        self._client      = gemini_client
        self._model_name  = gemini_model_name
        self._on_back     = on_back
        self._build()

      
    def _build(self):
        s = self._session
        reps      = s.get("reps", [])
        total     = len(reps)
        good      = sum(1 for r in reps if r.get("success"))
        avg_rom   = (sum(r.get("rom", 0) for r in reps) / total) if total else 0
        avg_tempo = (sum(r.get("tempo", 0) for r in reps) / total) if total else 0

                                                                               
        topbar = ctk.CTkFrame(self, fg_color="transparent")
        topbar.pack(fill="x", padx=24, pady=(20, 8))

        StyledButton(
            topbar, text="← New session", command=self._on_back,
            type="secondary", width=130, height=34
        ).pack(side="left")

        ctk.CTkLabel(
            topbar,
            text=f"Session review — {s.get('exercise','').capitalize()}",
            font=theme.get_font(20, "bold"),
            text_color=theme.TEXT
        ).pack(side="left", padx=20)

                
        badge_frame = ctk.CTkFrame(topbar, fg_color="transparent")
        badge_frame.pack(side="right")

        self._badge(badge_frame, s.get("date", ""), theme.SECONDARY)
        success_color = theme.SUCCESS if good == total else (theme.WARNING if good > 0 else theme.DANGER)
        self._badge(badge_frame, f"{good} / {total} successful", success_color)

        Divider(self)

                                                                               
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=0)

        left = ctk.CTkFrame(body, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=(0, 16))

        right = ctk.CTkFrame(body, width=260, fg_color="transparent")
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

                                                                               
        stat_row = ctk.CTkFrame(left, fg_color="transparent")
        stat_row.pack(fill="x", pady=(0, 16))
        for i in range(4):
            stat_row.grid_columnconfigure(i, weight=1, pad=8)

        StatCard(stat_row, "Total reps",  str(total),       color=theme.ACCENT).grid(row=0, column=0, sticky="nsew", padx=4)
        StatCard(stat_row, "Successful",  str(good),        color=success_color).grid(row=0, column=1, sticky="nsew", padx=4)
        StatCard(stat_row, "Avg ROM",     f"{avg_rom:.1f}°", color=theme.SECONDARY).grid(row=0, column=2, sticky="nsew", padx=4)
        StatCard(stat_row, "Avg tempo",   f"{avg_tempo:.2f}s", color=theme.WARNING).grid(row=0, column=3, sticky="nsew", padx=4)

                                                                               
        SectionLabel(left, "Rep-by-rep breakdown").pack(anchor="w", pady=(0, 6))

        rep_scroll = ctk.CTkScrollableFrame(
            left, fg_color="transparent",
            scrollbar_button_color=theme.BORDER,
            scrollbar_button_hover_color=theme.ACCENT
        )
        rep_scroll.pack(fill="both", expand=True)

        for rep in reps:
            self._rep_row(rep_scroll, rep)

                                                                               
        gem_card = ctk.CTkFrame(right, fg_color=theme.CARD, corner_radius=14, border_width=1, border_color=theme.BORDER)
        gem_card.pack(fill="x", pady=(0, 12))

        gem_header = ctk.CTkFrame(gem_card, fg_color="transparent")
        gem_header.pack(fill="x", padx=14, pady=(12, 4))

        ctk.CTkLabel(gem_header, text="✦", font=theme.get_font(18), text_color=theme.SECONDARY).pack(side="left")
        gem_title = ctk.CTkFrame(gem_header, fg_color="transparent")
        gem_title.pack(side="left", padx=8)
        ctk.CTkLabel(gem_title, text="Exercise Analysis", font=theme.get_font(13, "bold"), text_color=theme.TEXT).pack(anchor="w")
        ctk.CTkLabel(gem_title, text="Session feedback", font=theme.get_font(10), text_color=theme.SUBTEXT).pack(anchor="w")

        self._gem_label = ctk.CTkLabel(
            gem_card,
            text="Generating analysis...",
            font=theme.get_font(12),
            text_color=theme.SUBTEXT,
            wraplength=220,
            justify="left"
        )
        self._gem_label.pack(anchor="w", padx=14, pady=(4, 12))

        StyledButton(
            gem_card, text="Ask a follow-up ↗",
            command=self._ask_followup,
            type="ghost", height=32
        ).pack(fill="x", padx=14, pady=(0, 12))

                      
        SectionLabel(right, "Form metrics").pack(anchor="w", pady=(8, 6))

        self._pb_rom   = LabeledProgressBar(right, "ROM quality")
        self._pb_rom.pack(fill="x", pady=3)
        self._pb_chin  = LabeledProgressBar(right, "Chin clears bar")
        self._pb_chin.pack(fill="x", pady=3)
        self._pb_ext   = LabeledProgressBar(right, "Full extension")
        self._pb_ext.pack(fill="x", pady=3)
        self._pb_tempo = LabeledProgressBar(right, "Stable tempo")
        self._pb_tempo.pack(fill="x", pady=3)

        self._fill_metrics(reps)

                                       
        self._start_gemini_thread()

      
    def _badge(self, parent, text, color):
        ctk.CTkLabel(
            parent, text=text,
            font=theme.get_font(10, "bold"),
            text_color=color,
            fg_color=theme.CARD,
            corner_radius=8,
            padx=8, pady=3
        ).pack(side="right", padx=4)

    def _rep_row(self, parent, rep: dict):
        n       = rep.get("rep_num", "?")
        success = rep.get("success", False)
        rom     = rep.get("rom", 0)
        tempo   = rep.get("tempo", 0)
        ts      = rep.get("timestamp", "")
        fbs     = rep.get("feedback", [])
        color   = theme.SUCCESS if success else theme.DANGER

        row = ctk.CTkFrame(
            parent, fg_color=theme.CARD,
            corner_radius=10, border_width=1, border_color=theme.BORDER
        )
        row.pack(fill="x", pady=4)

        header = ctk.CTkFrame(row, fg_color="transparent")
        header.pack(fill="x", padx=14, pady=(10, 0))

                          
        badge = ctk.CTkFrame(header, fg_color=color, corner_radius=20, width=28, height=28)
        badge.pack(side="left")
        badge.pack_propagate(False)
        ctk.CTkLabel(badge, text=str(n), font=theme.get_font(11, "bold"), text_color=theme.TEXT_ON_ACCENT if success else theme.TEXT).pack(expand=True)

        meta = ctk.CTkFrame(header, fg_color="transparent")
        meta.pack(side="left", padx=10)
        ctk.CTkLabel(meta, text=f"Rep {n}  ", font=theme.get_font(12, "bold"), text_color=theme.TEXT).pack(side="left")
        ctk.CTkLabel(meta, text=ts, font=theme.get_font(10), text_color=theme.SUBTEXT).pack(side="left")

        right_meta = ctk.CTkFrame(header, fg_color="transparent")
        right_meta.pack(side="right")
        ctk.CTkLabel(right_meta, text=f"ROM {rom:.1f}°  ·  {tempo:.2f}s", font=theme.get_font(11), text_color=theme.SUBTEXT).pack()

                        
        if fbs:
            fb_frame = ctk.CTkFrame(row, fg_color="transparent")
            fb_frame.pack(fill="x", padx=14, pady=(4, 10))
            for fb in fbs:
                is_warn = any(k in fb.lower() for k in ("not", "higher", "partial", "incomplete", "drastic"))
                dot_color = theme.DANGER if is_warn else theme.SUCCESS
                item = ctk.CTkFrame(fb_frame, fg_color="transparent")
                item.pack(anchor="w", pady=1)
                ctk.CTkLabel(item, text="●", font=theme.get_font(9), text_color=dot_color).pack(side="left", padx=(0, 6))
                ctk.CTkLabel(item, text=fb, font=theme.get_font(11), text_color=theme.SUBTEXT).pack(side="left")

    def _fill_metrics(self, reps):
        if not reps:
            return
        total = len(reps)

                                                    
        avg_rom = sum(r.get("rom", 0) for r in reps) / total
        self._pb_rom.set_value(min(avg_rom / 120.0, 1.0))

                                                                                      
        chin_ok = sum(1 for r in reps if not any(
            "chin" in f.lower() or "higher" in f.lower()
            for f in r.get("feedback", [])
        ))
        self._pb_chin.set_value(chin_ok / total)

                                                                   
        ext_ok = sum(1 for r in reps if any("extension" in f.lower() for f in r.get("feedback", [])))
        self._pb_ext.set_value(ext_ok / total)

                                                                        
        tempo_ok = sum(1 for r in reps if any("stable" in f.lower() for f in r.get("feedback", [])))
        self._pb_tempo.set_value(tempo_ok / total)

      
    def _start_gemini_thread(self):
        threading.Thread(target=self._generate_analysis, daemon=True).start()

    def _generate_analysis(self):
        if not self._client:
            self.after(0, lambda: self._gem_label.configure(
                text="Add GEMINI_API_KEY to .env to enable AI analysis.",
                text_color=theme.WARNING
            ))
            return

        s = self._session
        reps = s.get("reps", [])
        total = len(reps)
        good = sum(1 for r in reps if r.get("success"))

        all_feedback = []
        for r in reps:
            all_feedback.extend(r.get("feedback", []))
        unique_fb = list(set(all_feedback))

        prompt = f"""
You are a professional fitness coach AI.
Analyse this workout session and give concise, actionable feedback in under 80 words.
Focus on the top 1-2 issues and one positive observation.

Exercise: {s.get('exercise')}
Date: {s.get('date')}
Total reps: {total}
Successful reps: {good}
Avg ROM: {(sum(r.get('rom',0) for r in reps)/total if total else 0):.1f}°
Avg tempo: {(sum(r.get('tempo',0) for r in reps)/total if total else 0):.2f}s
Recurring feedback: {', '.join(unique_fb)}
"""
        try:
            result = self._client.models.generate_content(
                model=self._model_name,
                contents=prompt
            )
            text = result.text.strip()
        except Exception as e:
            text = f"Error: {e}"

        clean = text.replace("**", "").replace("__", "").replace("*", "").replace("_", " ")
        self.after(0, lambda: self._gem_label.configure(text=clean, text_color=theme.TEXT))

    def _ask_followup(self):
                                                                          
                                                                       
        self.event_generate("<<AskFollowup>>")