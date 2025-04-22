from PyQt6.QtWidgets import QWidget
from PyQt6 import uic
import os

class ProcessInputScene(QWidget):
    def __init__(self):
        super().__init__()
        # Get the directory containing the UI file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ui_file = os.path.join(current_dir, "PyQtUI", "processInputSceneUI.ui")
        
        # Load the UI
        uic.loadUi(ui_file, self)
        
        # Initialize UI elements
        self.setup_ui()
    
    def setup_ui(self):
        # Connect signals
        self.addProcessButton.clicked.connect(self.add_process)
        self.removeProcessButton.clicked.connect(self.remove_process)
        self.editProcessButton.clicked.connect(self.edit_process)
        self.runLiveSimulationButton.clicked.connect(self.run_live_simulation)
        self.runAtOnceButton.clicked.connect(self.run_at_once)
        self.algorithmComboBox.currentIndexChanged.connect(self.on_algorithm_changed)
        
        # Set up initial state
        self.update_time_quantum_visibility()
    
    def update_time_quantum_visibility(self):
        # Show time quantum only for Round Robin
        is_round_robin = self.algorithmComboBox.currentText() == "Round Robin"
        self.timeQuantumSpinBox.setEnabled(is_round_robin)
    
    def on_algorithm_changed(self):
        self.update_time_quantum_visibility()
    
    def add_process(self):
        # TODO: Implement process addition logic
        pass
    
    def remove_process(self):
        # TODO: Implement process removal logic
        pass
    
    def edit_process(self):
        # TODO: Implement process editing logic
        pass
    
    def run_live_simulation(self):
        # TODO: Implement live simulation launch
        pass
    
    def run_at_once(self):
        # TODO: Implement at-once simulation launch
        pass