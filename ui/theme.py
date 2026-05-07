             
import customtkinter as ctk

                                                                                
BACKGROUND   = "#020817"               
SIDEBAR      = "#0b1628"                    
CARD         = "#111f36"                 
CARD_HOVER   = "#162540"                       
BORDER       = "#1e3352"                   
BORDER_ACCENT= "#00e5ff"                                      

ACCENT       = "#00e5ff"                 
SECONDARY    = "#6366f1"                     
SUCCESS      = "#10b981"          
WARNING      = "#f59e0b"          
DANGER       = "#ef4444"        

TEXT         = "#f1f5f9"                 
SUBTEXT      = "#64748b"               
TEXT_ON_ACCENT = "#020817"                           

                                                                                
def get_font(size=14, weight="normal", family="Inter"):
    return ctk.CTkFont(family=family, size=size, weight=weight)

def mono(size=14, weight="normal"):
    return ctk.CTkFont(family="Courier New", size=size, weight=weight)

                                                                                
CARD_RADIUS  = 16
BTN_RADIUS   = 10
PADDING      = 20
MARGIN       = 15

                                                                                
def apply():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")