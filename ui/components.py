                  
import os
import math
import customtkinter as ctk
from PIL import Image
from ui import theme


class SidebarButton(ctk.CTkButton):
    def __init__(self, parent, text, command, active=False, **kwargs):
        super().__init__(
            parent,
            text=text,
            command=command,
            anchor="w",
            height=46,
            fg_color=theme.ACCENT if active else "transparent",
            text_color=theme.TEXT_ON_ACCENT if active else theme.SUBTEXT,
            hover_color=theme.CARD_HOVER,
            font=theme.get_font(13, "bold" if active else "normal"),
            corner_radius=theme.BTN_RADIUS,
            border_width=1 if active else 0,
            border_color=theme.ACCENT if active else theme.SIDEBAR,
            **kwargs
        )
        self.pack(fill="x", pady=4, padx=16)

    def set_active(self, active: bool):
        self.configure(
            fg_color=theme.ACCENT if active else "transparent",
            text_color=theme.TEXT_ON_ACCENT if active else theme.SUBTEXT,
            font=theme.get_font(13, "bold" if active else "normal"),
            border_width=1 if active else 0,
            border_color=theme.ACCENT if active else theme.SIDEBAR,
        )


class SessionListItem(ctk.CTkFrame):
    def __init__(self, parent, exercise, date_str, total_reps, success_rate, command, **kwargs):
        super().__init__(
            parent,
            fg_color=theme.CARD,
            corner_radius=10,
            border_width=1,
            border_color=theme.BORDER,
            cursor="hand2",
            **kwargs
        )
        self.command = command

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=12, pady=(10, 2))

        ctk.CTkLabel(
            top, text=exercise.upper(),
            font=theme.get_font(11, "bold"),
            text_color=theme.ACCENT
        ).pack(side="left")

        rate_color = theme.SUCCESS if success_rate >= 70 else (theme.WARNING if success_rate >= 40 else theme.DANGER)
        ctk.CTkLabel(
            top, text=f"{success_rate}%",
            font=theme.get_font(11, "bold"),
            text_color=rate_color
        ).pack(side="right")

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkLabel(
            bottom, text=date_str,
            font=theme.get_font(10),
            text_color=theme.SUBTEXT
        ).pack(side="left")

        ctk.CTkLabel(
            bottom, text=f"{total_reps} reps",
            font=theme.get_font(10),
            text_color=theme.SUBTEXT
        ).pack(side="right")

        for w in [self] + list(self.winfo_children()) + [top, bottom] + list(top.winfo_children()) + list(bottom.winfo_children()):
            try:
                w.bind("<Button-1>", lambda e: self.command())
                w.bind("<Enter>", lambda e: self.configure(border_color=theme.ACCENT))
                w.bind("<Leave>", lambda e: self.configure(border_color=theme.BORDER))
            except Exception:
                pass


class ExerciseCard(ctk.CTkFrame):
    def __init__(self, parent, name, desc, img_path, command, **kwargs):
        super().__init__(
            parent,
            fg_color=theme.CARD,
            corner_radius=theme.CARD_RADIUS,
            cursor="hand2",
            border_width=1,
            border_color=theme.BORDER,
            **kwargs
        )
        self.command = command
        self._build(name, desc, img_path)
        self._bind_all()

    def _build(self, name, desc, img_path):
        img_frame = ctk.CTkFrame(self, fg_color="transparent")
        img_frame.pack(pady=(24, 8))

        if img_path and os.path.exists(img_path):
            try:
                img = Image.open(img_path)
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(140, 140))
                ctk.CTkLabel(img_frame, image=ctk_img, text="").pack()
            except Exception:
                ctk.CTkLabel(img_frame, text="🏋️", font=theme.get_font(56)).pack()
        else:
            ctk.CTkLabel(img_frame, text="🏋️", font=theme.get_font(56)).pack()

        ctk.CTkLabel(
            self, text=name.upper(),
            font=theme.get_font(20, "bold"),
            text_color=theme.ACCENT
        ).pack(pady=(6, 4))

        ctk.CTkLabel(
            self, text=desc,
            font=theme.get_font(13),
            text_color=theme.SUBTEXT,
            wraplength=260
        ).pack(pady=(0, 20), padx=20)

    def _bind_all(self):
        def on_enter(e):
            self.configure(border_color=theme.ACCENT, border_width=2, fg_color=theme.CARD_HOVER)
        def on_leave(e):
            self.configure(border_color=theme.BORDER, border_width=1, fg_color=theme.CARD)

        for w in self.winfo_children() + [self]:
            try:
                w.bind("<Enter>", on_enter)
                w.bind("<Leave>", on_leave)
                w.bind("<Button-1>", lambda e: self.command())
            except Exception:
                pass

        for child in self.winfo_children():
            for grandchild in child.winfo_children():
                try:
                    grandchild.bind("<Enter>", on_enter)
                    grandchild.bind("<Leave>", on_leave)
                    grandchild.bind("<Button-1>", lambda e: self.command())
                except Exception:
                    pass


