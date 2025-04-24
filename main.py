import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from src.gui.process_input_scene import ProcessInputScene
from src.gui.run_live_scene import RunLiveScene
from src.gui.run_at_once_scene import RunAtOnceScene

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CHRONOS")
        self.resize(800, 600)
        
        # Create instances of all scenes
        self.process_input_scene = ProcessInputScene()
        self.run_live_scene = RunLiveScene()
        self.run_at_once_scene = RunAtOnceScene()
        
        # Set the initial scene as the process input scene
        self.setCentralWidget(self.process_input_scene)

def main():
    """Main entry point for the CHRONOS CPU Scheduler application."""
    # Initialize application
    app = QApplication(sys.argv)
    
    # Set application name and metadata
    app.setApplicationName("CHRONOS")
    app.setApplicationDisplayName("CHRONOS")

    # Create and show main window
    window = ProcessInputScene()
    window.show()

    # Start application event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()