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
        self.max_time_displayed = 20
        self.time_scale = 35  # Adjusted default scale
        self.row_height = 60  # Adjusted row height
        self.header_height = 100 # Adjusted header height
        self.left_margin = 160  # Adjusted left margin
        self.timeline: List[Tuple[Process, int, int]] = []
        self.colors: Dict[int, QColor] = {}
        # Use the same color palette generation logic if possible, or define consistent colors
        self.process_colors = [
            QColor("#FF6347"), QColor("#1E90FF"), QColor("#32CD32"), QColor("#FFD700"),
            QColor("#8A2BE2"), QColor("#FF7F50"), QColor("#00CED1"), QColor("#FF1493"),
            QColor("#66BB6A"), QColor("#42A5F5") # Match main window colors
        ]
        self.dark_mode = True
        self.highlighted_pid = None
        self.hovered_block = None # Store (pid, start, end) of hovered block
        self.time_offset = 0
        self.last_process_end_time = 0
        
        # Setup UI
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the Gantt chart UI."""
        self.setMinimumHeight(250) # Adjusted minimum height
        self.setMinimumWidth(600) # Adjusted minimum width
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setFont(QFont("Segoe UI", 10)) # Use consistent font
    
    def reset(self):
        """Reset the Gantt chart to its initial state."""
        self.processes = []
        self.current_time = 0
        self.timeline = []
        self.colors = {}
        self.highlighted_pid = None
        self.max_time_displayed = 20
        self.time_offset = 0  # Reset the time offset
        self.last_process_end_time = 0  # Reset the last process end time
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
            
            # Update the last process end time to ensure current time is accurate
            self.last_process_end_time = adjusted_time + 1
        
        # CRITICAL FIX: Set current time to match the actual process execution time
        # Use the latest of: adjusted input time and last process end time
        self.current_time = max(adjusted_time, self.last_process_end_time)
        
        # Force immediate repaint to update the current time indicator
        # This ensures the timeline updates synchronously with processes
        self.update()
        
        # Automatically adjust displayed time range with more room ahead
        # This ensures we can always see what's coming next
        new_max_time = max(self.max_time_displayed, self.current_time + 5)
        if new_max_time > self.max_time_displayed:
            self.max_time_displayed = new_max_time
            # Adjust minimum width based on max time to ensure scrollbar appears
            # Cast to int to avoid TypeError
            self.setMinimumWidth(int(self.left_margin + self.max_time_displayed * self.time_scale + 20))
        
        # Maintain fixed time scale to ensure consistent visual representation
        # This prevents unwanted zooming/scaling during execution
        self.time_scale = 40
        
    def set_dark_mode(self, enabled: bool):
        """Enable or disable dark mode. Styles are handled in paintEvent."""
        self.dark_mode = enabled
        self.update() # Trigger repaint
        
    def paintEvent(self, event):
        """
        Paint the Gantt chart.
        
        Args:
            event: The paint event
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Use color definitions consistent with main_window.py
        # Define color palettes (simplified version for Gantt chart)
        dark_colors = {
            "window": QColor("#2D2D2D"),
            "base": QColor("#252525"),
            "header_bg_start": QColor(45, 45, 50),
            "header_bg_end": QColor(35, 35, 40),
            "sidebar_bg_start": QColor(45, 45, 50),
            "sidebar_bg_end": QColor(40, 40, 45),
            "text": QColor("#E0E0E0"),
            "grid": QColor(70, 70, 75),
            "axis": QColor("#C0C0C0"),
            "highlight": QColor("#3A7ECF"),
            "current_time_line": QColor(255, 80, 80, 220),
            "current_time_bg_start": QColor(180, 40, 40),
            "current_time_bg_end": QColor(130, 30, 30),
            "current_time_text": Qt.white,
            "tooltip_bg": QColor(50, 50, 55, 230),
            "tooltip_text": QColor(220, 220, 220),
        }

        light_colors = {
            "window": QColor("#F5F5F5"),
            "base": QColor("#FFFFFF"),
            "header_bg_start": QColor(240, 240, 245),
            "header_bg_end": QColor(225, 225, 230),
            "sidebar_bg_start": QColor(235, 235, 240),
            "sidebar_bg_end": QColor(225, 225, 230),
            "text": QColor("#212121"),
            "grid": QColor(220, 220, 225),
            "axis": QColor("#555555"),
            "highlight": QColor("#42A5F5"),
            "current_time_line": QColor(255, 60, 60, 220),
            "current_time_bg_start": QColor(255, 80, 80),
            "current_time_bg_end": QColor(220, 60, 60),
            "current_time_text": Qt.white,
            "tooltip_bg": QColor(250, 250, 250, 230),
            "tooltip_text": QColor(30, 30, 30),
        }

        colors = dark_colors if self.dark_mode else light_colors

        # Draw background
        painter.fillRect(event.rect(), colors["window"])

        # Draw header background
        header_grad = QLinearGradient(0, 0, 0, self.header_height)
        header_grad.setColorAt(0, colors["header_bg_start"])
        header_grad.setColorAt(1, colors["header_bg_end"])
        painter.fillRect(0, 0, self.width(), self.header_height, QBrush(header_grad))

        # Draw process names column background
        sidebar_gradient = QLinearGradient(0, 0, self.left_margin, 0)
        sidebar_gradient.setColorAt(0, colors["sidebar_bg_start"])
        sidebar_gradient.setColorAt(1, colors["sidebar_bg_end"])
        painter.fillRect(0, 0, self.left_margin, self.height(), QBrush(sidebar_gradient))

        # Draw grid
        self._draw_grid(painter, colors["grid"])

        # Draw timeline
        self._draw_timeline(painter, colors["text"], colors["axis"], colors["highlight"], colors)

        # Draw process labels
        self._draw_process_labels(painter, colors["text"], colors["highlight"])

        # Draw process executions
        self._draw_executions(painter, colors["text"])

        # Draw tooltip if hovering over a block
        self._draw_tooltip(painter, colors)
        
    def _draw_grid(self, painter: QPainter, grid_color: QColor):
        """
        Draw the grid for the Gantt chart.
        
        Args:
            painter (QPainter): The painter to use
            grid_color (QColor): Color to use for grid lines
        """
        grid_pen = QPen(grid_color, 1, Qt.DotLine)
        painter.setPen(grid_pen)

        # Draw vertical grid lines (time markers)
        time_step = self._calculate_time_step()
        for i in range(0, self.max_time_displayed + time_step, time_step):
            # Convert float to int to avoid TypeError
            x = int(self.left_margin + i * self.time_scale)
            if x < self.left_margin: continue
            # Convert all coordinates to int to match drawLine's signature
            painter.drawLine(x, int(self.header_height), x, int(self.height()))

        # Draw horizontal grid lines (process boundaries)
        for i in range(len(self.processes)):
            # Convert float to int for y coordinate
            y = int(self.header_height + (i + 1) * self.row_height)
            painter.drawLine(int(self.left_margin), y, int(self.width()), y)
        # Draw line separating labels from chart
        painter.drawLine(0, int(self.header_height), int(self.width()), int(self.header_height))
        
    def _calculate_time_step(self) -> int:
        """
        Calculate the appropriate time step for the timeline based on the scale.
        Returns the step size for timeline markers.
        
        Always returns 1 to ensure second-by-second timeline
        """
        if self.time_scale < 5:
            return 10
        elif self.time_scale < 15:
            return 5
        elif self.time_scale < 30:
            return 2
        else:
            return 1
            
    def _draw_timeline(self, painter: QPainter, text_color: QColor, axis_color: QColor, highlight_color: QColor, colors):
        """
        Draw the timeline axis with a completely redesigned layout.
        
        Args:
            painter (QPainter): The painter to use
            text_color (QColor): Color to use for text
        """
        axis_y = int(self.header_height - 25) # Position axis higher
        labels_y = int(self.header_height - 45) # Position labels above axis
        title_y = 10 # Position title at the top

        # Draw Title
        painter.setFont(QFont("Segoe UI", 12, QFont.Bold))
        painter.setPen(highlight_color)
        painter.drawText(QRect(0, title_y, int(self.width()), 30), Qt.AlignCenter, "CPU Execution Timeline")

        # Draw timeline axis
        painter.setPen(QPen(axis_color, 1.5))
        painter.drawLine(int(self.left_margin), axis_y, int(self.width() - 10), axis_y)

        # Determine label step based on time step
        time_step = self._calculate_time_step()
        label_step = time_step
        if self.time_scale < 10 and time_step == 1: label_step = 5
        elif self.time_scale < 20 and time_step == 1: label_step = 2

        # Draw time markers and labels
        painter.setFont(QFont("Segoe UI", 9))
        for i in range(0, self.max_time_displayed + 1, time_step):
            x = int(self.left_margin + i * self.time_scale)
            is_major = (i % max(label_step * 2, 5) == 0) # Make major ticks less frequent
            is_labeled = (i % label_step == 0)

            # Draw tick mark
            tick_height = 6 if is_major else 3
            painter.setPen(QPen(axis_color, 1.5 if is_major else 1))
            painter.drawLine(x, axis_y - tick_height, x, axis_y + tick_height)

            # Draw time label
            if is_labeled:
                painter.setPen(text_color)
                label_rect = QRect(int(x - 20), labels_y, 40, 20)
                painter.drawText(label_rect, Qt.AlignCenter, str(i))

        # Draw current time indicator
        if self.timeline:
            display_time = self.current_time
            current_x = int(self.left_margin + display_time * self.time_scale)

            # Draw line
            painter.setPen(QPen(colors["current_time_line"], 2, Qt.SolidLine))
            painter.drawLine(current_x, int(self.header_height), current_x, int(self.height()))
        
    def _draw_process_labels(self, painter: QPainter, text_color: QColor, highlight_color: QColor):
        """
        Draw the process names on the left side.
        
        Args:
            painter (QPainter): The painter to use
            text_color (QColor): Color to use for text
        """
        painter.setPen(text_color)

        # Draw column header
        painter.setFont(QFont("Segoe UI", 11, QFont.Bold))
        painter.setPen(highlight_color)
        painter.drawText(10, self.header_height - 30, self.left_margin - 20, 25, Qt.AlignLeft | Qt.AlignVCenter, "Processes")

        # Draw each process name
        painter.setFont(QFont("Segoe UI", 10))
        for i, process in enumerate(self.processes):
            y = self.header_height + i * self.row_height
            row_rect = QRect(0, y, self.left_margin, self.row_height)

            # Highlight background if hovered
            if self.hovered_block and self.hovered_block[0] == process.pid:
                highlight_bg = QColor(highlight_color)
                highlight_bg.setAlpha(40)
                painter.fillRect(row_rect, highlight_bg)

            # Draw process color indicator
            color_rect = QRect(10, y + self.row_height // 2 - 10, 20, 20)
            path = QPainterPath()
            path.addRoundedRect(QRectF(color_rect), 4, 4)
            painter.fillPath(path, self.colors.get(process.pid, QColor("gray")))
            painter.setPen(QPen(text_color.lighter(120) if self.dark_mode else text_color.darker(120), 0.5))
            painter.drawPath(path)

            # Draw process name and ID
            painter.setPen(text_color)
            process_text = f"{process.name} (P{process.pid})"
            text_rect = QRect(40, y, self.left_margin - 45, self.row_height)
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, process_text)
            
    def _draw_executions(self, painter: QPainter, text_color: QColor):
        """
        Draw the process execution blocks.
        
        Args:
            painter (QPainter): The painter to use
            text_color (QColor): Color to use for text
        """
        process_indices = {process.pid: i for i, process in enumerate(self.processes)}

        for process, start, end in self.timeline:
            if process.pid not in process_indices: continue

            row_index = process_indices[process.pid]
            y = int(self.header_height + row_index * self.row_height)
            x_start = int(self.left_margin + start * self.time_scale)
            width = int((end - start) * self.time_scale)

            # Ensure minimum width for visibility
            if width < 1: width = 1

            block_rect = QRectF(x_start, y + 10, width, self.row_height - 20) # Add padding
            block_path = QPainterPath()
            block_path.addRoundedRect(block_rect, 5, 5)

            # Base color
            base_color = self.colors.get(process.pid, QColor("gray"))

            # Apply gradient for 3D effect
            gradient = QLinearGradient(block_rect.topLeft(), block_rect.bottomLeft())
            gradient.setColorAt(0, base_color.lighter(120))
            gradient.setColorAt(1, base_color.darker(120))
            painter.fillPath(block_path, gradient)

            # Add border
            border_color = base_color.darker(150)
            painter.setPen(QPen(border_color, 1))
            painter.drawPath(block_path)

            # Highlight if hovered
            is_hovered = (self.hovered_block and
                          self.hovered_block[0] == process.pid and
                          self.hovered_block[1] == start and
                          self.hovered_block[2] == end)
            if is_hovered:
                painter.setPen(QPen(Qt.white if self.dark_mode else Qt.black, 1.5))
                painter.drawPath(block_path)

            # Draw process name inside block if it fits
            painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
            text_width = QFontMetrics(painter.font()).width(process.name)
            if width > text_width + 10:
                painter.setPen(Qt.white if base_color.lightness() < 128 else Qt.black)
                painter.drawText(block_rect.adjusted(5, 0, -5, 0), Qt.AlignCenter, process.name)
        
        # Update widget size to accommodate all processes without scaling down
        min_height = int(self.header_height + len(self.processes) * self.row_height + 20)
        min_width = int(self.left_margin + (self.max_time_displayed + 1) * self.time_scale + 20)
        
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
        if pid not in self.colors:
            color_index = len(self.colors) % len(self.process_colors)
            self.colors[pid] = self.process_colors[color_index]
        return self.colors[pid]
        
    def mouseMoveEvent(self, event):
        """
        Handle mouse movement events for hover effects.
        
        Args:
            event: The mouse move event
        """
        pos = event.pos()
        self.hovered_block = None

        if pos.y() > self.header_height and pos.x() > self.left_margin:
            time_at_pos = (pos.x() - self.left_margin) / self.time_scale
            row_index = int((pos.y() - self.header_height) // self.row_height)

            if 0 <= row_index < len(self.processes):
                hovered_pid = self.processes[row_index].pid
                # Find the specific block under the cursor
                for p, start, end in self.timeline:
                    if p.pid == hovered_pid and start <= time_at_pos < end:
                        self.hovered_block = (p.pid, start, end)
                        break

        self.update() # Trigger repaint for hover effect
        super().mouseMoveEvent(event)
            
    def mouseReleaseEvent(self, event):
        """
        Handle mouse release events for block selection.
        
        Args:
            event: The mouse release event
        """
        if event.button() == Qt.LeftButton and self.hovered_block:
            pid, start, end = self.hovered_block
            print(f"Clicked on P{pid} block [{start}-{end}]") # Debug print
            self.process_clicked.emit(pid)
        super().mouseReleaseEvent(event)
        
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
        delta = event.angleDelta().y()
        zoom_factor = 1.15 if delta > 0 else 1 / 1.15
        new_scale = self.time_scale * zoom_factor

        # Limit zoom levels
        min_scale = 2
        max_scale = 200
        if min_scale <= new_scale <= max_scale:
            self.time_scale = new_scale
            # Adjust minimum width based on new scale
            # Cast the result to int to fix TypeError
            self.setMinimumWidth(int(self.left_margin + self.max_time_displayed * self.time_scale + 20))
            self.update()
        event.accept()
            
    def keyPressEvent(self, event):
        """
        Handle keyboard events.
        
        Args:
            event: The key event
        """
        # Basic panning could be added here if desired
        pass
        
    def _draw_tooltip(self, painter: QPainter, colors):
        """
        Draw a tooltip if hovering over an execution block.
        """
        if not self.hovered_block: return

        pid, start, end = self.hovered_block
        process = next((p for p in self.processes if p.pid == pid), None)
        if not process: return

        tooltip_text = f"{process.name} (P{pid})\nExecuted: {start}s - {end}s\nDuration: {end - start}s"

        painter.setFont(QFont("Segoe UI", 9))
        # Fix: Move metrics definition before usage
        metrics = QFontMetrics(painter.font())
        text_rect = metrics.boundingRect(QRect(), Qt.AlignLeft, tooltip_text)

        tooltip_width = text_rect.width() + 20
        tooltip_height = text_rect.height() + 15

        # Position tooltip near the mouse cursor
        pos = self.mapFromGlobal(self.cursor().pos())
        tooltip_x = pos.x() + 15
        tooltip_y = pos.y() + 10

        # Adjust position if tooltip goes off-screen
        if tooltip_x + tooltip_width > self.width():
            tooltip_x = pos.x() - tooltip_width - 15
        if tooltip_y + tooltip_height > self.height():
            tooltip_y = pos.y() - tooltip_height - 10

        tooltip_rect = QRectF(tooltip_x, tooltip_y, tooltip_width, tooltip_height)
        tooltip_path = QPainterPath()
        tooltip_path.addRoundedRect(tooltip_rect, 5, 5)

        # Draw background
        painter.fillPath(tooltip_path, colors["tooltip_bg"])

        # Draw text
        painter.setPen(colors["tooltip_text"])
        painter.drawText(tooltip_rect.adjusted(10, 7, -10, -8), Qt.AlignLeft, tooltip_text)