class StatCard(ctk.CTkFrame):
    def __init__(self, parent, label, value="–", unit="", color=None, **kwargs):
        super().__init__(
            parent,
            fg_color=theme.CARD,
            corner_radius=12,
            border_width=1,
            border_color=theme.BORDER,
            **kwargs
        )
        self._color = color or theme.ACCENT

        ctk.CTkLabel(
            self, text=label.upper(),
            font=theme.get_font(10, "bold"),
            text_color=theme.SUBTEXT
        ).pack(pady=(12, 2))

        self._val_label = ctk.CTkLabel(
            self, text=value,
            font=theme.mono(32, "bold"),
            text_color=self._color
        )
        self._val_label.pack()

        if unit:
            ctk.CTkLabel(
                self, text=unit,
                font=theme.get_font(11),
                text_color=theme.SUBTEXT
            ).pack(pady=(0, 10))
        else:
            ctk.CTkFrame(self, fg_color="transparent", height=10).pack()

    def set_value(self, value: str, color=None):
        self._val_label.configure(text=str(value), text_color=color or self._color)


class AnimatedRepCounter(ctk.CTkFrame):
    """Large animated rep counter with a circular progress ring drawn on canvas."""

    RING_SIZE = 140
    RING_WIDTH = 10

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._reps = 0
        self._target = 0
        self._anim_after = None

        import tkinter as tk
        self._canvas = tk.Canvas(
            self,
            width=self.RING_SIZE,
            height=self.RING_SIZE,
            bg=theme.BACKGROUND,
            highlightthickness=0
        )
        self._canvas.pack(pady=(8, 0))

        self._rep_text = ctk.CTkLabel(
            self, text="0",
            font=theme.mono(42, "bold"),
            text_color=theme.ACCENT
        )
        self._rep_text.place(
            x=self.RING_SIZE // 2,
            y=self.RING_SIZE // 2,
            anchor="center"
        )

        ctk.CTkLabel(
            self, text="REPS",
            font=theme.get_font(10, "bold"),
            text_color=theme.SUBTEXT
        ).pack(pady=(4, 8))

        self._draw_ring(0)

    def _draw_ring(self, pct: float):
        c = self._canvas
        c.delete("all")
        pad = self.RING_WIDTH + 4
        size = self.RING_SIZE
                         
        c.create_arc(pad, pad, size - pad, size - pad,
                     start=90, extent=360,
                     style="arc", outline=theme.BORDER,
                     width=self.RING_WIDTH)
        if pct > 0:
            extent = -pct * 3.6                 
            c.create_arc(pad, pad, size - pad, size - pad,
                         start=90, extent=extent,
                         style="arc", outline=theme.ACCENT,
                         width=self.RING_WIDTH)

    def set_reps(self, reps: int, total: int = 0):
        self._target = reps
        self._animate()
        pct = (reps / total * 100) if total > 0 else 0
        self._draw_ring(min(pct, 100))
        self._rep_text.configure(text=str(reps))

    def _animate(self):
        if self._anim_after:
            try:
                self._rep_text.after_cancel(self._anim_after)
            except Exception:
                pass
                            
        self._rep_text.configure(text_color=theme.WARNING)
        self._anim_after = self._rep_text.after(
            180, lambda: self._rep_text.configure(text_color=theme.ACCENT)
        )


class FeedbackBar(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            fg_color=theme.CARD,
            corner_radius=10,
            border_width=1,
            border_color=theme.BORDER,
            **kwargs
        )
        ctk.CTkLabel(
            self, text="LIVE ANALYSIS",
            font=theme.get_font(10, "bold"),
            text_color=theme.SUBTEXT
        ).pack(anchor="w", padx=14, pady=(10, 2))

        self._label = ctk.CTkLabel(
            self, text="Waiting for pose...",
            font=theme.get_font(13),
            text_color=theme.WARNING,
            wraplength=260,
            justify="left"
        )
        self._label.pack(anchor="w", padx=14, pady=(0, 12))

    def set_text(self, text: str, level: str = "warning"):
        color_map = {
            "good": theme.SUCCESS,
            "warning": theme.WARNING,
            "error": theme.DANGER,
            "info": theme.ACCENT,
        }
        self._label.configure(text=text, text_color=color_map.get(level, theme.WARNING))


