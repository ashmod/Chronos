from PyQt5.QtWidgets import (QSplitter, QFileDialog, QMessageBox, 
                           QHBoxLayout, QPushButton)
from PyQt5.QtCore import Qt, pyqtSignal

from .base_scene import BaseScene
from ..process_control_widget import ProcessControlWidget
from ..process_table import ProcessTable
from ...models.process import Process

import csv
import os

class ProcessInputScene(BaseScene):
    """Scene for adding and managing processes."""
    
    # Signal when user is ready to proceed to simulation
    proceed_with_processes = pyqtSignal(list)  # list of Process objects
    
    def __init__(self, parent=None):
        self.processes = []
        self.process_table = None
        self.process_control = None
        self.next_pid = 1  # Track the next process ID
        super().__init__(parent)
        
    def setup_ui(self):
        """Setup the process input scene UI."""
        super().setup_ui()
        
        # Main splitter
        self.splitter = QSplitter(Qt.Horizontal)
        
        # Process control on the left - specifically for pre-simulation (is_runtime=False)
        self.process_control = ProcessControlWidget(is_runtime=False)
        self.splitter.addWidget(self.process_control)
        
        # Process table on the right
        self.process_table = ProcessTable()
        self.splitter.addWidget(self.process_table)
        
        # Set initial sizes
        self.splitter.setSizes([400, 600])
        
        # Add splitter to layout
        self.layout.addWidget(self.splitter, 1)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        
        # Back button
        self.back_button = QPushButton("Back")
        self.back_button.clicked.connect(lambda: self.switch_scene.emit("welcome"))
        nav_layout.addWidget(self.back_button)
        
        nav_layout.addStretch()
        
        # Next button
        self.next_button = QPushButton("Continue to Simulation")
        self.next_button.clicked.connect(self._on_continue)
        self.next_button.setEnabled(False)  # Disabled until processes are added
        nav_layout.addWidget(self.next_button)
        
        self.layout.addLayout(nav_layout)
        
        # Connect signals
        self.process_control.add_process_button.clicked.connect(self._add_process)
        self.process_control.remove_all_button.clicked.connect(self._remove_all_processes)
        self.process_control.import_button.clicked.connect(self._import_processes)
        self.process_control.export_button.clicked.connect(self._export_processes)
        
    def enter_scene(self, data=None):
        """Handle scene entry, potentially with data."""
        if data == "load":
            # Automatically open file dialog when entering with load flag
            self._import_processes()
        elif data == "example":
            # Load example processes
            self._load_example_processes()
            
    def _add_process(self):
        """Add a new process from the form inputs."""
        process = Process(
            pid=self.next_pid,  # Assign the next available process ID
            name=self.process_control.process_name_input.text(),
            arrival_time=self.process_control.get_arrival_time(),  # Use new helper method
            burst_time=self.process_control.burst_time_spinbox.value(),
            priority=self.process_control.priority_spinbox.value()
        )
        
        # Increment the process ID counter
        self.next_pid += 1
        
        # Add to the process list
        self.processes.append(process)
        
        # Update the table
        self._update_process_table()
        
        # Generate next process name
        self.process_control.next_process_name()
        
        # Enable next button if we have processes
        self.next_button.setEnabled(len(self.processes) > 0)
        
    def _remove_process(self, pid):
        """Remove a process by its ID."""
        self.processes = [p for p in self.processes if p.pid != pid]
        self._update_process_table()
        
        # Update next button state
        self.next_button.setEnabled(len(self.processes) > 0)
        
    def _remove_all_processes(self):
        """Remove all processes."""
        if not self.processes:
            return
            
        reply = QMessageBox.question(
            self, 
            "Confirm Removal",
            "Are you sure you want to remove all processes?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.processes = []
            self._update_process_table()
            self.next_button.setEnabled(False)
            # Reset the process ID counter
            self.next_pid = 1
            
    def _reset(self):
        """Reset the process counter and form."""
        self.process_control.reset_count()
        
    def _update_process_table(self):
        """Update the process table with current processes."""
        # The ProcessTable class handles clearing processes within update_table
        # so we don't need a separate clear_processes call
        self.process_table.update_table(self.processes, 0)
            
        # Set up removal callback
        self.process_table.set_remove_callback(self._remove_process)
        
    def _on_continue(self):
        """Handle continue button click."""
        # Emit signal with current processes
        self.proceed_with_processes.emit(self.processes)
        
        # Switch to simulation scene
        self.switch_scene.emit("simulation")
        
    def _import_processes(self):
        """Import processes from a CSV file."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Import Processes", "", "CSV Files (*.csv);;All Files (*)"
        )
        
        if not filename:
            return
            
        try:
            with open(filename, 'r') as file:
                reader = csv.reader(file)
                # Skip header row if it exists
                header = next(reader, None)
                if header and not any(h.isdigit() for h in header):
                    # This was likely a header row, continue with data
                    pass
                else:
                    # This was likely data, rewind the file and read again
                    file.seek(0)
                    reader = csv.reader(file)
                
                # Clear current processes
                self.processes = []
                # Reset the process ID counter
                self.next_pid = 1
                
                # Read processes
                for row in reader:
                    if len(row) >= 4:
                        try:
                            name = row[0]
                            arrival_time = int(row[1])
                            burst_time = int(row[2])
                            priority = int(row[3])
                            
                            process = Process(
                                pid=self.next_pid,  # Assign the next available process ID
                                name=name,
                                arrival_time=arrival_time,
                                burst_time=burst_time,
                                priority=priority
                            )
                            self.processes.append(process)
                            self.next_pid += 1  # Increment the process ID counter
                        except ValueError:
                            # Skip rows that can't be parsed properly
                            continue
                
                # Update the table
                self._update_process_table()
                
                # Enable next button if we imported any processes
                self.next_button.setEnabled(len(self.processes) > 0)
                
                # Reset process counter for future additions
                self.process_control.process_count = len(self.processes)
                self.process_control.next_process_name()
                
                QMessageBox.information(
                    self, 
                    "Import Successful", 
                    f"Successfully imported {len(self.processes)} processes."
                )
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Import Failed", 
                f"Failed to import processes: {str(e)}"
            )
            
    def _export_processes(self):
        """Export processes to a CSV file."""
        if not self.processes:
            QMessageBox.warning(
                self, 
                "No Processes", 
                "There are no processes to export."
            )
            return
            
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Processes", "", "CSV Files (*.csv);;All Files (*)"
        )
        
        if not filename:
            return
            
        try:
            with open(filename, 'w', newline='') as file:
                writer = csv.writer(file)
                # Write header
                writer.writerow(["Name", "Arrival Time", "Burst Time", "Priority"])
                
                # Write processes
                for process in self.processes:
                    writer.writerow([
                        process.name, 
                        process.arrival_time, 
                        process.burst_time, 
                        process.priority
                    ])
                    
            QMessageBox.information(
                self, 
                "Export Successful", 
                f"Successfully exported {len(self.processes)} processes to {filename}."
            )
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Export Failed", 
                f"Failed to export processes: {str(e)}"
            )
            
    def _load_example_processes(self):
        """Load example processes."""
        # Try to load from example_processes.csv in project root
        example_path = os.path.join(os.getcwd(), "example_processes.csv")
        
        if os.path.exists(example_path):
            try:
                with open(example_path, 'r') as file:
                    reader = csv.reader(file)
                    # Skip header if exists
                    header = next(reader, None)
                    if header and not any(h.isdigit() for h in header):
                        # This was a header, continue
                        pass
                    else:
                        # This was likely data, rewind
                        file.seek(0)
                        reader = csv.reader(file)
                    
                    # Clear current processes
                    self.processes = []
                    # Reset the process ID counter
                    self.next_pid = 1
                    
                    # Read processes
                    for row in reader:
                        if len(row) >= 4:
                            try:
                                name = row[0]
                                arrival_time = int(row[1])
                                burst_time = int(row[2])
                                priority = int(row[3])
                                
                                process = Process(
                                    pid=self.next_pid,  # Assign the next available process ID
                                    name=name,
                                    arrival_time=arrival_time,
                                    burst_time=burst_time,
                                    priority=priority
                                )
                                self.processes.append(process)
                                self.next_pid += 1  # Increment the process ID counter
                            except ValueError:
                                continue
                    
                    # Update the table
                    self._update_process_table()
                    
                    # Enable next button if we imported any processes
                    self.next_button.setEnabled(len(self.processes) > 0)
                    
                    # Reset process counter
                    self.process_control.process_count = len(self.processes)
                    self.process_control.next_process_name()
                    
                    return
            except Exception:
                pass
        
        # If loading from file failed, use hardcoded examples
        self.processes = [
            Process(pid=1, name="Process A", arrival_time=0, burst_time=5, priority=3),
            Process(pid=2, name="Process B", arrival_time=1, burst_time=9, priority=1),
            Process(pid=3, name="Process C", arrival_time=2, burst_time=6, priority=4),
            Process(pid=4, name="Process D", arrival_time=3, burst_time=3, priority=2),
            Process(pid=5, name="Process E", arrival_time=4, burst_time=8, priority=5)
        ]
        
        # Update the next_pid for future additions
        self.next_pid = 6
        
        # Update the table
        self._update_process_table()
        
        # Enable next button
        self.next_button.setEnabled(True)
        
        # Reset process counter
        self.process_control.process_count = len(self.processes)
        self.process_control.next_process_name()