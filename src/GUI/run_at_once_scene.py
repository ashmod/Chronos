from PyQt6.QtWidgets import QWidget, QHBoxLayout, QSizePolicy
from PyQt6 import uic
import os
from .ganttchart import GanttCanvas

class RunAtOnceScene(QWidget):
    def __init__(self):
        super().__init__()
        # Get the directory containing the UI file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ui_file = os.path.join(current_dir, "PyQtUI", "runAtOnceSceneUI.ui")
        
        # Load the UI
        uic.loadUi(ui_file, self)
        
        # Initialize UI elements
        self.setup_ui()
    
    def setup_ui(self):
        # Create the canvas for the Gantt chart
        self.gantt_canvas = GanttCanvas(self)
        
        # # Set equal size policies for both widgets
        # self.frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # self.frame_2.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Set stretch factors in the main layout to make them equal
        main_layout = self.verticalLayout
        main_layout.setStretch(0, 1)  # processStatsTable frame
        main_layout.setStretch(1, 1)  # Gantt chart frame
        main_layout.setStretch(2, 0)  # Button frame (no stretch)
        
        # Create a layout for the placeholder frame and add the canvas
        layout = QHBoxLayout(self.ganttPlaceHolder)
        layout.addWidget(self.gantt_canvas)
        self.ganttPlaceHolder.setLayout(layout)
        
        # # Set minimum heights to ensure they don't get too small
        # self.frame.setMinimumHeight(200)
        # self.frame_2.setMinimumHeight(200)
        
        # Connect return button signal
        self.returnToInputSceneButton.clicked.connect(self.return_to_input)
    
    def return_to_input(self):
        # TODO: Implement return to input scene logic
        pass
    
    def update_gantt_chart(self, processes_timeline):
        """
        Update the Gantt chart with process execution timeline
        Args:
            processes_timeline: List of tuples (time, process_id, process_name)
        """
        # Clear the previous plot
        self.gantt_canvas.axes.clear()
        
        # TODO: Implement Gantt chart plotting logic
        # This will be implemented when we have the process timeline data
        
        # Refresh the canvas
        self.gantt_canvas.draw()