import os
import customtkinter as ctk
from PIL import Image
from .scheduler_config import SchedulerConfigFrame

class WelcomeScreen(ctk.CTkFrame):
    """
    Welcome screen for the CPU Scheduler application.
    """
    
    def __init__(self, master, switch_to_config):
        """
        Initialize the welcome screen.
        
        Args:
            master: The parent widget
            switch_to_config: Callback function to switch to config screen
        """
        super().__init__(master)
        self.master = master
        self.switch_to_config = switch_to_config
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=1)
        
        # Try to load banner image
        try:
            banner_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                     "assets", "banner.png")
            banner_image = ctk.CTkImage(Image.open(banner_path), size=(400, 180))
            ctk.CTkLabel(self, image=banner_image, text="").grid(row=0, column=0, pady=(20, 0), sticky="n")
        except Exception:
            # If image loading fails, show text banner instead
            ctk.CTkLabel(self, text="CPU SCHEDULER", font=ctk.CTkFont(size=32, weight="bold")).grid(
                row=0, column=0, pady=(20, 0), sticky="n")
            
        # Title and description
        ctk.CTkLabel(self, text="Operating Systems Project", 
                   font=ctk.CTkFont(size=24)).grid(row=1, column=0, pady=(0, 10))
        
        description_text = (
            "This application simulates various CPU scheduling algorithms:\n"
            "• First-Come, First-Served (FCFS)\n"
            "• Shortest Job First (SJF) - Preemptive and Non-Preemptive\n"
            "• Priority Scheduling - Preemptive and Non-Preemptive\n"
            "• Round Robin\n\n"
            "Features include live visualization, dynamic process addition, and performance metrics."
        )
        
        ctk.CTkLabel(self, text=description_text, 
                   font=ctk.CTkFont(size=14), justify="left").grid(row=2, column=0, padx=40, pady=10)
        
        # Start button
        ctk.CTkButton(self, text="Start Scheduler", 
                    font=ctk.CTkFont(size=16), 
                    command=self.switch_to_config,
                    width=200, height=40).grid(row=3, column=0, pady=20)