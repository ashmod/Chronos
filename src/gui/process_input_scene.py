from PyQt5.QtWidgets import QWidget, QTableWidgetItem
from PyQt5.QtCore import Qt
from PyQt5 import uic
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
        
        self.showMaximized()

        # Create simulation with initial scheduler
        # initial_scheduler = self._create_scheduler(self.algorithmComboBox.currentText())
        # self.simulation = Simulation(None)
        self.next_pid = 1  # Add PID counter
        # self.table_contents = {}  # Store the processes in the table
        # self.editing_row = -1  # Row currently being edited
        # self.currently_editing = False  # Flag to check if we are in editing mode
        # Initialize UI elements
        self.setup_ui()

    def setup_ui(self):
        # Connect signals
        self.addProcessButton.clicked.connect(self.add_process)
        self.removeProcessButton.clicked.connect(self.remove_process)
        self.editProcessButton.clicked.connect(self.edit_process)
        self.resetTableButton.clicked.connect(self.reset_table)
        self.runLiveSimulationButton.clicked.connect(self.goto_run_live_simulation)
        self.runAtOnceButton.clicked.connect(self.goto_run_at_once)
        self.algorithmComboBox.currentIndexChanged.connect(self.on_algorithm_changed)
        self.importButton.clicked.connect(self.import_processes)
        
        # Set up initial state (read algorithm from combo box right away)
        self.on_algorithm_changed()

        # Set default process name
        self.processNameTextBox.setText(f"Process {self.next_pid}")

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

    def import_processes(self) -> None:
        """ Import processes from a csv file and add them to the table. """
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        import csv

        file_dialog = QFileDialog(self)
        file_path, _ = file_dialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)")
        print(file_path)
        if not file_path:
            print("No file selected.")
            QMessageBox.warning(self, "Warning", "No file selected.")
            return  # User canceled the dialog

        try:
            print("Importing processes from file...")
            with open(file_path, mode='r', newline='') as file:
                csv_reader = csv.reader(file)
                header = next(csv_reader, None)  # Skip the header row if present
                print(header)
                for row in csv_reader:

                    print(row)
                    name = row[0].strip()
                    arrival_time = int(row[1])
                    burst_time = int(row[2])
                    priority = int(row[3]) if len(row) > 3 else 0  # Default priority to 0 if not provided
                    
                    # Update table
                    row_index = self.processTableWidget.rowCount()
                    self.processTableWidget.insertRow(row_index)
                    self.processTableWidget.setItem(row_index, 0, QTableWidgetItem(str(self.next_pid)))
                    self.processTableWidget.setItem(row_index, 1, QTableWidgetItem(name))
                    self.processTableWidget.setItem(row_index, 2, QTableWidgetItem(str(arrival_time)))
                    self.processTableWidget.setItem(row_index, 3, QTableWidgetItem(str(burst_time)))
                    self.processTableWidget.setItem(row_index, 4, QTableWidgetItem(str(priority)))
                    
                    # Increment PID counter
                    self.next_pid += 1

            # Update process name text box with next default name
            self.processNameTextBox.setText(f"Process {self.next_pid}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import processes: {str(e)}")

    def add_process(self):
        # Get values from input fields
        name = self.processNameTextBox.text().strip()
        if not name:  # If name is empty or only whitespace
            name = f"Process {self.next_pid}"
            
        arrival_time = self.arrivalTimeSpinBox.value()
        burst_time = self.burstTimeSpinBox.value()
        priority = self.prioritySpinBox.value()
        
        
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
        pass
    
    def reset_table(self):
        self.processTableWidget.setRowCount(0)  # Clear all rows in the table
        self.next_pid = 1
        self.processNameTextBox.setText(f"Process {self.next_pid}")

    def get_processes_from_table(self):
        processes = []
        for row in range(self.processTableWidget.rowCount()):
            pid = int(self.processTableWidget.item(row, 0).text())
            name = self.processTableWidget.item(row, 1).text()
            arrival_time = int(self.processTableWidget.item(row, 2).text())
            burst_time = int(self.processTableWidget.item(row, 3).text())
            priority = int(self.processTableWidget.item(row, 4).text())
            
            process = Process(pid, name, arrival_time, burst_time, priority)
            processes.append(process)
        
        return processes
    
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
        
    def goto_run_at_once(self):
        scheduler = self._create_scheduler(self.algorithmComboBox.currentText())
        scheduler.add_processes(self.get_processes_from_table())
        # print(*self.get_processes_from_table())
        simulation = Simulation(scheduler)
        from src.gui.run_at_once_scene import RunAtOnceScene
        self.run_at_once_scene = RunAtOnceScene(simulation)
        self.run_at_once_scene.show()
        self.close()  
    
    def goto_run_live_simulation(self):
        scheduler = self._create_scheduler(self.algorithmComboBox.currentText())
        scheduler.add_processes(self.get_processes_from_table())
        # print(*self.get_processes_from_table())
        simulation = Simulation(scheduler)
        from src.gui.run_live_scene import RunLiveScene
        self.run_live_scene = RunLiveScene(simulation,self.next_pid)
        self.run_live_scene.show()
        self.close()

