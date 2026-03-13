import customtkinter as ctk

# COLORS
BACKGROUND = "#0b1220"
SIDEBAR = "#0f1a2f"
CARD = "#16223a"
ACCENT = "#00e5ff"
SECONDARY = "#4f7cff"
DANGER = "#ff4d4d"
TEXT = "#ffffff"
SUBTEXT = "#94a3b8"

# FONTS
def get_font(size=14, weight="normal", family="Inter"):
    return ctk.CTkFont(family=family, size=size, weight=weight)

TITLE_FONT = ("Inter", 32, "bold")
SUBTITLE_FONT = ("Inter", 18, "bold")
BODY_FONT = ("Inter", 14, "normal")

# SPACING & RADIUS
CARD_RADIUS = 20
PADDING = 20
MARGIN = 15
