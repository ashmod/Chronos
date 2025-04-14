from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QSizePolicy, QMenu
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QFont, QFontMetrics, QPainterPath, QLinearGradient
from PyQt5.QtCore import Qt, QRect, QPointF, QRectF, pyqtSignal
from typing import List, Dict, Optional, Tuple
import math

from ..models.process import Process

class GanttChart(QWidget):
    """
    An enhanced widget that displays a Gantt chart for process execution
    with improved time axis scaling and visualization.
    """
    
    # Signal emitted when user clicks on a process block
    process_clicked = pyqtSignal(int)  # pid of clicked process
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize variables
        self.processes: List[Process] = []
        self.current_time = 0
        self.max_time_displayed = 20  # Initial maximum time to display
        self.time_scale = 40  # Pixels per time unit - increased for better visibility
        self.row_height = 70  # Height of each process row - increased from 45 to 70
        self.header_height = 60  # Height of the timeline header - increased from 50 to 60
        self.left_margin = 180  # Width of the area for process names - increased from 150 to 180
        self.timeline: List[Tuple[Process, int, int]] = []  # List of (process, start_time, end_time) tuples
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
        self.dark_mode = True  # Default to dark mode
        self.highlighted_pid = None  # Currently highlighted process
        self.time_offset = 0  # Initialize the time offset to track the first process start time
        
        # Setup UI
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the Gantt chart UI."""
        # Set minimum size for the widget
        self.setMinimumHeight(300)
        self.setMinimumWidth(800)
        
        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)
        
        # Set the focus policy to accept keyboard events
        self.setFocusPolicy(Qt.StrongFocus)
        
        # Set size policy to allow the widget to expand
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    
    def reset(self):
        """Reset the Gantt chart to its initial state."""
        self.processes = []
        self.current_time = 0
        self.timeline = []
        self.colors = {}
        self.highlighted_pid = None
        self.max_time_displayed = 20
        self.time_offset = 0  # Reset the time offset
        self.update()  # Trigger a repaint
        
    def update_chart(self, current_process: Optional[Process], current_time: int):
        """
        Update the Gantt chart with the current state of the simulation.
        
        Args:
            current_process (Optional[Process]): The currently executing process, or None if idle
            current_time (int): Current simulation time
        """
        # If this is the first process execution, record the start time as our offset
        # This ensures that the first process always starts at "visual time 0"
        if current_process and not self.timeline:
            self.time_offset = current_time
            
        # Adjust time by the offset to ensure first process starts at 0
        adjusted_time = current_time - self.time_offset
        
        if current_process:
            # Add current process to the processes list if it's not already there
            if current_process not in self.processes:
                self.processes.append(current_process)
                self.colors[current_process.pid] = self._get_color_for_process(current_process.pid)
                
            # Add to timeline if this is a new execution period
            if (not self.timeline or 
                self.timeline[-1][0] != current_process or 
                self.timeline[-1][2] != adjusted_time):
                
                self.timeline.append((current_process, adjusted_time, adjusted_time + 1))
            else:
                # Extend the current execution period
                _, start, _ = self.timeline[-1]
                self.timeline[-1] = (current_process, start, adjusted_time + 1)
        
        self.current_time = adjusted_time
        
        # Automatically adjust displayed time range if needed
        self.max_time_displayed = max(self.max_time_displayed, adjusted_time + 5)
        
        # Keep time scale constant regardless of time length
        # This addresses the requirement to show sec by sec and not zoom out
        self.time_scale = 40
        
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
        background_color = QColor(28, 28, 30) if self.dark_mode else QColor(248, 248, 250)
        text_color = QColor(240, 240, 240) if self.dark_mode else QColor(20, 20, 20)
        grid_color = QColor(70, 70, 75) if self.dark_mode else QColor(220, 220, 225)
        header_color = QColor(40, 40, 45) if self.dark_mode else QColor(230, 230, 235)
        
        painter.fillRect(event.rect(), background_color)
        
        # Draw header background with subtle gradient
        if self.dark_mode:
            grad = QLinearGradient(0, 0, 0, self.header_height)
            grad.setColorAt(0, QColor(45, 45, 50))
            grad.setColorAt(1, QColor(35, 35, 40))
            painter.fillRect(0, 0, self.width(), self.header_height, QBrush(grad))
        else:
            grad = QLinearGradient(0, 0, 0, self.header_height)
            grad.setColorAt(0, QColor(240, 240, 245))
            grad.setColorAt(1, QColor(225, 225, 230))
            painter.fillRect(0, 0, self.width(), self.header_height, QBrush(grad))
        
        # Draw process names column background with gradient
        if self.dark_mode:
            sidebar_gradient = QLinearGradient(0, 0, self.left_margin, 0)
            sidebar_gradient.setColorAt(0, QColor(45, 45, 50))
            sidebar_gradient.setColorAt(1, QColor(40, 40, 45))
            painter.fillRect(0, 0, self.left_margin, self.height(), QBrush(sidebar_gradient))
        else:
            sidebar_gradient = QLinearGradient(0, 0, self.left_margin, 0)
            sidebar_gradient.setColorAt(0, QColor(235, 235, 240))
            sidebar_gradient.setColorAt(1, QColor(225, 225, 230))
            painter.fillRect(0, 0, self.left_margin, self.height(), QBrush(sidebar_gradient))
        
        # Draw grid
        self._draw_grid(painter, grid_color)
        
        # Draw timeline
        self._draw_timeline(painter, text_color)
        
        # Draw process labels
        self._draw_process_labels(painter, text_color)
        
        # Draw process executions
        self._draw_executions(painter, text_color)
        
    def _draw_grid(self, painter: QPainter, grid_color: QColor):
        """
        Draw the grid for the Gantt chart.
        
        Args:
            painter (QPainter): The painter to use
            grid_color (QColor): Color to use for grid lines
        """
        # Set pen for grid lines
        grid_pen = QPen(grid_color, 1, Qt.DotLine)
        painter.setPen(grid_pen)
        
        # Draw vertical grid lines (time markers)
        time_step = self._calculate_time_step()
        for i in range(0, self.max_time_displayed + time_step + 1, time_step):  # Start from 0
            x = self.left_margin + i * self.time_scale  # Using 0-based timeline
            
            # Skip if outside the visible area
            if x < self.left_margin:
                continue
                
            # Draw vertical grid line
            painter.drawLine(x, self.header_height, x, self.height())
            
        # Draw horizontal grid lines (process boundaries)
        for i, process in enumerate(self.processes):
            y = self.header_height + (i + 1) * self.row_height
            painter.drawLine(0, y, self.width(), y)
            
    def _calculate_time_step(self) -> int:
        """
        Calculate the appropriate time step for the timeline based on the scale.
        Returns the step size for timeline markers.
        
        Always returns 1 to ensure second-by-second timeline
        """
        # Always use a step of 1 for sec-by-sec timeline as requested
        return 1
            
    def _draw_timeline(self, painter: QPainter, text_color: QColor):
        """
        Draw the timeline axis.
        
        Args:
            painter (QPainter): The painter to use
            text_color (QColor): Color to use for text
        """
        # Set pen and font for timeline
        painter.setPen(QPen(text_color, 1))
        painter.setFont(QFont("Arial", 10))  # Increased font size from 9 to 10
        
        # Draw timeline axis
        axis_y = self.header_height - 15  # Adjusted to accommodate taller header
        axis_pen = QPen(text_color, 2)  # Thicker line for better visibility
        painter.setPen(axis_pen)
        painter.drawLine(self.left_margin, axis_y, self.width() - 10, axis_y)
        
        # Draw time markers and labels (starting from 0)
        time_step = self._calculate_time_step()  # Always 1 for second-by-second timeline
        
        # Calculate how many markers to draw
        for i in range(0, self.max_time_displayed + time_step + 1, time_step):
            x = self.left_margin + i * self.time_scale
            
            # Draw tick mark - taller for better visibility
            if i % 5 == 0:  # Larger ticks for multiples of 5
                painter.setPen(QPen(text_color, 2))  # Thicker line for better visibility
                painter.drawLine(x, axis_y - 8, x, axis_y + 8)
                
                # Draw time label with larger font for multiples of 5
                painter.setFont(QFont("Arial", 11, QFont.Bold))
                label_rect = QRect(int(x - 20), 10, 40, 30)
                painter.drawText(label_rect, Qt.AlignCenter, str(i))
            else:
                painter.setPen(QPen(text_color, 1))
                painter.drawLine(x, axis_y - 5, x, axis_y + 5)
                
                # Draw time label for regular ticks with smaller font
                painter.setFont(QFont("Arial", 9))
                label_rect = QRect(int(x - 15), 15, 30, 20)
                painter.drawText(label_rect, Qt.AlignCenter, str(i))
            
        # Draw timeline title
        title_rect = QRect(int(self.width() / 2 - 100), 5, 200, 30)
        painter.setFont(QFont("Arial", 12, QFont.Bold))  # Larger font for title
        
        # Apply a nice color to the title
        if self.dark_mode:
            painter.setPen(QColor(72, 161, 255))  # A nice blue for dark mode
        else:
            painter.setPen(QColor(25, 118, 210))  # A nice blue for light mode
            
        painter.drawText(title_rect, Qt.AlignCenter, "Timeline (seconds)")
        
    def _draw_process_labels(self, painter: QPainter, text_color: QColor):
        """
        Draw the process names on the left side.
        
        Args:
            painter (QPainter): The painter to use
            text_color (QColor): Color to use for text
        """
        # Set font for process names
        painter.setFont(QFont("Arial", 10))  # Increased from 9 to 10
        painter.setPen(text_color)
        
        # Draw column header
        painter.setFont(QFont("Arial", 12, QFont.Bold))  # Increased from 10 to 12
        
        # Apply a nice color to the header
        if self.dark_mode:
            painter.setPen(QColor(72, 161, 255))  # A nice blue for dark mode
        else:
            painter.setPen(QColor(25, 118, 210))  # A nice blue for light mode
            
        painter.drawText(10, 5, self.left_margin - 20, 30, Qt.AlignLeft | Qt.AlignVCenter, "Process")
        
        # Reset text color for process names
        painter.setPen(text_color)
        
        # Draw each process name
        painter.setFont(QFont("Arial", 10))  # Increased from 9 to 10
        for i, process in enumerate(self.processes):
            y = self.header_height + i * self.row_height
            
            # Draw process background
            if i % 2 == 0:  # Alternating row backgrounds
                if self.dark_mode:
                    painter.fillRect(0, y, self.left_margin, self.row_height, QColor(45, 45, 50, 120))
                else:
                    painter.fillRect(0, y, self.left_margin, self.row_height, QColor(240, 240, 245, 120))
            
            # Draw process color indicator with rounded corners - larger indicator
            color_rect = QRect(10, y + self.row_height // 2 - 12, 24, 24)  # Increased from 16x16 to 24x24
            path = QPainterPath()
            path.addRoundedRect(QRectF(color_rect), 4, 4)  # Increased corner radius
            painter.fillPath(path, self.colors[process.pid])
            
            # Draw border around color indicator
            painter.setPen(QPen(Qt.black if not self.dark_mode else Qt.white, 1))
            painter.drawPath(path)
            
            # Draw process name and ID with more details
            painter.setPen(text_color)
            process_text = f"{process.name} (ID: {process.pid})"
            process_details = f"Burst: {process.burst_time}, Priority: {process.priority}"
            
            # Draw main process text
            painter.setFont(QFont("Arial", 10, QFont.Bold))
            painter.drawText(40, y + 5, self.left_margin - 50, self.row_height // 2 - 5, 
                         Qt.AlignLeft | Qt.AlignVCenter, process_text)
                         
            # Draw process details in smaller font
            painter.setFont(QFont("Arial", 9))
            painter.drawText(40, y + self.row_height // 2, self.left_margin - 50, self.row_height // 2 - 5, 
                         Qt.AlignLeft | Qt.AlignVCenter, process_details)
            
    def _draw_executions(self, painter: QPainter, text_color: QColor):
        """
        Draw the process execution blocks.
        
        Args:
            painter (QPainter): The painter to use
            text_color (QColor): Color to use for text
        """
        # Set font for block text
        painter.setFont(QFont("Arial", 10))  # Increased from 9 to 10
        
        # Create a mapping from process ID to row index
        process_indices = {process.pid: i for i, process in enumerate(self.processes)}
        
        # Draw each execution period
        for process, start, end in self.timeline:
            # Check if process is in our list (it might have been removed)
            if process.pid not in process_indices:
                continue
                
            # Calculate position
            x = self.left_margin + start * self.time_scale
            width = (end - start) * self.time_scale
            i = process_indices[process.pid]
            y = self.header_height + i * self.row_height + 10  # Added more padding (5 to 10)
            height = self.row_height - 20  # Increased padding for taller blocks
            
            # Get the color for this process
            color = self.colors[process.pid]
            
            # Adjust color if this process is highlighted
            if self.highlighted_pid == process.pid:
                # Make color brighter for highlight
                color = QColor(
                    min(255, int(color.red() * 1.3)),
                    min(255, int(color.green() * 1.3)),
                    min(255, int(color.blue() * 1.3))
                )
            elif self.dark_mode:
                # Make colors slightly darker in dark mode
                color = QColor(
                    int(color.red() * 0.9),
                    int(color.green() * 0.9),
                    int(color.blue() * 0.9)
                )
            
            # Create a path for rounded rectangle
            path = QPainterPath()
            path.addRoundedRect(QRectF(x, y, width, height), 8, 8)  # Increased corner radius from 5 to 8
            
            # Create a gradient for the block
            gradient = QLinearGradient(x, y, x, y + height)
            gradient.setColorAt(0, color.lighter(115))  # Slightly brighter top
            gradient.setColorAt(1, color.darker(115))   # Slightly darker bottom
            
            # Fill the block with gradient
            painter.fillPath(path, QBrush(gradient))
            
            # Draw border with soft shadow effect
            if self.dark_mode:
                # Shadow in dark mode
                shadow_path = QPainterPath()
                shadow_path.addRoundedRect(QRectF(x + 2, y + 2, width, height), 8, 8)  # Increased shadow offset
                painter.fillPath(shadow_path, QColor(0, 0, 0, 50))  # Increased shadow opacity
                
                # Border
                painter.setPen(QPen(color.darker(130), 1.5))  # Thicker border
            else:
                # Shadow in light mode
                shadow_path = QPainterPath()
                shadow_path.addRoundedRect(QRectF(x + 2, y + 2, width, height), 8, 8)
                painter.fillPath(shadow_path, QColor(0, 0, 0, 30))
                
                # Border
                painter.setPen(QPen(color.darker(130), 1.5))  # Thicker border
            
            painter.drawPath(path)
            
            # Draw text in the block - larger font
            if width > 30:  # Only show text if there's enough space
                process_text = f"{process.name}"
                # Add time info if there's more space
                if width > 60:
                    process_text += f" ({start}-{end})"
                    
                text_rect = QRect(int(x + 5), int(y), int(width - 10), int(height))
                painter.setPen(QPen(Qt.black if color.lightness() > 128 else Qt.white, 1))
                painter.setFont(QFont("Arial", 11, QFont.Bold))  # Larger, bold font
                painter.drawText(text_rect, Qt.AlignCenter, process_text)
            else:
                # For narrow blocks, just show a simple identifier
                painter.setPen(QPen(Qt.black if color.lightness() > 128 else Qt.white, 1))
                painter.setFont(QFont("Arial", 10, QFont.Bold))  # Still larger than before
                painter.drawText(QRect(int(x), int(y), int(width), int(height)), Qt.AlignCenter, f"{process.pid}")
        
        # Update widget size to accommodate all processes without scaling down
        min_height = self.header_height + len(self.processes) * self.row_height + 20
        min_width = self.left_margin + (self.max_time_displayed + 1) * self.time_scale + 20
        
        if self.minimumHeight() < min_height or self.minimumWidth() < min_width:
            self.setMinimumHeight(min_height)
            self.setMinimumWidth(min_width)
            
    def _get_color_for_process(self, pid: int) -> QColor:
        """
        Get a color for a process based on its ID.
        
        Args:
            pid (int): Process ID
            
        Returns:
            QColor: Color for the process
        """
        return self.process_colors[pid % len(self.process_colors)]
        
    def mouseMoveEvent(self, event):
        """
        Handle mouse movement events for hover effects.
        
        Args:
            event: The mouse move event
        """
        # Get mouse position
        x, y = event.x(), event.y()
        
        # Check if mouse is in the chart area
        if x < self.left_margin or y < self.header_height:
            if self.highlighted_pid is not None:
                self.highlighted_pid = None
                self.update()
            return
        
        # Calculate process row
        row = (y - self.header_height) // self.row_height
        if row < 0 or row >= len(self.processes):
            if self.highlighted_pid is not None:
                self.highlighted_pid = None
                self.update()
            return
            
        # Calculate time (using 0-based timeline)
        time = (x - self.left_margin) // self.time_scale  # Using 0-based timeline without adjustment
        
        # Check if there's a process block at this position
        for process, start, end in self.timeline:
            process_idx = 0
            for i, p in enumerate(self.processes):
                if p.pid == process.pid:
                    process_idx = i
                    break
                    
            if process_idx == row and start <= time < end:
                if self.highlighted_pid != process.pid:
                    self.highlighted_pid = process.pid
                    self.update()
                    # Show tooltip with process info (using 0-based time display)
                    self.setToolTip(
                        f"Process: {process.name}\n"
                        f"ID: {process.pid}\n"
                        f"Time: {start} - {end}\n"  # Using 0-based timeline
                        f"Duration: {end - start}"
                    )
                return
        
        # If we get here, no process block was found
        if self.highlighted_pid is not None:
            self.highlighted_pid = None
            self.update()
            self.setToolTip("")
            
    def mouseReleaseEvent(self, event):
        """
        Handle mouse release events for block selection.
        
        Args:
            event: The mouse release event
        """
        if event.button() == Qt.LeftButton and self.highlighted_pid is not None:
            self.process_clicked.emit(self.highlighted_pid)
        elif event.button() == Qt.RightButton:
            # Show context menu
            self._show_context_menu(event.pos())
            
    def _show_context_menu(self, pos):
        """
        Show a context menu at the specified position.
        
        Args:
            pos: The position to show the menu at
        """
        menu = QMenu(self)
        
        # Add actions for time scale adjustment
        zoom_in_action = menu.addAction("Zoom In Timeline")
        zoom_out_action = menu.addAction("Zoom Out Timeline")
        
        menu.addSeparator()
        
        # Add actions for row height adjustment
        increase_row_action = menu.addAction("Increase Row Height")
        decrease_row_action = menu.addAction("Decrease Row Height")
        
        menu.addSeparator()
        
        # Add action for resetting the view
        reset_action = menu.addAction("Reset View")
        
        # Show the menu and get the selected action
        action = menu.exec_(self.mapToGlobal(pos))
        
        # Handle the selected action
        if action == zoom_in_action:
            self.time_scale = min(100, self.time_scale + 10)
            self.update()
        elif action == zoom_out_action:
            self.time_scale = max(20, self.time_scale - 10)
            self.update()
        elif action == increase_row_action:
            self.row_height = min(120, self.row_height + 10)
            self.update()
        elif action == decrease_row_action:
            self.row_height = max(40, self.row_height - 10)
            self.update()
        elif action == reset_action:
            self.time_scale = 40
            self.row_height = 70
            self.max_time_displayed = max(20, self.current_time + 5)
            self.update()
            
    def wheelEvent(self, event):
        """
        Handle mouse wheel events for zooming.
        
        Args:
            event: The wheel event
        """
        # Check if Ctrl key is pressed for zooming
        if event.modifiers() & Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                # Zoom in
                self.time_scale = min(100, self.time_scale + 2)
            else:
                # Zoom out
                self.time_scale = max(5, self.time_scale - 2)
                
            self.update()
        else:
            # Normal scrolling
            super().wheelEvent(event)
            
    def keyPressEvent(self, event):
        """
        Handle keyboard events.
        
        Args:
            event: The key event
        """
        if event.key() == Qt.Key_Plus or event.key() == Qt.Key_Equal:
            # Zoom in
            self.time_scale = min(100, self.time_scale + 5)
            self.update()
        elif event.key() == Qt.Key_Minus:
            # Zoom out
            self.time_scale = max(5, self.time_scale - 5)
            self.update()
        elif event.key() == Qt.Key_R:
            # Reset view
            self.time_scale = 30
            self.max_time_displayed = max(20, self.current_time + 5)
            self.update()
        else:
            super().keyPressEvent(event)