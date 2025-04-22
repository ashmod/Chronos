from PyQt6.QtWidgets import QWidget
from PyQt6 import uic
import os

class RunLiveScene(QWidget):
    def __init__(self):
        super().__init__()
        # Get the directory containing the UI file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ui_file = os.path.join(current_dir, "PyQtUI", "runLiveSceneUI.ui")
        
        # Load the UI
        uic.loadUi(ui_file, self)
        
        # Initialize UI elements
        self.setup_ui()
    
    def setup_ui(self):
        # TODO: Connect signals and initialize UI state
        pass