import os
import time
import threading
import customtkinter as ctk
from PIL import Image

class SplashScreen(ctk.CTkToplevel):
    """
    Splash screen shown during application startup.
    """
    
    def __init__(self, master, on_complete):
        """
        Initialize the splash screen.
        
        Args:
            master: The parent widget
            on_complete: Callback function when splash screen is complete
        """
        super().__init__(master)
        self.master = master
        self.on_complete = on_complete
        self._is_running = True  # Flag to track if splash screen is still active
        
        # Configure window
        self.title("CHRONOS")
        self.attributes('-topmost', True)
        self.overrideredirect(True)  # Remove window decorations
        
        # Get screen dimensions for centering
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Set splash window size and position
        width = 600
        height = 300
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        
        # Main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Configure main frame grid
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=0)
        main_frame.grid_rowconfigure(2, weight=0)
        
        # Try to load SVG logo first
        logo_loaded = False
        try:
            logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                   "docs", "logo.svg")
            
            # Try using cairosvg to convert SVG
            try:
                from cairosvg import svg2png
                import io
                
                # Convert SVG to PNG in memory
                png_data = io.BytesIO()
                svg2png(url=logo_path, write_to=png_data, output_width=200, output_height=200)
                png_data.seek(0)
                
                # Create image from PNG data
                logo_image = ctk.CTkImage(light_image=Image.open(png_data),
                                       dark_image=Image.open(png_data),
                                       size=(200, 200))
                ctk.CTkLabel(main_frame, image=logo_image, text="").grid(
                    row=0, column=0, pady=(20, 0))
                logo_loaded = True
            except ImportError:
                print("cairosvg not available for SVG conversion")
        except Exception as e:
            print(f"Error loading logo SVG: {e}")
            
        # If SVG loading fails, try the banner image
        if not logo_loaded:
            try:
                banner_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                         "docs", "logo.svg")
                banner_image = ctk.CTkImage(Image.open(banner_path), size=(400, 180))
                ctk.CTkLabel(main_frame, image=banner_image, text="").grid(row=0, column=0, pady=(20, 0))
                logo_loaded = True
            except Exception:
                # If all image loading fails, show text banner with CHRONOS name
                ctk.CTkLabel(main_frame, text="CHRONOS", font=ctk.CTkFont(size=36, weight="bold")).grid(
                    row=0, column=0, pady=(20, 0))
        
        # Loading text
        ctk.CTkLabel(main_frame, text="CPU Scheduler Simulator", 
                   font=ctk.CTkFont(size=20)).grid(row=1, column=0, pady=(10, 20))
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(main_frame)
        self.progress_bar.grid(row=2, column=0, padx=40, pady=20, sticky="ew")
        self.progress_bar.set(0)
        
        # Ensure splash screen is displayed before starting progress
        self.update_idletasks()
        self.lift()
        
        # Setup protocol handler for window close
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Start progress bar animation
        self.progress_thread = threading.Thread(target=self._run_progress)
        self.progress_thread.daemon = True
        self.progress_thread.start()
    
    def _on_closing(self):
        """Handle window closing event"""
        self._is_running = False
        self.destroy()
    
    def _run_progress(self):
        """Simulate loading with progress bar animation."""
        try:
            for i in range(101):
                if not self._is_running:
                    return
                    
                time.sleep(0.02)  # Short delay for animation
                progress = i / 100.0
                
                # Update progress bar safely using after() method
                if self._is_running:
                    self.after(0, lambda p=progress: self._update_progress(p))
                
                # Short pause between updates
                time.sleep(0.005)
            
            # Loading complete
            time.sleep(0.5)  # Short pause at the end
            
            # Close splash screen and call the completion callback using after()
            if self._is_running:
                self.after(0, self._complete)
                
        except Exception as e:
            print(f"Error in progress animation: {e}")
            if self._is_running:
                self.after(0, self._complete)
    
    def _update_progress(self, progress):
        """Update progress bar from the main thread"""
        if self._is_running and hasattr(self, 'progress_bar'):
            try:
                self.progress_bar.set(progress)
            except Exception:
                pass  # Ignore errors if widget is being destroyed
    
    def _complete(self):
        """Complete the splash screen process safely"""
        self._is_running = False
        
        try:
            self.destroy()
        except Exception:
            pass  # Ignore errors if already destroyed
            
        # Call completion callback after ensuring splash is destroyed
        if self.on_complete:
            self.after(100, self.on_complete)