class LabeledProgressBar(ctk.CTkFrame):
    def __init__(self, parent, label: str, value: float = 0.0, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x")

        ctk.CTkLabel(row, text=label, font=theme.get_font(11), text_color=theme.SUBTEXT).pack(side="left")
        self._pct_label = ctk.CTkLabel(row, text="0%", font=theme.get_font(11, "bold"), text_color=theme.TEXT)
        self._pct_label.pack(side="right")

        self._bar = ctk.CTkProgressBar(self, height=5, corner_radius=3, fg_color=theme.BORDER, progress_color=theme.ACCENT)
        self._bar.pack(fill="x", pady=(3, 0))
        self._bar.set(value)

    def set_value(self, value: float):
        """value: 0.0 – 1.0"""
        value = max(0.0, min(1.0, value))
        self._bar.set(value)
        pct = int(value * 100)
        if pct >= 70:
            color = theme.SUCCESS
        elif pct >= 40:
            color = theme.WARNING
        else:
            color = theme.DANGER
        self._bar.configure(progress_color=color)
        self._pct_label.configure(text=f"{pct}%")


class CameraCard(ctk.CTkFrame):
                                                           
    _all_cards = []

    def __init__(self, parent, index: int, name: str, is_active: bool, command, **kwargs):
        super().__init__(
            parent,
            fg_color=theme.CARD,
            corner_radius=12,
            border_width=2 if is_active else 1,
            border_color=theme.ACCENT if is_active else theme.BORDER,
            cursor="hand2",
            **kwargs
        )
        self.command    = command
        self._selected  = is_active
        self._index     = index

                            
        CameraCard._all_cards.append(self)

        self._cam_label = ctk.CTkLabel(
            self, text=f"CAM {index}",
            font=theme.get_font(11, "bold"),
            text_color=theme.ACCENT
        )
        self._cam_label.pack(pady=(14, 2))

        self._name_label = ctk.CTkLabel(
            self, text=name,
            font=theme.get_font(11),
            text_color=theme.SUBTEXT
        )
        self._name_label.pack(padx=10)

        self._status_label = ctk.CTkLabel(
            self,
            text="● SELECTED" if is_active else "AVAILABLE",
            font=theme.get_font(9, "bold"),
            text_color=theme.ACCENT if is_active else theme.SUBTEXT
        )
        self._status_label.pack(pady=(4, 14))

        def _on_click(e=None):
                                            
            for card in CameraCard._all_cards:
                if card is not self:
                    card._deselect()
            self._select()
            self.command()

        def _on_enter(e=None):
            if not self._selected:
                self.configure(border_color=theme.SECONDARY, border_width=1)
                self._status_label.configure(text="● CLICK TO SELECT", text_color=theme.SECONDARY)

        def _on_leave(e=None):
            if not self._selected:
                self.configure(border_color=theme.BORDER, border_width=1)
                self._status_label.configure(text="AVAILABLE", text_color=theme.SUBTEXT)

        def _walk(widget):
            try:
                widget.bind("<Button-1>", _on_click)
                widget.bind("<Enter>",    _on_enter)
                widget.bind("<Leave>",    _on_leave)
            except Exception:
                pass
            for child in widget.winfo_children():
                _walk(child)

        _walk(self)

    def _select(self):
        self._selected = True
        self.configure(border_color=theme.ACCENT, border_width=2,
                       fg_color=theme.CARD_HOVER)
        self._status_label.configure(text="● SELECTED", text_color=theme.ACCENT)

    def _deselect(self):
        self._selected = False
        self.configure(border_color=theme.BORDER, border_width=1,
                       fg_color=theme.CARD)
        self._status_label.configure(text="AVAILABLE", text_color=theme.SUBTEXT)

    def destroy(self):
                                      
        if self in CameraCard._all_cards:
            CameraCard._all_cards.remove(self)
        super().destroy()
                                                                               
           
class DropZone(ctk.CTkFrame):
    def __init__(self, parent, on_file_selected, **kwargs):
        super().__init__(
            parent,
            fg_color=theme.BACKGROUND,
            corner_radius=14,
            border_width=2,
            border_color=theme.BORDER,
            **kwargs
        )
        self._callback = on_file_selected
        self._file_loaded = False

        self._icon = ctk.CTkLabel(self, text="⬆", font=theme.get_font(36), text_color=theme.SUBTEXT)
        self._icon.pack(pady=(28, 4))

        self._title = ctk.CTkLabel(
            self, text="Drag & drop video here",
            font=theme.get_font(14, "bold"),
            text_color=theme.TEXT
        )
        self._title.pack()

        self._sub = ctk.CTkLabel(
            self, text="MP4 · AVI · MOV · MKV",
            font=theme.get_font(11),
            text_color=theme.SUBTEXT
        )
        self._sub.pack(pady=(2, 16))

        self._browse_btn = StyledButton(
            self, text="Browse files", command=self._browse,
            type="secondary", width=130, height=34
        )
        self._browse_btn.pack(pady=(0, 20))

                                   
        try:
            self.drop_target_register("DND_Files")               
            self.dnd_bind("<<Drop>>", self._on_drop)
        except Exception:
            pass

    def _browse(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv")]
        )
        if path:
            self._set_file(path)

    def _on_drop(self, event):
        path = event.data.strip("{}")
        ext = path.split(".")[-1].lower()
        if ext in ("mp4", "avi", "mov", "mkv"):
            self._set_file(path)

    def _set_file(self, path):
        import os
        name = os.path.basename(path)
        size_mb = round(os.path.getsize(path) / 1_048_576, 1)
        self._file_loaded = True
        self.configure(border_color=theme.ACCENT, border_width=2)
        self._icon.configure(text="✓", text_color=theme.SUCCESS)
        self._title.configure(text=name, text_color=theme.SUCCESS)
        self._sub.configure(text=f"{size_mb} MB  ·  Ready to analyse")
        self._browse_btn.configure(text="Change file")
        self._callback(path)

    def reset(self):
        self._file_loaded = False
        self.configure(border_color=theme.BORDER)
        self._icon.configure(text="⬆", text_color=theme.SUBTEXT)
        self._title.configure(text="Drag & drop video here", text_color=theme.TEXT)
        self._sub.configure(text="MP4 · AVI · MOV · MKV", text_color=theme.SUBTEXT)
        self._browse_btn.configure(text="Browse files")


class RepHistoryItem(ctk.CTkFrame):
    def __init__(self, parent, rep_data: dict, **kwargs):
        n = rep_data.get("rep_num", "?")
        tempo = rep_data.get("tempo", 0)
        success = rep_data.get("success", False)
        rom = rep_data.get("rom", 0)

        color = theme.SUCCESS if success else theme.DANGER

        super().__init__(
            parent,
            fg_color=theme.CARD,
            corner_radius=8,
            border_width=1,
            border_color=color,
            **kwargs
        )

        left = ctk.CTkFrame(self, fg_color="transparent")
        left.pack(side="left", padx=12, pady=8)

        ctk.CTkLabel(
            left, text=f"REP {n}",
            font=theme.get_font(12, "bold"),
            text_color=theme.ACCENT
        ).pack(anchor="w")

        ctk.CTkLabel(
            left, text=f"ROM {rom:.1f}°",
            font=theme.get_font(10),
            text_color=theme.SUBTEXT
        ).pack(anchor="w")

        right = ctk.CTkFrame(self, fg_color="transparent")
        right.pack(side="right", padx=12, pady=8)

        ctk.CTkLabel(
            right, text=f"{tempo:.2f}s",
            font=theme.get_font(12, "bold"),
            text_color=color
        ).pack()

        ctk.CTkLabel(
            right, text="✓ OK" if success else "✗ FAIL",
            font=theme.get_font(9, "bold"),
            text_color=color
        ).pack()


class StyledButton(ctk.CTkButton):
    def __init__(self, parent, text, command, type="primary", **kwargs):
        styles = {
            "primary": dict(fg_color=theme.ACCENT, text_color=theme.TEXT_ON_ACCENT, hover_color=theme.SECONDARY, border_width=0),
            "secondary": dict(fg_color="transparent", text_color=theme.TEXT, hover_color=theme.CARD_HOVER, border_width=1, border_color=theme.BORDER),
            "danger": dict(fg_color=theme.DANGER, text_color=theme.TEXT, hover_color="#cc0000", border_width=0),
            "ghost": dict(fg_color="transparent", text_color=theme.ACCENT, hover_color=theme.CARD_HOVER, border_width=1, border_color=theme.ACCENT),
        }
        s = styles.get(type, styles["primary"])
        super().__init__(
            parent, text=text, command=command,
            corner_radius=theme.BTN_RADIUS,
            font=theme.get_font(13, "bold"),
            **s, **kwargs
        )


class SectionLabel(ctk.CTkLabel):
    def __init__(self, parent, text, **kwargs):
        super().__init__(
            parent, text=text.upper(),
            font=theme.get_font(10, "bold"),
            text_color=theme.SUBTEXT,
            **kwargs
        )

                                                                               
from PIL import ImageFilter, ImageEnhance

class ExerciseCard(ctk.CTkFrame):
    def __init__(self, parent, name, desc, img_path, video_path, command, **kwargs):
        super().__init__(
            parent,
            fg_color=theme.CARD,
            corner_radius=theme.CARD_RADIUS,
            cursor="hand2",
            border_width=2,
            border_color=theme.BORDER,
            **kwargs
        )
        self.command     = command
        self._video_path = video_path
        self._img_path   = img_path
        self._name       = name
        self._cap        = None
        self._after_id   = None
        self._playing    = False
        
        self._current_size = (332, 212)                      
        self._base_img     = None
        self._thumbnail    = None

        self._build(name, img_path)
        self._bind_all()

    def _build(self, name, img_path):
        self._preview_label = ctk.CTkLabel(
            self, text=name.upper(),
            font=theme.get_font(26, "bold"),
            text_color="white",
            compound="center",
            corner_radius=theme.CARD_RADIUS - 2
        )
        self._preview_label.pack(fill="both", expand=True, padx=4, pady=4)

        if img_path and os.path.exists(img_path):
            try:
                self._base_img = Image.open(img_path)
            except Exception as e:
                print(f"Error loading img: {e}")
                self._preview_label.configure(text=name.upper() + "\n(Image Error)")
        else:
            self._preview_label.configure(text=name.upper() + "\n(No Image)")
            
        self._update_thumbnail()

    def _update_thumbnail(self):
        if not self._base_img:
            return
            
        try:
                    
            img = self._base_img.resize(self._current_size)
            
                             
            enhancer = ImageEnhance.Brightness(img)
            img_dark = enhancer.enhance(0.4)
            img_blur = img_dark.filter(ImageFilter.GaussianBlur(3))
            
            self._thumbnail = ctk.CTkImage(
                light_image=img_blur, dark_image=img_blur, size=self._current_size
            )
                                              
            if not self._playing:
                self._preview_label.configure(image=self._thumbnail)
        except Exception as e:
            print("Error rendering thumbnail:", e)

    def _bind_all(self):
        def on_enter(e):
            self.configure(border_color=theme.ACCENT)
            self._start_video()

        def on_leave(e):
            self.configure(border_color=theme.BORDER)
            self._stop_video()

        def on_click(e):
            self.command()
            
        def on_resize(e):
            w = max(10, e.width)
            h = max(10, e.height)
            if (w, h) != self._current_size:
                self._current_size = (w, h)
                self._update_thumbnail()

        targets = [self, self._preview_label]
        for w in targets:
            try:
                w.bind("<Enter>", on_enter)
                w.bind("<Leave>", on_leave)
                w.bind("<Button-1>", on_click)
            except Exception:
                pass
                
        self._preview_label.bind("<Configure>", on_resize)

    def _start_video(self):
        if not self._video_path or not os.path.exists(self._video_path):
            return
        if self._playing:
            return
        self._playing = True
        self._cap = __import__('cv2').VideoCapture(self._video_path)
        
                                                                                                       
        self._preview_label.configure(font=theme.get_font(26, "bold"))
        self._next_frame()

    def _next_frame(self):
        if not self._playing or self._cap is None:
            return
        success, frame = self._cap.read()
        if not success:
                                
            self._cap.set(__import__('cv2').CAP_PROP_POS_FRAMES, 0)
            success, frame = self._cap.read()
            
        if success:
            import cv2
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_pil   = Image.fromarray(frame_rgb).resize(self._current_size)
            
                                                           
            enhancer = ImageEnhance.Brightness(img_pil)
            img_dark = enhancer.enhance(0.5)
                
            ctk_img   = ctk.CTkImage(light_image=img_dark, dark_image=img_dark, size=self._current_size)
            self._preview_label.configure(image=ctk_img)
            self._preview_label.image = ctk_img
            
                       
        self._after_id = self.after(33, self._next_frame)           

    def _stop_video(self):
        self._playing = False
        if self._after_id:
            try:
                self.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None
            
        if self._cap:
            self._cap.release()
            self._cap = None
            
                           
        if self._thumbnail:
            self._preview_label.configure(image=self._thumbnail, font=theme.get_font(26, "bold"))
        
    def destroy(self):
        self._stop_video()
        super().destroy()


class Divider(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=theme.BORDER, height=1, **kwargs)
        self.pack(fill="x", padx=16, pady=8)