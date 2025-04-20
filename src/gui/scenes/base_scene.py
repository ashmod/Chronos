from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import pyqtSignal

class BaseScene(QWidget):
    """Base class for all scenes in the application."""
    
    # Signal to switch to another scene
    switch_scene = pyqtSignal(str)  # scene_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the UI for this scene."""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)
        
    def enter_scene(self, data=None):
        """Called when this scene becomes active."""
        pass
        
    def exit_scene(self):
        """Called when this scene is no longer active."""
        pass
        
    def set_dark_mode(self, enabled):
        """Enable or disable dark mode for this scene."""
        pass