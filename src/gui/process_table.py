from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar, QPushButton, QStyle, QHBoxLayout, QWidget, QLabel, QApplication
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QColor, QBrush, QFont, QIcon, QPainter, QPixmap, QPen, QLinearGradient, QPalette
from typing import List, Dict

from ..models.process import Process

class ProcessTable(QTableWidget):
    """
    A table widget that displays process information.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dark_mode = False # Initial state, will be set by MainWindow
        self.process_colors = {}  # Dictionary to store process colors
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the table UI."""
        # Set column headers and tooltips
        self.setColumnCount(11)
        headers = ["PID", "Name", "Arrival", "Burst", "Priority",
                   "Progress", "Status", "Waiting", "Turnaround",
                   "Response", "Actions"]
        self.setHorizontalHeaderLabels(headers)
        tooltips = ["Process ID", "Process name", "Time when process arrives",
                    "Total CPU burst time", "Process priority (lower is higher)",
                    "Percentage of burst completed", "Current status",
                    "Total waiting time so far", "Turnaround time (completion-arrival)",
                    "Response time (first CPU start)", "Remove process"]
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
        header.setSectionResizeMode(10, QHeaderView.Fixed) # Action column - Fixed width (FIXED: was incorrectly set to 8)
        self.setColumnWidth(10, 105) # Increased width for action column to prevent cropping
        
        # Set relative widths for Name and Progress columns
        # We use fixed widths for the stretch columns instead of setStretchFactor
        # This gives us similar control over their relative sizes
        screen_width = QApplication.desktop().screenGeometry().width()
        table_width = int(screen_width * 0.6)  # Approximate table width (60% of screen)
        
        # Calculate remaining width after fixed columns
        fixed_columns_width = 0
        for col in [0, 2, 3, 4, 6, 7, 8, 9, 10]:
            fixed_columns_width += self.columnWidth(col)
        
        remaining_width = table_width - fixed_columns_width
        name_width = int(remaining_width * 0.4)  # Name gets 40% 
        progress_width = int(remaining_width * 0.6)  # Progress gets 60%
        
        self.setColumnWidth(1, name_width)  # Name column
        self.setColumnWidth(5, progress_width)  # Progress column
        
        # Auto-resize rows to contents but with minimum height for better spacing
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.verticalHeader().setMinimumSectionSize(40) # Increased minimum row height
        self.verticalHeader().setVisible(False) # Hide vertical header (row numbers)
        
        # Make table read-only
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # Enable sorting by clicking headers
        self.setSortingEnabled(True)
        
        # Basic table properties for modern look
        self.setShowGrid(False) # Cleaner look without internal grid lines
        self.setAlternatingRowColors(True) # Use alternate base color from theme
        self.setSelectionMode(QTableWidget.SingleSelection)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setFocusPolicy(Qt.NoFocus) # Prevent cell focus outline
        
        # Set consistent row height
        self.verticalHeader().setDefaultSectionSize(45)
        
        # Set modern styling for the table
        self.setStyleSheet("""
            QTableWidget {
                border: none;
                gridline-color: transparent;
                outline: none;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid rgba(150, 150, 150, 0.1);
            }
            QTableWidget::item:selected {
                background-color: rgba(70, 130, 180, 0.2);
                color: inherit;
            }
            QHeaderView::section {
                padding: 10px;
                background-color: rgba(60, 60, 60, 0.05);
                border: none;
                border-bottom: 2px solid rgba(70, 130, 180, 0.5);
                font-weight: bold;
            }
        """)
        
    def set_dark_mode(self, enabled: bool):
        """
        Enable or disable dark mode and refresh the table display.
        
        Args:
            enabled (bool): True for dark mode, False for light mode
        """
        if self.dark_mode != enabled:
            self.dark_mode = enabled
            
            # Refresh the table if there's data
            # Get current sorting state
            sorting_column = self.horizontalHeader().sortIndicatorSection()
            sorting_order = self.horizontalHeader().sortIndicatorOrder()
            
            # Store processes currently displayed
            processes = []
            current_time = 0
            
            # Find MainWindow and get current processes and time
            parent = self.parent()
            while parent:
                if hasattr(parent, 'simulation') and parent.simulation:
                    current_time = parent.simulation.current_time
                    if hasattr(parent.simulation, 'scheduler'):
                        processes = parent.simulation.scheduler.processes
                    break
                parent = parent.parent()
            
            # Update the table with current processes
            if processes:
                self.update_table(processes, current_time)
            
            # Restore sorting
            self.horizontalHeader().setSortIndicator(sorting_column, sorting_order)
        
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
            
            # Name with color indicator
            name_widget = QWidget()
            name_layout = QHBoxLayout(name_widget)
            name_layout.setContentsMargins(4, 2, 8, 2)
            
            # Create color indicator
            color_indicator = QWidget()
            color_indicator.setFixedSize(16, 16)
            color_indicator.setStyleSheet(f"""
                background-color: {self._get_process_color(process.pid).name()};
                border-radius: 8px;
            """)
            
            # Create name label
            name_label = QLabel(process.name)
            name_label.setStyleSheet("font-weight: normal;")
            
            # Add to layout
            name_layout.addWidget(color_indicator)
            name_layout.addWidget(name_label, 1)  # 1 = stretch
            name_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            
            self.setCellWidget(i, 1, name_widget)
            
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
            
            # Calculate progress percentage
            progress_percent = ((process.burst_time - process.remaining_time) / process.burst_time) * 100
            
            # Determine color based on progress percentage
            # Red (0-33%), Orange (34-66%), Green (67-100%)
            if progress_percent < 33:
                bar_color = "#FF5252" if not self.dark_mode else "#FF7373"  # Red (lighter in dark mode)
            elif progress_percent < 66:
                bar_color = "#FFA726" if not self.dark_mode else "#FFC166"  # Orange (lighter in dark mode)
            else:
                bar_color = "#66BB6A" if not self.dark_mode else "#8EDA91"  # Green (lighter in dark mode)
            
            # Create a custom text label for the progress bar with better visibility
            fraction_text = f"{process.burst_time - process.remaining_time}/{process.burst_time}"
            
            # Set progress bar to not show text - we'll overlay our own text
            progress.setTextVisible(False)
            
            # Enhanced progress bar styling with clear borders
            progress.setStyleSheet(f"""
                QProgressBar {{
                    border: 1.5px solid {'#505050' if self.dark_mode else '#A0A0A0'};
                    border-radius: 7px;
                    background-color: {'#2D2D30' if self.dark_mode else '#FFFFFF'};
                    text-align: center;
                    min-height: 24px;
                    max-height: 24px;
                }}
                QProgressBar::chunk {{
                    background-color: {bar_color};
                    border-radius: 5px;
                    margin: 2px;
                }}
            """)
            
            # Create progress widget with overlaid text
            progress_widget = QWidget()
            progress_layout = QHBoxLayout(progress_widget)
            progress_layout.setContentsMargins(8, 2, 8, 2)
            
            # Add progress bar
            progress_layout.addWidget(progress)
            
            # Create and add an overlaid label for better text visibility
            text_label = QLabel(fraction_text)
            text_label.setAlignment(Qt.AlignCenter)
            
            # Enhanced text label styling for better visibility in both themes
            # Use bright white in dark mode with stronger shadow
            text_color = "#FFFFFF" if self.dark_mode else "black"
            text_shadow = "1px 1px 3px #000000, -1px -1px 3px #000000" if self.dark_mode else "none"
            
            text_label.setStyleSheet(f"""
                font-weight: bold;
                color: {text_color};
                background-color: transparent;
                text-shadow: {text_shadow};
            """)
            
            # Make sure the text label is raised above the progress bar
            text_label.raise_()
            text_label.setAttribute(Qt.WA_TransparentForMouseEvents)
            
            # Set the label to appear over the progress bar
            progress_layout.addWidget(text_label)
            progress_layout.setAlignment(text_label, Qt.AlignCenter)
            
            # Use stacked layout effect by setting negative spacing
            progress_layout.setSpacing(-progress.width())
            
            self.setCellWidget(i, 5, progress_widget)
            
            # Set process status with color coding
            status = self._get_process_status(process, current_time)
            status_item = QTableWidgetItem(status)
            
            # Enhanced color coding based on status with better dark/light mode distinction
            if status == "Running":
                status_item.setForeground(QColor("#4CAF50") if not self.dark_mode else QColor("#8AFF8E"))
            elif status == "Waiting":
                status_item.setForeground(QColor("#FFC107") if not self.dark_mode else QColor("#FFD54F"))
            elif status == "Completed":
                status_item.setForeground(QColor("#2196F3") if not self.dark_mode else QColor("#64B5F6"))
            elif status == "Not Arrived":
                # Make not arrived status more visible in both themes
                status_item.setForeground(QColor("#9E9E9E") if not self.dark_mode else QColor("#BDBDBD"))
            
            status_item.setTextAlignment(Qt.AlignCenter)
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
            
            # Add Remove button with enhanced styling
            remove_btn = QPushButton("Remove")  # Added text label
            trash_icon = self._create_trash_icon(24)  # Slightly smaller icon to fit with text
            remove_btn.setIcon(trash_icon)
            remove_btn.setIconSize(QSize(18, 18))  # Smaller icon size to accommodate text
            remove_btn.setCursor(Qt.PointingHandCursor)
            remove_btn.setToolTip("Remove Process")
            remove_btn.setProperty("pid", process.pid)
            remove_btn.clicked.connect(self.on_remove_clicked)
            remove_btn.setObjectName("remove_table_button")
            
            # Modern style for remove button with text
            remove_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {'rgba(198, 40, 40, 0.1)' if self.dark_mode else 'rgba(211, 47, 47, 0.07)'};
                    color: {'#FF6E6E' if self.dark_mode else '#D32F2F'};
                    border: 1px solid {'rgba(255, 110, 110, 0.4)' if self.dark_mode else 'rgba(211, 47, 47, 0.3)'};
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 12px;
                    min-width: 70px;
                }}
                QPushButton:hover {{
                    background-color: {'rgba(255, 110, 110, 0.2)' if self.dark_mode else 'rgba(211, 47, 47, 0.15)'};
                    border: 1px solid {'rgba(255, 110, 110, 0.6)' if self.dark_mode else 'rgba(211, 47, 47, 0.5)'};
                }}
                QPushButton:pressed {{
                    background-color: {'rgba(255, 110, 110, 0.3)' if self.dark_mode else 'rgba(211, 47, 47, 0.25)'};
                }}
            """)
            
            # Center the button in the cell
            cell_widget = QWidget()
            layout = QHBoxLayout(cell_widget)
            layout.setContentsMargins(3, 0, 3, 0)  # Reduced horizontal margins
            layout.addWidget(remove_btn)
            layout.setAlignment(Qt.AlignCenter)
            self.setCellWidget(i, 10, cell_widget)
            
            # Align text centrally for numerical columns
            for col_idx in [0, 2, 3, 4, 7, 8, 9]:
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
            avg_item.setData(Qt.UserRole, "summary_label")
            self.setItem(avg_row, 0, avg_item)
            
            # Set average values
            for col, val in [(7, avg_wait), (8, avg_turn), (9, avg_resp)]:
                item = QTableWidgetItem(f"{val:.2f}")
                item.setFont(font)
                item.setTextAlignment(Qt.AlignCenter)
                item.setFlags(Qt.ItemIsEnabled)
                item.setData(Qt.UserRole, "summary_value")
                self.setItem(avg_row, col, item)
            # Disable the action button cell in the summary row
            self.setCellWidget(avg_row, 10, None)
            self.setItem(avg_row, 10, QTableWidgetItem(""))
            self.item(avg_row, 10).setFlags(Qt.ItemIsEnabled)
        
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
        
    def _create_trash_icon(self, size=24):
        """Create a custom red trash icon (basket) that's filled. Adapts color based on self.dark_mode."""
        # Define colors - use slightly different shades for dark vs light mode
        primary_color = "#C62828" if self.dark_mode else "#D32F2F"  # Use theme-appropriate red
        highlight_color = "#D32F2F" if self.dark_mode else "#E57373"  # Lighter red for highlights
        
        # Create a pixmap to draw on
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        
        # Create painter
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw the trash can body (main basket)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(primary_color))
        
        # Calculate dimensions for the trash can - explicitly convert to int
        basket_width = int(size * 0.7) # Slightly narrower
        basket_height = int(size * 0.65)
        basket_x = int((size - basket_width) / 2)
        basket_y = int(size * 0.35)  # Start slightly lower
        
        # Draw the main body of the trash can (rectangle with rounded corners)
        painter.drawRoundedRect(basket_x, basket_y, basket_width, basket_height, 2, 2)
        
        # Draw the lid of the trash can - explicitly convert to int
        lid_width = int(basket_width * 1.1) # Slightly wider lid
        lid_height = int(size * 0.12)
        lid_x = int((size - lid_width) / 2)
        lid_y = int(basket_y - lid_height * 0.8) # Position lid closer to body
        
        painter.setBrush(QColor(primary_color)) # Lid same color as body
        painter.drawRoundedRect(lid_x, lid_y, lid_width, lid_height, 1, 1)
        
        # Draw the handle on top of the lid - explicitly convert to int
        handle_width = int(basket_width * 0.3)
        handle_height = int(lid_height * 0.7)
        handle_x = int((size - handle_width) / 2)
        handle_y = int(lid_y - handle_height * 0.7) # Position handle closer
        
        painter.drawRoundedRect(handle_x, handle_y, handle_width, handle_height, 1, 1)
        
        # Draw some lines on the trash can body using highlight color
        painter.setPen(QPen(QColor(highlight_color), 1)) # Use highlight color for lines
        
        # Draw 2 vertical lines - explicitly convert to int
        line1_x = int(basket_x + basket_width / 3)
        line2_x = int(basket_x + (basket_width * 2) / 3)
        
        # Make sure line start/end points are also integers
        line_start_y = basket_y + 3
        line_end_y = basket_y + basket_height - 3
        
        painter.drawLine(line1_x, int(line_start_y), line1_x, int(line_end_y))
        painter.drawLine(line2_x, int(line_start_y), line2_x, int(line_end_y)) # Fixed missing parenthesis
        
        painter.end()
        
        return QIcon(pixmap)
    
    def set_process_colors(self, process_colors):
        """Set the process colors dictionary"""
        self.process_colors = process_colors
        
    def _get_process_color(self, pid):
        """Get the color for a process"""
        if pid in self.process_colors:
            return self.process_colors[pid]
        
        # Default colors if not found
        default_colors = [
            QColor("#FF6347"), QColor("#1E90FF"), QColor("#32CD32"), 
            QColor("#FFD700"), QColor("#8A2BE2"), QColor("#FF7F50")
        ]
        return default_colors[pid % len(default_colors)]