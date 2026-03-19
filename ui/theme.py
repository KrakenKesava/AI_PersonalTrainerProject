# ui/theme.py
import customtkinter as ctk

# ── Core Palette ──────────────────────────────────────────────────────────────
BACKGROUND   = "#020817"   # deepest bg
SIDEBAR      = "#0b1628"   # sidebar surface
CARD         = "#111f36"   # card surface
CARD_HOVER   = "#162540"   # card hover surface
BORDER       = "#1e3352"   # default border
BORDER_ACCENT= "#00e5ff"   # accent border (active / selected)

ACCENT       = "#00e5ff"   # primary cyan
SECONDARY    = "#6366f1"   # indigo highlight
SUCCESS      = "#10b981"   # green
WARNING      = "#f59e0b"   # amber
DANGER       = "#ef4444"   # red

TEXT         = "#f1f5f9"   # primary text
SUBTEXT      = "#64748b"   # muted text
TEXT_ON_ACCENT = "#020817" # text placed on ACCENT bg

# ── Fonts ─────────────────────────────────────────────────────────────────────
def get_font(size=14, weight="normal", family="Inter"):
    return ctk.CTkFont(family=family, size=size, weight=weight)

def mono(size=14, weight="normal"):
    return ctk.CTkFont(family="Courier New", size=size, weight=weight)

# ── Spacing & Radii ───────────────────────────────────────────────────────────
CARD_RADIUS  = 16
BTN_RADIUS   = 10
PADDING      = 20
MARGIN       = 15

# ── CTk Appearance ────────────────────────────────────────────────────────────
def apply():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")