#!/usr/bin/env python3
import sys
import time
import os
import threading
import customtkinter as ctk
from PIL import Image, ImageTk
import tkinter as tk

from src.gui.splash_screen import SplashScreen
from src.gui.welcome_screen import WelcomeScreen
from src.gui.scheduler_config import SchedulerConfigFrame
from src.gui.simulation_screen import SimulationScreen


class CPUSchedulerApp:
    """
    Main CPU Scheduler application.
    """
    
    def __init__(self, master):
        """
        Initialize the application.
        
        Args:
            master: The root Tk window
        """
        self.master = master
        self.master.title("CHRONOS")
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Configure theme
        ctk.set_appearance_mode("dark")  # Options: "dark", "light"
        ctk.set_default_color_theme("blue")  # Options: "blue", "green", "dark-blue"
        
        # Set window icon using SVG logo
        self.set_app_icon()
        
        # Configure window size and position
        window_width = 1200
        window_height = 800
        
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.master.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.master.minsize(900, 600)
        
        # Configure main grid
        self.master.grid_columnconfigure(0, weight=1)
        self.master.grid_rowconfigure(0, weight=1)
        
        # Initialize variables
        self.current_frame = None
        self.welcome_frame = None
        self.config_frame = None
        self.simulation_frame = None
        
        # Show splash screen and then welcome screen
        self.master.withdraw()  # Hide main window until splash screen is done
        self.splash = SplashScreen(self.master, self.show_welcome_screen)
    
    def set_app_icon(self):
        """Set the application icon using the SVG logo."""
        try:
            # Directly use the icon.ico file instead of SVG conversion
            icon_path = os.path.join(os.path.dirname(__file__), "docs", "icon.ico")
            if os.path.exists(icon_path):
                self.master.iconbitmap(icon_path)
            else:
                print(f"Warning: Icon file not found at {icon_path}")
        except Exception as e:
            print(f"Error setting application icon: {e}")
    
    def show_welcome_screen(self):
        """Show the welcome screen."""
        # Show main window
        self.master.deiconify()
        
        # Create and show welcome screen
        self.welcome_frame = WelcomeScreen(self.master, self.show_config_screen)
        self.switch_frame(self.welcome_frame)
    
    def show_config_screen(self):
        """Show the scheduler configuration screen."""
        # Create config screen if it doesn't exist
        if self.config_frame is None:
            self.config_frame = SchedulerConfigFrame(self.master, self.show_simulation_screen)
            
        # Switch to config screen
        self.switch_frame(self.config_frame)
    
    def show_simulation_screen(self, scheduler):
        """
        Show the simulation screen with the configured scheduler.
        
        Args:
            scheduler: The configured scheduler to use for simulation3.11.7\Lib\tkinter_init.py", line 1943, in call
            def call(self, *args):
            
            KeyboardInterrupt
            
            fix these
            
            GitHub Copilot
            I'll fix the errors in the simulation_screen.py file. Looking at the traceback, there are issues with attempting to set the 'font' property on CTkFrame objects, which doesn't support this attribute. The main problem is in the _apply_gantt_zoom() method where the code is trying to configure frames with font attributes.
            
            Let me examine the code and make the necessary fixes:
            
            
        """
        # Create simulation screen if it doesn't exist
        if self.simulation_frame is None:
            self.simulation_frame = SimulationScreen(self.master, self.show_config_screen)
            
        # Set scheduler and switch to simulation screen
        self.simulation_frame.set_scheduler(scheduler)
        self.switch_frame(self.simulation_frame)
    
    def switch_frame(self, frame):
        """
        Switch to a different frame.
        
        Args:
            frame: The frame to switch to
        """
        # Hide current frame if it exists
        if self.current_frame is not None:
            self.current_frame.grid_forget()
            
        # Show new frame
        frame.grid(row=0, column=0, sticky="nsew")
        self.current_frame = frame
    
    def on_close(self):
        """Handle window close event."""
        # Check if simulation is running
        if (self.simulation_frame is not None and 
            hasattr(self.simulation_frame, 'simulation') and 
            self.simulation_frame.simulation and 
            self.simulation_frame.simulation.running):
            
            # Confirm exit if simulation is running
            from tkinter import messagebox
            if not messagebox.askyesno("Confirm Exit", 
                                    "A simulation is still running. Are you sure you want to exit?"):
                return
                
            # Stop simulation
            self.simulation_frame.simulation.stop()
            
        # Destroy window
        self.master.destroy()
        sys.exit(0)


if __name__ == "__main__":
    # Create root window
    root = ctk.CTk()
    
    # Create and run application
    app = CPUSchedulerApp(root)
    
    # Start main loop
    root.mainloop()

