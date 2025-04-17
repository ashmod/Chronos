from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar, QPushButton, QStyle, QHBoxLayout, QWidget
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
        # Set column headers and tooltips
        self.setColumnCount(11)
        headers = ["PID", "Name", "Arrival", "Burst", "Priority",
                   "Progress", "Status", "Waiting", "Turnaround",
                   "Response", "Actions"] # Remove Action header text
        self.setHorizontalHeaderLabels(headers)
        tooltips = ["Process ID", "Process name", "Time when process arrives",
                    "Total CPU burst time", "Process priority (lower is higher)",
                    "Percentage of burst completed", "Current status",
                    "Total waiting time so far", "Turnaround time (completion-arrival)",
                    "Response time (first CPU start)", "Remove process"] # Update tooltip
        for idx, tip in enumerate(tooltips):
            self.horizontalHeaderItem(idx).setToolTip(tip)
        
        # Set font (will be overridden by global style, but good fallback)
        self.setFont(QFont("Segoe UI", 10))
        
        # Auto-resize columns - Adjustments for better spacing
        header = self.horizontalHeader()
        # Clear previous settings if any
        for i in range(self.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.Interactive) # Reset first
            
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents) # PID
        header.setSectionResizeMode(1, QHeaderView.Stretch) # Name - Stretch
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents) # Arrival
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents) # Burst
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents) # Priority
        header.setSectionResizeMode(5, QHeaderView.Stretch) # Progress - Stretch
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents) # Status
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents) # Waiting
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents) # Turnaround
        header.setSectionResizeMode(9, QHeaderView.ResizeToContents) # Response
        header.setSectionResizeMode(10, QHeaderView.ResizeToContents) # Action column
        
        # Auto-resize rows to contents
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.verticalHeader().setVisible(False) # Hide vertical header (row numbers)
        
        # Make table read-only
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        # Enable sorting by clicking headers
        self.setSortingEnabled(True)
        
        # Modern styling (most styling is now handled globally)
        self.setShowGrid(False) # Cleaner look without internal grid lines
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QTableWidget.SingleSelection)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setFocusPolicy(Qt.NoFocus) # Prevent cell focus outline
        
        # Increase row padding visually
        self.setStyleSheet("""
            QTableView::item { 
                padding: 15px 5px; /* Vertical padding for row height */
            }
            QHeaderView::section { 
                padding: 10px 5px; /* Padding for header text */
                min-height: 30px; /* Minimum height for header sections */
            }
        """)
        
    def set_dark_mode(self, enabled: bool):
        """Enable or disable dark mode. Styles are mostly global now."""
        self.dark_mode = enabled
        # Force re-evaluation of styles if needed, though global stylesheet should handle it
        self.style().unpolish(self)
        self.style().polish(self)
        self.update() # Trigger repaint
        
    def update_table(self, processes: List[Process], current_time: int):
        """
        Update the table with the current state of the processes.
        
        Args:
            processes (List[Process]): List of processes to display
            current_time (int): Current simulation time
        """
        self.setSortingEnabled(False) # Disable sorting during update
        self.setRowCount(0)
        
        # Add processes to the table
        for i, process in enumerate(processes):
            self.insertRow(i)
            
            # PID (as integer for sorting)
            pid_item = QTableWidgetItem()
            pid_item.setData(Qt.DisplayRole, process.pid)
            self.setItem(i, 0, pid_item)
            
            # Name
            self.setItem(i, 1, QTableWidgetItem(process.name))
            
            # Arrival Time (as integer)
            arrival_item = QTableWidgetItem()
            arrival_item.setData(Qt.DisplayRole, process.arrival_time)
            self.setItem(i, 2, arrival_item)
            
            # Burst Time (as integer)
            burst_item = QTableWidgetItem()
            burst_item.setData(Qt.DisplayRole, process.burst_time)
            self.setItem(i, 3, burst_item)
            
            # Priority (as integer)
            priority_item = QTableWidgetItem()
            priority_item.setData(Qt.DisplayRole, process.priority)
            self.setItem(i, 4, priority_item)
            
            # Remaining time as progress bar
            progress = QProgressBar()
            progress.setMaximum(process.burst_time)
            progress.setValue(process.burst_time - process.remaining_time)
            progress.setTextVisible(True) # Show percentage text
            progress.setFormat(f"{process.burst_time - process.remaining_time}/{process.burst_time}") # Show fraction
            progress.setAlignment(Qt.AlignCenter)
            progress.setFixedHeight(20) # Slightly taller progress bar
            # Styling moved to global stylesheet for consistency
            self.setCellWidget(i, 5, progress)
            
            # Set process status
            status = self._get_process_status(process, current_time)
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignCenter)
            
            # Status styling moved to global stylesheet for consistency
            # Add a property to the item for the stylesheet to target
            status_item.setData(Qt.UserRole, status) # Store status for styling
                
            self.setItem(i, 6, status_item)
            
            # Metrics columns (as float/int for sorting)
            wait_item = QTableWidgetItem()
            wait_item.setData(Qt.DisplayRole, float(process.waiting_time))
            self.setItem(i, 7, wait_item)
            
            turn_item = QTableWidgetItem()
            turn_val = float(process.turnaround_time) if process.turnaround_time is not None else -1.0
            turn_item.setData(Qt.DisplayRole, turn_val)
            # Display '-' if not completed yet
            turn_item.setText(f"{turn_val:.1f}" if turn_val >= 0 else "-")
            self.setItem(i, 8, turn_item)
            
            resp_item = QTableWidgetItem()
            resp_val = float(process.response_time) if process.response_time is not None else -1.0
            resp_item.setData(Qt.DisplayRole, resp_val)
            # Display '-' if not started yet
            resp_item.setText(f"{resp_val:.1f}" if resp_val >= 0 else "-")
            self.setItem(i, 9, resp_item)
            
            # Add Remove button (icon only) in the Action column
            remove_btn = QPushButton() # No text
            # Get standard trash icon
            trash_icon = self.style().standardIcon(QStyle.SP_TrashIcon)
            remove_btn.setIcon(trash_icon)
            remove_btn.setCursor(Qt.PointingHandCursor) # Add hover cursor
            remove_btn.setToolTip("Remove Process")
            remove_btn.setProperty("pid", process.pid)
            remove_btn.clicked.connect(self.on_remove_clicked)
            # Styling moved to global stylesheet
            remove_btn.setObjectName("remove_table_button") # Set object name for styling
            remove_btn.setMinimumHeight(30) # Set minimum height for the button
            
            # Center the button in the cell
            cell_widget = QWidget()
            layout = QHBoxLayout(cell_widget)
            layout.addWidget(remove_btn)
            layout.setAlignment(Qt.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            self.setCellWidget(i, 10, cell_widget)
            
            # Align text centrally for numerical columns and status
            for col_idx in [0, 2, 3, 4, 6, 7, 8, 9]:
                item = self.item(i, col_idx)
                if item:
                    item.setTextAlignment(Qt.AlignCenter)
        
        # Add summary row for averages
        completed = [p for p in processes if p.completion_time is not None]
        if completed:
            # Calculate averages safely handling None values
            avg_wait = sum(p.waiting_time for p in completed) / len(completed)
            avg_turn = sum(p.turnaround_time for p in completed) / len(completed)
            
            # Handle None values in response_time - only consider processes with a valid response_time
            processes_with_response_time = [p for p in completed if p.response_time is not None]
            avg_resp = sum(p.response_time for p in processes_with_response_time) / len(processes_with_response_time) if processes_with_response_time else 0
            
            avg_row = len(processes)
            self.insertRow(avg_row)
            # Merge first columns for label
            self.setSpan(avg_row, 0, 1, 7) # Span across first 7 columns
            avg_item = QTableWidgetItem("Averages")
            font = avg_item.font()
            font.setBold(True)
            avg_item.setFont(font)
            avg_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter) # Align right
            avg_item.setFlags(Qt.ItemIsEnabled)
            # Add padding to the right of the label
            avg_item.setData(Qt.UserRole, "summary_label") # For styling
            self.setItem(avg_row, 0, avg_item)
            
            # Set average values
            for col, val in [(7, avg_wait), (8, avg_turn), (9, avg_resp)]:
                item = QTableWidgetItem(f"{val:.2f}")
                item.setFont(font)
                item.setTextAlignment(Qt.AlignCenter)
                item.setFlags(Qt.ItemIsEnabled)
                item.setData(Qt.UserRole, "summary_value") # For styling
                self.setItem(avg_row, col, item)
            # Disable the action button cell in the summary row
            self.setCellWidget(avg_row, 10, None)
            self.setItem(avg_row, 10, QTableWidgetItem(""))
            self.item(avg_row, 10).setFlags(Qt.ItemIsEnabled)
            
            # Set specific height for summary row
            self.setRowHeight(avg_row, 35)
        
        self.setSortingEnabled(True) # Re-enable sorting
        
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