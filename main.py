#!/usr/bin/env python3
import sys
import time
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# Set high DPI attributes before creating QApplication
if hasattr(Qt, 'AA_EnableHighDpiScaling'):
    Qt.AA_EnableHighDpiScaling = True
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

from src.gui.main_window import MainWindow
from src.gui.splash_screen import SplashScreen

def main():
    """Main entry point for the ProcessPilot CPU Scheduler application."""
    # Initialize application
    app = QApplication(sys.argv)
    
    # Set application name and metadata
    app.setApplicationName("ProcessPilot")
    app.setApplicationDisplayName("ProcessPilot")
    app.setOrganizationName("ASU Operating Systems Team")
    app.setOrganizationDomain("asu.edu")
    
    # Show splash screen (dark mode by default)
    splash = SplashScreen(app_name="ProcessPilot", dark_mode=True)
    splash.show()
    
    # Process events to ensure splash screen is displayed
    app.processEvents()
    
    # Load main window (simulate loading time)
    def finish_loading():
        # Create and show main window
        window = MainWindow()
        window.show()
        
        # Hide splash screen when main window is ready
        splash.finish(window)
    
    # Connect splash screen finished signal to lambda that shows main window
    splash.finished.connect(finish_loading)
    
    # Start application event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()