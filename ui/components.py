import os
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
            height=50,
            fg_color=theme.ACCENT if active else "transparent",
            text_color="#000000" if active else theme.SUBTEXT,
            hover_color="#1a2a47",
            font=theme.get_font(15, "bold" if active else "normal"),
            corner_radius=12,
            border_width=0,
            **kwargs
        )
        self.pack(fill="x", pady=5, padx=20)

class ExerciseCard(ctk.CTkFrame):
    def __init__(self, parent, name, desc, img_path, command, **kwargs):
        super().__init__(
            parent,
            fg_color=theme.CARD,
            corner_radius=theme.CARD_RADIUS,
            cursor="hand2",
            border_width=2,
            border_color="#1e293b",
            **kwargs
        )
        
        self.command = command
        
        # Banner Image Area
        self.img_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.img_frame.pack(fill="x", pady=(20, 10))
        
        if img_path and os.path.exists(img_path):
            try:
                img = Image.open(img_path)
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(180, 180))
                self.logo_label = ctk.CTkLabel(self.img_frame, image=ctk_img, text="")
                self.logo_label.pack()
            except Exception:
                self.logo_label = ctk.CTkLabel(self.img_frame, text="🏋️", font=theme.get_font(64))
                self.logo_label.pack()
        else:
            self.logo_label = ctk.CTkLabel(self.img_frame, text="🏋️", font=theme.get_font(64))
            self.logo_label.pack()

        self.title_label = ctk.CTkLabel(
            self,
            text=name.upper(),
            font=theme.get_font(22, "bold"),
            text_color=theme.ACCENT
        )
        self.title_label.pack(pady=(10, 5))

        self.desc_label = ctk.CTkLabel(
            self,
            text=desc,
            font=theme.get_font(15),
            text_color=theme.SUBTEXT,
            wraplength=300
        )
        self.desc_label.pack(pady=(0, 20), padx=30)

        # Start Workout Button
        self.start_btn = StyledButton(
            self, 
            text="START WORKOUT", 
            command=self.command,
            type="primary",
            width=200,
            height=45
        )
        self.start_btn.pack(pady=(0, 30))

        # Bindings for hover
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        
        # Recursive bind
        self.bind_widgets(self)

    def bind_widgets(self, widget):
        for child in widget.winfo_children():
            if not isinstance(child, ctk.CTkButton):
                child.bind("<Enter>", self.on_enter)
                child.bind("<Leave>", self.on_leave)
                child.bind("<Button-1>", lambda e: self.command())
                self.bind_widgets(child)

    def on_enter(self, e):
        self.configure(border_color=theme.ACCENT, border_width=3)
        self.configure(fg_color="#1d2b4a")

    def on_leave(self, e):
        self.configure(border_color="#1e293b", border_width=2)
        self.configure(fg_color=theme.CARD)

class ChatBubble(ctk.CTkFrame):
    def __init__(self, parent, text, is_user=True, **kwargs):
        align = "right" if is_user else "left"
        bg_color = "#1a2a47" if is_user else "#1e293b"
        border_color = theme.SECONDARY if is_user else theme.ACCENT
        
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.pack(fill="x", pady=15)
        
        inner_bubble = ctk.CTkFrame(
            self, 
            fg_color=bg_color, 
            corner_radius=18,
            border_width=2,
            border_color=border_color
        )
        inner_bubble.pack(side=align, padx=10)

        ctk.CTkLabel(
            inner_bubble,
            text=text,
            font=theme.get_font(15),
            text_color=theme.TEXT,
            wraplength=500,
            justify="left"
        ).pack(padx=20, pady=15)

class StyledButton(ctk.CTkButton):
    def __init__(self, parent, text, command, type="primary", **kwargs):
        fg = theme.ACCENT if type == "primary" else "transparent"
        txt = "#000000" if type == "primary" else theme.TEXT
        border = 0 if type == "primary" else 2
        
        # FIXED: Avoiding "transparent" for border_color to prevent ValueError
        border_col = theme.ACCENT if type == "primary" else theme.SECONDARY
        hover = theme.SECONDARY if type == "primary" else "#1a2a47"
        
        if type == "danger":
            fg = theme.DANGER
            txt = theme.TEXT
            hover = "#cc0000"
            border = 0
            border_col = theme.DANGER

        super().__init__(
            parent,
            text=text,
            command=command,
            fg_color=fg,
            text_color=txt,
            hover_color=hover,
            border_width=border,
            border_color=border_col,
            corner_radius=12,
            font=theme.get_font(14, "bold"),
            **kwargs
        )
