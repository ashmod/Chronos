from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QFont
from PyQt5.QtCore import Qt, QRect
from typing import List, Dict, Optional

from ..models.process import Process

class GanttChart(QWidget):
    """
    A widget that displays a Gantt chart for process execution.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize variables
        self.processes: List[Process] = []
        self.current_time = 0
        self.time_scale = 20  # Pixels per time unit
        self.row_height = 40  # Height of each process row
        self.timeline: List[tuple] = []  # List of (process, start_time, end_time) tuples
        self.colors: Dict[int, QColor] = {}  # Dict mapping process IDs to colors
        self.process_colors = [
            QColor(255, 99, 71),   # Tomato
            QColor(30, 144, 255),  # Dodger Blue
            QColor(50, 205, 50),   # Lime Green
            QColor(255, 215, 0),   # Gold
            QColor(138, 43, 226),  # Blue Violet
            QColor(255, 127, 80),  # Coral
            QColor(0, 206, 209),   # Dark Turquoise
            QColor(255, 20, 147),  # Deep Pink
            QColor(0, 100, 0),     # Dark Green
            QColor(255, 69, 0),    # Orange Red
        ]
        self.dark_mode = False
        
        # Setup UI
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the Gantt chart UI."""
        # Set minimum size for the widget
        self.setMinimumHeight(200)
        self.setMinimumWidth(600)
    
    def reset(self):
        """Reset the Gantt chart to its initial state."""
        self.processes = []
        self.current_time = 0
        self.timeline = []
        self.colors = {}
        self.update()  # Trigger a repaint
        
    def update_chart(self, current_process: Optional[Process], current_time: int):
        """
        Update the Gantt chart with the current state of the simulation.
        
        Args:
            current_process (Optional[Process]): The currently executing process, or None if idle
            current_time (int): Current simulation time
        """
        if current_process:
            # Add current process to the processes list if it's not already there
            if current_process not in self.processes:
                self.processes.append(current_process)
                self.colors[current_process.pid] = self._get_color_for_process(current_process.pid)
                
            # Add to timeline if this is a new execution period
            if (not self.timeline or 
                self.timeline[-1][0] != current_process or 
                self.timeline[-1][2] != current_time):
                
                self.timeline.append((current_process, current_time, current_time + 1))
            else:
                # Extend the current execution period
                _, start, _ = self.timeline[-1]
                self.timeline[-1] = (current_process, start, current_time + 1)
        
        self.current_time = current_time
        self.update()  # Trigger a repaint
        
    def set_dark_mode(self, enabled: bool):
        """Enable or disable dark mode."""
        self.dark_mode = enabled
        self.update()
        
    def paintEvent(self, event):
        """
        Paint the Gantt chart.
        
        Args:
            event: The paint event
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background
        background_color = QColor(33, 33, 33) if self.dark_mode else Qt.white
        text_color = Qt.white if self.dark_mode else Qt.black
        grid_color = QColor(70, 70, 70) if self.dark_mode else QColor(200, 200, 200)
        
        painter.fillRect(event.rect(), background_color)
        
        # Draw timeline
        self._draw_timeline(painter, text_color, grid_color)
        
        # Draw process executions
        self._draw_executions(painter, text_color)
        
    def _draw_timeline(self, painter: QPainter, text_color, grid_color):
        """
        Draw the timeline axis.
        
        Args:
            painter (QPainter): The painter to use
            text_color: Color to use for text
            grid_color: Color to use for grid lines
        """
        # Set pen and font for timeline
        painter.setPen(QPen(text_color, 1))
        painter.setFont(QFont("Arial", 9))
        
        # Draw timeline axis
        axis_y = 30
        axis_length = (self.current_time + 5) * self.time_scale
        
        # Ensure minimum width
        self.setMinimumWidth(max(self.minimumWidth(), axis_length + 50))
        
        # Draw horizontal axis
        painter.drawLine(50, axis_y, 50 + axis_length, axis_y)
        
        # Draw time markers and grid lines
        for i in range(self.current_time + 5):
            x = 50 + i * self.time_scale
            
            # Draw vertical grid line
            painter.setPen(QPen(grid_color, 1, Qt.DotLine))
            painter.drawLine(x, axis_y + 5, x, self.height())
            
            # Draw tick mark and time label
            painter.setPen(QPen(text_color, 1))
            painter.drawLine(x, axis_y - 5, x, axis_y + 5)
            painter.drawText(x - 10, axis_y + 20, str(i))
            
    def _draw_executions(self, painter: QPainter, text_color):
        """
        Draw the process execution blocks.
        
        Args:
            painter (QPainter): The painter to use
            text_color: Color to use for text
        """
        # Set font for process names
        painter.setFont(QFont("Arial", 9))
        
        # Track y-position for each process
        process_positions = {}
        next_y = 60
        
        # Draw each execution period
        for process, start, end in self.timeline:
            # Calculate position
            x = 50 + start * self.time_scale
            width = (end - start) * self.time_scale
            
            # Determine y-position for this process
            if process.pid not in process_positions:
                process_positions[process.pid] = next_y
                next_y += self.row_height
                
            y = process_positions[process.pid]
            
            # Draw process name on the left
            painter.setPen(text_color)
            process_name = f"{process.name}"
            painter.drawText(5, y + self.row_height // 2 + 5, process_name)
            
            # Draw execution block
            color = self.colors[process.pid]
            # Make colors slightly darker in dark mode
            if self.dark_mode:
                color = QColor(
                    int(color.red() * 0.9),
                    int(color.green() * 0.9),
                    int(color.blue() * 0.9)
                )
            
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(Qt.black if not self.dark_mode else Qt.white, 1))
            
            # Draw with rounded corners for a modern look
            painter.drawRoundedRect(x, y, width, self.row_height - 10, 5, 5)
            
            # Draw process name in the block
            block_text = process.name
            if width > 40:  # Only show name if there's enough space
                text_rect = QRect(x, y, width, self.row_height - 10)
                painter.drawText(text_rect, Qt.AlignCenter, block_text)
            else:
                # For narrow blocks, just show the pid
                text_rect = QRect(x, y, width, self.row_height - 10)
                painter.drawText(text_rect, Qt.AlignCenter, f"P{process.pid}")
            
        # Update widget height to accommodate all processes
        self.setMinimumHeight(next_y + 20)
        
    def _get_color_for_process(self, pid: int) -> QColor:
        """
        Get a color for a process based on its ID.
        
        Args:
            pid (int): Process ID
            
        Returns:
            QColor: Color for the process
        """
        return self.process_colors[pid % len(self.process_colors)]