from PyQt6.QtWidgets import QWidget, QTableWidgetItem
from PyQt6.QtCore import Qt
from PyQt6 import uic
import os
from src.core.scheduler import Scheduler
from src.core.simulation import Simulation
from src.models.process import Process
from src.algorithms.fcfs import FCFSScheduler
from src.algorithms.sjf_preemptive import SJFPreemptiveScheduler
from src.algorithms.sjf_non_preemptive import SJFNonPreemptiveScheduler
from src.algorithms.priority_preemptive import PriorityPreemptiveScheduler
from src.algorithms.priority_non_preemptive import PriorityNonPreemptiveScheduler
from src.algorithms.round_robin import RoundRobinScheduler

class ProcessInputScene(QWidget):
    def __init__(self):
        super().__init__()
        
        # Initialize UI first so we can access the combo box
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ui_file = os.path.join(current_dir, "PyQtUI", "processInputSceneUI.ui")
        uic.loadUi(ui_file, self)
        
        # Create simulation with initial scheduler
        # initial_scheduler = self._create_scheduler(self.algorithmComboBox.currentText())
        self.simulation = Simulation(None)
        self.next_pid = 1  # Add PID counter
        self.table_contents = []  # Store the processes in the table
        self.editing_row = -1  # Row currently being edited
        self.currently_editing = False  # Flag to check if we are in editing mode
        # Initialize UI elements
        self.setup_ui()

    def setup_ui(self):
        # Set default process name
        self.processNameTextBox.setText(f"Process {self.next_pid}")
        
        # Connect signals
        self.addProcessButton.clicked.connect(self.add_process)
        self.removeProcessButton.clicked.connect(self.remove_process)
        self.editProcessButton.clicked.connect(self.edit_process)
        self.resetTableButton.clicked.connect(self.reset_table)
        self.runLiveSimulationButton.clicked.connect(self.run_live_simulation)
        self.runAtOnceButton.clicked.connect(self.run_at_once)
        self.algorithmComboBox.currentIndexChanged.connect(self.on_algorithm_changed)
        
        # Set up initial state (read algorithm from combo box right away)
        self.on_algorithm_changed()

    def update_time_quantum_visibility(self):
        # Show time quantum only for Round Robin
        if(self.algorithmComboBox.currentText() == "Round Robin"):
            self.timeQuantumSpinBox.setEnabled(True)
        else:
            self.timeQuantumSpinBox.setEnabled(False)

    def update_priority_visibility(self):
        # Show priority only for Priority Scheduling
        if("Priority" in self.algorithmComboBox.currentText()):
            self.prioritySpinBox.setEnabled(True)
        else:
            self.prioritySpinBox.setEnabled(False)
    
    def on_algorithm_changed(self):
        self.update_time_quantum_visibility()
        self.update_priority_visibility()
        # Update scheduler when algorithm changes
        self.simulation.scheduler = self._create_scheduler(self.algorithmComboBox.currentText())
    
    def _create_scheduler(self, algorithm_name: str) -> Scheduler:
        """Create appropriate scheduler based on algorithm name"""
        if "First-Come, First-Served" in algorithm_name:
            return FCFSScheduler()
        elif "Shortest Job First (Preemptive)" in algorithm_name:
            return SJFPreemptiveScheduler()
        elif "Shortest Job First (Non-Preemptive)" in algorithm_name:
            return SJFNonPreemptiveScheduler()
        elif "Priority (Preemptive)" in algorithm_name:
            return PriorityPreemptiveScheduler()
        elif "Priority (Non-Preemptive)" in algorithm_name:
            return PriorityNonPreemptiveScheduler()
        elif "Round Robin" in algorithm_name:
            time_quantum = self.timeQuantumSpinBox.value() if hasattr(self, 'timeQuantumSpinBox') else 2
            return RoundRobinScheduler(time_quantum)
        else:
            return FCFSScheduler()  # Default to FCFS

    def add_process(self):
        # Get values from input fields
        name = self.processNameTextBox.text().strip()
        if not name:  # If name is empty or only whitespace
            name = f"Process {self.next_pid}"
            
        arrival_time = self.arrivalTimeSpinBox.value()
        burst_time = self.burstTimeSpinBox.value()
        priority = self.prioritySpinBox.value()
        
        # Create and add the process to simulation
        process = Process(
            pid=self.next_pid,
            name=name,
            arrival_time=arrival_time,
            burst_time=burst_time,
            priority=priority
        )

        self.table_contents.append(process)
        
        # Update table
        row = self.processTableWidget.rowCount()
        self.processTableWidget.insertRow(row)
        self.processTableWidget.setItem(row, 0, QTableWidgetItem(str(self.next_pid)))
        self.processTableWidget.setItem(row, 1, QTableWidgetItem(name))
        self.processTableWidget.setItem(row, 2, QTableWidgetItem(str(arrival_time)))
        self.processTableWidget.setItem(row, 3, QTableWidgetItem(str(burst_time)))
        self.processTableWidget.setItem(row, 4, QTableWidgetItem(str(priority)))
        
        # Increment PID counter
        self.next_pid += 1
        
        # Update process name text box with next default name
        self.processNameTextBox.setText(f"Process {self.next_pid}")
        
        # Clear other input fields
        self.arrivalTimeSpinBox.setValue(0)
        self.burstTimeSpinBox.setValue(1)
        self.prioritySpinBox.setValue(0)
    
    def remove_process(self):
        # Remove from table
        self.processTableWidget.removeRow(self.processTableWidget.selectedItems()[0].row())

    def edit_process(self):
        # TODO: Implement process editing
        pass

    def reset_table(self):
                self.processTableWidget.setRowCount(0)  # Clear all rows in the table
            
    def run_live_simulation(self):
        # TODO: Implement live simulation launch
        pass
    
    def run_at_once(self):
        # TODO: Implement at-once simulation launch
        pass
