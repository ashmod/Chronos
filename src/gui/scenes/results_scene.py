from PyQt5.QtWidgets import (QTableWidget, QTableWidgetItem, QHeaderView, 
                          QPushButton, QVBoxLayout, QHBoxLayout, QLabel, 
                          QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from .base_scene import BaseScene

import csv

class ResultsScene(BaseScene):
    """Scene for displaying detailed simulation results."""
    
    def __init__(self, parent=None):
        self.processes = []
        self.results_table = None
        super().__init__(parent)
        
    def setup_ui(self):
        """Setup the results scene UI."""
        super().setup_ui()
        
        # Add a title
        title = QLabel("Simulation Results")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.layout.addWidget(title)
        
        # Create the results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(8)
        self.results_table.setHorizontalHeaderLabels([
            "Process", "Arrival", "Burst", "Priority", "Completion", 
            "Turnaround", "Waiting", "Response"
        ])
        
        # Format the table
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.results_table.setSortingEnabled(True)
        self.layout.addWidget(self.results_table, 1)
        
        # Add a summary label for statistics
        self.summary_label = QLabel()
        self.summary_label.setAlignment(Qt.AlignCenter)
        self.summary_label.setFont(QFont("Segoe UI", 11))
        self.summary_label.setWordWrap(True)
        self.layout.addWidget(self.summary_label)
        
        # Button controls
        btn_layout = QHBoxLayout()
        
        # Back button (improved)
        self.back_btn = QPushButton("← Back to Simulation")
        self.back_btn.setToolTip("Return to the simulation scene")
        self.back_btn.clicked.connect(lambda: self.switch_scene.emit("simulation"))
        btn_layout.addWidget(self.back_btn)
        
        # Export button
        self.export_btn = QPushButton("Export Results")
        self.export_btn.clicked.connect(self._export_results)
        btn_layout.addWidget(self.export_btn)
        
        # Continue to iterate button
        self.iterate_btn = QPushButton("Continue to iterate?")
        self.iterate_btn.setToolTip("Modify process inputs and run another simulation")
        self.iterate_btn.clicked.connect(lambda: self.switch_scene.emit("process_input"))
        btn_layout.addWidget(self.iterate_btn)
        
        # New simulation button (renamed for clarity)
        self.new_sim_btn = QPushButton("Start New Simulation")
        self.new_sim_btn.setToolTip("Start a new simulation from the beginning")
        self.new_sim_btn.clicked.connect(lambda: self.switch_scene.emit("welcome"))
        btn_layout.addWidget(self.new_sim_btn)
        
        self.layout.addLayout(btn_layout)
    
    def enter_scene(self, data=None):
        """
        Handle entering the scene with result data.
        
        Args:
            data (dict): Dictionary with simulation results containing:
                - processes (list): List of completed Process objects
                - scheduler_name (str): Name of the scheduler used
                - stats (dict): Overall statistics
        """
        if not isinstance(data, dict) or 'processes' not in data:
            return
            
        self.processes = data['processes']
        self.current_scheduler = data.get('scheduler_name', 'Unknown')
        self.current_stats = data.get('stats', {})
        
        # Update the table
        self._update_table()
        
        # Update the summary label
        avg_waiting = self.current_stats.get('avg_waiting', 0)
        avg_turnaround = self.current_stats.get('avg_turnaround', 0)
        avg_response = self.current_stats.get('avg_response', 0)
        cpu_util = self.current_stats.get('cpu_utilization', 0)
        throughput = self.current_stats.get('throughput', 0)
        
        summary_text = (
            f"<b>Scheduler:</b> {self.current_scheduler} | "
            f"<b>CPU Utilization:</b> {cpu_util:.2f}% | "
            f"<b>Throughput:</b> {throughput:.4f} proc/unit time<br>"
            f"<b>Average Waiting Time:</b> {avg_waiting:.2f} | "
            f"<b>Average Turnaround Time:</b> {avg_turnaround:.2f} | "
            f"<b>Average Response Time:</b> {avg_response:.2f}"
        )
        self.summary_label.setText(summary_text)
        
    def _update_table(self):
        """Update the results table with process data."""
        self.results_table.setRowCount(0)
        
        for i, process in enumerate(self.processes):
            self.results_table.insertRow(i)
            
            # Process name/ID
            name_item = QTableWidgetItem(f"{process.name} (P{process.pid})")
            self.results_table.setItem(i, 0, name_item)
            
            # Arrival time
            arrival_item = QTableWidgetItem(str(process.arrival_time))
            self.results_table.setItem(i, 1, arrival_item)
            
            # Burst time
            burst_item = QTableWidgetItem(str(process.burst_time))
            self.results_table.setItem(i, 2, burst_item)
            
            # Priority
            priority_item = QTableWidgetItem(str(process.priority))
            self.results_table.setItem(i, 3, priority_item)
            
            # Completion time
            completion_item = QTableWidgetItem(str(process.completion_time))
            self.results_table.setItem(i, 4, completion_item)
            
            # Turnaround time
            turnaround_item = QTableWidgetItem(f"{process.turnaround_time:.1f}")
            self.results_table.setItem(i, 5, turnaround_item)
            
            # Waiting time
            waiting_item = QTableWidgetItem(f"{process.waiting_time:.1f}")
            self.results_table.setItem(i, 6, waiting_item)
            
            # Response time
            response_time = process.first_run_time - process.arrival_time if process.first_run_time is not None else "-"
            response_item = QTableWidgetItem(f"{response_time:.1f}" if isinstance(response_time, float) else response_time)
            self.results_table.setItem(i, 7, response_item)
            
            # Center-align all cells
            for col in range(self.results_table.columnCount()):
                item = self.results_table.item(i, col)
                if item:
                    item.setTextAlignment(Qt.AlignCenter)
                    
    def _export_results(self):
        """Export results to a CSV file."""
        if not self.processes:
            return
            
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Results", "", "CSV Files (*.csv);;All Files (*)"
        )
        
        if not filename:
            return
        
        # Get the current scheduler name and stats from the scene data
        scheduler_name = getattr(self, 'current_scheduler', 'Unknown')
        stats = getattr(self, 'current_stats', {})
        
        try:
            with open(filename, 'w', newline='') as file:
                writer = csv.writer(file)
                
                # Write export timestamp
                from datetime import datetime
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                writer.writerow(["Export Date", current_time])
                writer.writerow([])  # Empty row for better readability
                
                # Write scheduler details
                writer.writerow(["Scheduling Algorithm", scheduler_name])
                
                # Write summary statistics
                writer.writerow([])  # Empty row for better readability
                writer.writerow(["SUMMARY METRICS"])
                writer.writerow(["Metric", "Value"])
                
                # Add overall metrics with more details
                avg_waiting = stats.get('avg_waiting', 0)
                avg_turnaround = stats.get('avg_turnaround', 0) 
                avg_response = stats.get('avg_response', 0)
                cpu_util = stats.get('cpu_utilization', 0)
                throughput = stats.get('throughput', 0)
                
                writer.writerow(["Average Waiting Time", f"{avg_waiting:.2f} time units"])
                writer.writerow(["Average Turnaround Time", f"{avg_turnaround:.2f} time units"])
                writer.writerow(["Average Response Time", f"{avg_response:.2f} time units"])
                writer.writerow(["CPU Utilization", f"{cpu_util:.2f}%"])
                writer.writerow(["Throughput", f"{throughput:.4f} processes/time unit"])
                
                # Add min/max metrics if available
                if stats.get('min_waiting') is not None:
                    writer.writerow(["Min Waiting Time", f"{stats.get('min_waiting', 0):.2f} time units"])
                if stats.get('max_waiting') is not None:
                    writer.writerow(["Max Waiting Time", f"{stats.get('max_waiting', 0):.2f} time units"])
                if stats.get('min_turnaround') is not None:
                    writer.writerow(["Min Turnaround Time", f"{stats.get('min_turnaround', 0):.2f} time units"])
                if stats.get('max_turnaround') is not None:
                    writer.writerow(["Max Turnaround Time", f"{stats.get('max_turnaround', 0):.2f} time units"])
                if stats.get('min_response') is not None:
                    writer.writerow(["Min Response Time", f"{stats.get('min_response', 0):.2f} time units"])
                if stats.get('max_response') is not None:
                    writer.writerow(["Max Response Time", f"{stats.get('max_response', 0):.2f} time units"])
                
                if 'context_switches' in stats:
                    writer.writerow(["Context Switches", stats['context_switches']])
                
                # Write empty row for better readability
                writer.writerow([])
                
                # Write process data header
                writer.writerow(["PROCESS DETAILS"])
                writer.writerow([
                    "Process", "Arrival", "Burst", "Priority", "Completion",
                    "Turnaround", "Waiting", "Response", "Start Time", "End Time"
                ])
                
                # Write process data
                for process in self.processes:
                    response_time = process.first_run_time - process.arrival_time if process.first_run_time is not None else "-"
                    
                    writer.writerow([
                        f"{process.name} (P{process.pid})",
                        process.arrival_time,
                        process.burst_time,
                        process.priority,
                        process.completion_time,
                        round(process.turnaround_time, 2),
                        round(process.waiting_time, 2),
                        round(response_time, 2) if isinstance(response_time, float) else response_time,
                        process.first_run_time if process.first_run_time is not None else "-",
                        process.completion_time
                    ])
                
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Results successfully exported to {filename}"
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export results: {str(e)}"
            )