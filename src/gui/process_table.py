from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QBrush, QFont
from typing import List

from ..models.process import Process

class ProcessTable(QTableWidget):
    """
    A table widget that displays process information.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dark_mode = False
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the table UI."""
        # Set column headers
        self.setColumnCount(8)  # Added an extra column for remove button
        self.setHorizontalHeaderLabels([
            "PID", "Name", "Arrival Time", "Burst Time", 
            "Priority", "Remaining Time", "Status", "Action"
        ])
        
        # Set font
        self.setFont(QFont("Arial", 9))
        
        # Auto-resize columns to contents
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Auto-resize rows to contents
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        
        # Make table read-only
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # Modern styling
        self.setShowGrid(True)
        self.setGridStyle(Qt.SolidLine)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QTableWidget.SingleSelection)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        
    def set_dark_mode(self, enabled: bool):
        """Enable or disable dark mode."""
        self.dark_mode = enabled
        
        if enabled:
            # Dark mode colors
            self.setStyleSheet("""
                QTableWidget {
                    background-color: #212121;
                    color: #FFFFFF;
                    gridline-color: #444444;
                    alternate-background-color: #2A2A2A;
                }
                QHeaderView::section {
                    background-color: #2A2A2A;
                    color: #FFFFFF;
                    padding: 5px;
                    border: 1px solid #444444;
                }
                QTableCornerButton::section {
                    background-color: #2A2A2A;
                    border: 1px solid #444444;
                }
            """)
        else:
            # Light mode colors
            self.setStyleSheet("""
                QTableWidget {
                    background-color: #FFFFFF;
                    color: #000000;
                    gridline-color: #DDDDDD;
                    alternate-background-color: #F5F5F5;
                }
                QHeaderView::section {
                    background-color: #F5F5F5;
                    color: #000000;
                    padding: 5px;
                    border: 1px solid #DDDDDD;
                }
                QTableCornerButton::section {
                    background-color: #F5F5F5;
                    border: 1px solid #DDDDDD;
                }
            """)
        
        # Refresh the table
        self.update()
        
    def update_table(self, processes: List[Process], current_time: int):
        """
        Update the table with the current state of the processes.
        
        Args:
            processes (List[Process]): List of processes to display
            current_time (int): Current simulation time
        """
        # Clear existing rows
        self.setRowCount(0)
        
        # Add processes to the table
        for i, process in enumerate(processes):
            self.insertRow(i)
            
            # Set process information
            self.setItem(i, 0, QTableWidgetItem(str(process.pid)))
            self.setItem(i, 1, QTableWidgetItem(process.name))
            self.setItem(i, 2, QTableWidgetItem(str(process.arrival_time)))
            self.setItem(i, 3, QTableWidgetItem(str(process.burst_time)))
            self.setItem(i, 4, QTableWidgetItem(str(process.priority)))
            self.setItem(i, 5, QTableWidgetItem(str(process.remaining_time)))
            
            # Set process status
            status = self._get_process_status(process, current_time)
            status_item = QTableWidgetItem(status)
            
            # Set status color - adjust colors based on dark mode
            if self.dark_mode:
                if status == "Running":
                    status_item.setBackground(QBrush(QColor(40, 167, 69)))  # Dark green
                    status_item.setForeground(QBrush(Qt.white))
                elif status == "Completed":
                    status_item.setBackground(QBrush(QColor(52, 58, 64)))   # Dark gray
                    status_item.setForeground(QBrush(Qt.white))
                elif status == "Waiting":
                    status_item.setBackground(QBrush(QColor(255, 193, 7)))  # Amber
                    status_item.setForeground(QBrush(Qt.black))
                elif status == "Not Arrived":
                    status_item.setBackground(QBrush(QColor(73, 80, 87)))   # Medium gray
                    status_item.setForeground(QBrush(Qt.white))
            else:
                if status == "Running":
                    status_item.setBackground(QBrush(QColor(40, 167, 69)))  # Green
                    status_item.setForeground(QBrush(Qt.white))
                elif status == "Completed":
                    status_item.setBackground(QBrush(QColor(108, 117, 125)))  # Gray
                    status_item.setForeground(QBrush(Qt.white))
                elif status == "Waiting":
                    status_item.setBackground(QBrush(QColor(255, 193, 7)))  # Yellow
                    status_item.setForeground(QBrush(Qt.black))
                elif status == "Not Arrived":
                    status_item.setBackground(QBrush(QColor(173, 181, 189)))  # Light gray
                    status_item.setForeground(QBrush(Qt.black))
                
            self.setItem(i, 6, status_item)
            
            # Add Remove button in the Action column
            from PyQt5.QtWidgets import QPushButton
            remove_btn = QPushButton("Remove")
            remove_btn.setProperty("row", i)
            remove_btn.setProperty("pid", process.pid)
            remove_btn.clicked.connect(self.on_remove_clicked)
            self.setCellWidget(i, 7, remove_btn)
            
    def on_remove_clicked(self):
        """Handle remove button click"""
        # Get the sender button
        button = self.sender()
        pid = button.property("pid")
        
        # Signal to parent that a process should be removed
        # This will be connected in MainWindow
        if hasattr(self, "remove_process_callback") and self.remove_process_callback is not None:
            self.remove_process_callback(pid)
            
    def set_remove_callback(self, callback):
        """Set the callback function for removing a process"""
        self.remove_process_callback = callback
        
    def _get_process_status(self, process: Process, current_time: int) -> str:
        """
        Get the status of a process.
        
        Args:
            process (Process): The process to check
            current_time (int): Current simulation time
            
        Returns:
            str: Status of the process ("Not Arrived", "Waiting", "Running", or "Completed")
        """
        if process.is_completed():
            return "Completed"
        elif process.arrival_time > current_time:
            return "Not Arrived"
        elif (process.execution_history and 
              process.execution_history[-1][0] <= current_time < process.execution_history[-1][1]):
            return "Running"
        else:
            return "Waiting"