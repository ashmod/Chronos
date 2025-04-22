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
        # Connect signals
        self.addLiveProcessButton.clicked.connect(self.add_live_process)
        self.runLiveButton.clicked.connect(self.run_live)
        self.runAllButton.clicked.connect(self.run_all)
        self.pauseButton.clicked.connect(self.pause_simulation)  # Pause button
        self.returnToInputSceneButton.clicked.connect(self.return_to_input)

    def add_live_process(self):
        # TODO: Add a new process during live simulation
        pass

    def run_live(self):
        # TODO: Start the live simulation step by step
        pass

    def run_all(self):
        # TODO: Run the simulation to completion
        pass

    def pause_simulation(self):
        # TODO: Pause the current simulation
        pass

    def return_to_input(self):
        # TODO: Return to the process input scene
        pass