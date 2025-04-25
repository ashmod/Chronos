from PyQt5.QtWidgets import QWidget, QHBoxLayout, QSizePolicy, QTableWidgetItem
from PyQt5 import uic
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
        
        # Load the UI
        uic.loadUi(ui_file, self)
        
        self.showMaximized()

        # Initialize UI elements
        self.setup_ui()
        self.run_algorithm()
    
    def setup_ui(self):
        # Create the canvas for the Gantt chart
        self.gantt_canvas = GanttCanvas()

         # Set fixed minimum size for the placeholder to ensure visibility
        self.ganttPlaceHolder.setMinimumSize(800, 400)  # width: 800px, height: 400px
        # Set maximum size to prevent excessive scaling
        self.ganttPlaceHolder.setMaximumHeight(800)  # max height: 800px    
        
        # # Set size policy to maintain aspect ratio
        # self.gantt_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # self.ganttPlaceHolder.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Set stretch factors in the main layout to make them equal
        main_layout = self.verticalLayout
        main_layout.setStretch(0, 1)  # processStatsTable frame
        main_layout.setStretch(1, 1)  # Gantt chart frame
        main_layout.setStretch(2, 0)  # Button frame (no stretch)
        
        # Create a layout for the placeholder frame and add the canvas
        layout = QHBoxLayout(self.ganttPlaceHolder)
        layout.addWidget(self.gantt_canvas)
        self.ganttPlaceHolder.setLayout(layout)

        if "Priority" not in self.simulation.scheduler.name:
            # Hide the priority column if the scheduler is not priority-based
            self.processStatsTable.setColumnHidden(4, True)

        # Connect return button signal
        self.returnToInputSceneButton.clicked.connect(self.return_to_input)

    def return_to_input(self):
        from src.gui.process_input_scene import ProcessInputScene
        self.return_to_input_scene = ProcessInputScene()
        self.return_to_input_scene.show()
        self.close()  
    
    def run_algorithm(self) -> None:
        """" Runs the simluation method till completion without interruptions."""
        
        self.simulation.start()
        status: Generator = self.simulation._run_simulation(False)
        # Handle generator not created case
        if not status:
            raise ValueError("Could not create generator object for the run_simulation().") 
        
        # Loop on the generator object till the simulation is done 
        while not self.simulation.scheduler.all_processes_completed():
            try:
                current_process = next(status)
                self.simulation.processes_timeline.append(current_process)
            except StopIteration:
                break   # Break out of while if you reach method return

        # Update the process table after finishing the simulation
        self.update_process_table()
        # Update Average waiting time and turnaround time labels
        self.averageWaitingTimeTextBox.setText(str(self.simulation.scheduler.get_average_waiting_time()))
        self.averageTurnaroundTimeTextBox.setText(str(self.simulation.scheduler.get_average_turnaround_time()))
        # Update the Gantt chart with the collected process timeline
        self.update_gantt_chart()
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
            self.processStatsTable.setItem(row, 4, QTableWidgetItem(str(process.get_priority())))
            self.processStatsTable.setItem(row, 5, QTableWidgetItem(str(process.get_completion_time())))
            self.processStatsTable.setItem(row, 6, QTableWidgetItem(str(waiting_time)))
            self.processStatsTable.setItem(row, 7, QTableWidgetItem(str(turnaround_time)))
            self.processStatsTable.setItem(row, 8, QTableWidgetItem(str(response_time)))


    def update_gantt_chart(self):
        """
        Update the Gantt chart with process execution timeline
        """
        if not self.simulation.processes_timeline:
            return
            
        # Use the plot_gantt_chart method from our GanttCanvas class
        self.gantt_canvas.plot_gantt_chart(self.simulation.processes_timeline)