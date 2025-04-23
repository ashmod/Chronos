from PyQt6.QtWidgets import QWidget, QHBoxLayout, QSizePolicy, QTableWidgetItem
from PyQt6 import uic
from typing import Generator
import os
from src.core.simulation import Simulation
from src.gui.ganttchart import GanttCanvas
from src.models.process import Process

class RunAtOnceScene(QWidget):
    def __init__(self,simulation: Simulation):
        super().__init__()
        self.simulation = simulation
        # Get the directory containing the UI file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ui_file = os.path.join(current_dir, "PyQtUI", "runAtOnceSceneUI.ui")
        
        # Create timestep proces list
        self.processes_timeline = list()
        
        # Load the UI
        uic.loadUi(ui_file, self)
        
        # Initialize UI elements
        self.setup_ui()
        self.run_algorithm()
    
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
        from src.gui.process_input_scene import ProcessInputScene
        self.return_to_input_scene = ProcessInputScene()
        self.return_to_input_scene.show()
        self.close()  
    
    def run_algorithm(self) -> None:
        """" Runs the simluation method till completion without interruptions."""
        
        status: Generator = self.simulation._run_simulation(False)
        # Handle generator not created case
        if not status:
            raise ValueError("Could not create generator object for the run_simulation().") 
        
        # Loop on the generator object till the simulation is done 
        while not self.simulation.scheduler.all_processes_completed():
            print("test world") 
            try:
                current_process = next(status)
                self.processes_timeline.append(current_process)
                print(current_process)
            except StopIteration:
                break   # Break out of while if you reach method return

        # Update the process table after finishing the simulation
        self.update_process_table()
        return



    def update_process_table(self) -> None:
        """" Updates the process stable using simulation result from the run_algorithm()"""

        processes: list[Process] = self.simulation.scheduler.get_processes()
        self.processStatsTable.setRowCount(len(processes))  # Set the number of rows in the table
        
        for row, process in enumerate(processes):
            waiting_time = process.get_waiting_time()
            turnaround_time = process.get_turnaround_time()
            response_time = process.get_response_time()
            
            # Add data to the table
            self.processStatsTable.setItem(row, 0, QTableWidgetItem(str(process.get_pid())))
            self.processStatsTable.setItem(row, 1, QTableWidgetItem(process.get_name()))
            self.processStatsTable.setItem(row, 2, QTableWidgetItem(str(process.get_arrival_time())))
            self.processStatsTable.setItem(row, 3, QTableWidgetItem(str(process.get_burst_time())))
            self.processStatsTable.setItem(row, 4, QTableWidgetItem(str(waiting_time)))
            self.processStatsTable.setItem(row, 5, QTableWidgetItem(str(turnaround_time)))
            self.processStatsTable.setItem(row, 6, QTableWidgetItem(str(response_time)))
        
        # self.update_gantt_chart()

    def update_gantt_chart(self):
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