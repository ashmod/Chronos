from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QSizePolicy, QMenu
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QFont, QFontMetrics, QPainterPath, QLinearGradient, QTextDocument
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
        self.time_scale = 40  # Increased default scale for clarity
        self.row_height = 70  # Increased row height for spacing
        self.header_height = 60 # Adjusted header height for new design
        self.left_margin = 210  # Increased left margin further for PIDs
        self.timeline: List[Tuple[Process, int, int]] = []
        self.colors: Dict[int, QColor] = {}
        # Use a slightly more vibrant color palette
        self.process_colors = [
            QColor("#EF5350"), QColor("#42A5F5"), QColor("#66BB6A"), QColor("#FFEE58"),
            QColor("#AB47BC"), QColor("#FFA726"), QColor("#26C6DA"), QColor("#EC407A"),
            QColor("#9CCC65"), QColor("#5C6BC0")
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
        self.setMinimumHeight(300) # Increased minimum height
        self.setMinimumWidth(700) # Increased minimum width
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
        new_max_time = max(self.max_time_displayed, self.current_time + 10) # Increased buffer
        if new_max_time > self.max_time_displayed:
            self.max_time_displayed = new_max_time
            # Adjust minimum width based on max time to ensure scrollbar appears
            # Cast to int to avoid TypeError
            self.setMinimumWidth(int(self.left_margin + self.max_time_displayed * self.time_scale + 40)) # Added padding
        
        # Maintain fixed time scale to ensure consistent visual representation
        # This prevents unwanted zooming/scaling during execution
        # self.time_scale = 40 # Keep scale consistent unless user changes it

        # Update minimum height based on number of processes
        min_height = int(self.header_height + len(self.processes) * self.row_height + 20)
        if self.minimumHeight() < min_height:
            self.setMinimumHeight(min_height)

        self.update() # Trigger repaint
        
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
        painter.setRenderHint(QPainter.Antialiasing) # Ensure smoothness
        
        colors = self._get_theme_colors()

        # Draw background
        painter.fillRect(event.rect(), colors["background"])

        # Draw header background (Time Axis Area)
        header_rect = QRectF(0, 0, self.width(), self.header_height)
        header_grad = QLinearGradient(header_rect.topLeft(), header_rect.bottomLeft())
        header_grad.setColorAt(0, colors["header"])
        header_grad.setColorAt(1, colors["header"].darker(110))
        painter.fillRect(header_rect, QBrush(header_grad))
        # Add a subtle bottom border to the header
        painter.setPen(QPen(colors["grid"], 0.5))
        painter.drawLine(0, int(self.header_height -1), self.width(), int(self.header_height -1))


        # Draw process names column background (Sidebar Area)
        sidebar_rect = QRectF(0, 0, self.left_margin, self.height())
        sidebar_gradient = QLinearGradient(sidebar_rect.topLeft(), sidebar_rect.topRight()) # Horizontal gradient
        sidebar_gradient.setColorAt(0, colors["header"])
        sidebar_gradient.setColorAt(1, colors["header"].darker(110))
        painter.fillRect(sidebar_rect, QBrush(sidebar_gradient))
        # Add a subtle right border to the sidebar
        painter.setPen(QPen(colors["grid"], 0.5))
        painter.drawLine(int(self.left_margin -1), 0, int(self.left_margin -1), self.height())


        # Draw grid
        self._draw_grid(painter, colors["grid"])

        # Draw timeline (pass colors dict)
        self._draw_timeline(painter, colors)

        # Draw process labels (pass colors dict)
        self._draw_process_labels(painter, colors)

        # Draw process executions (pass colors dict)
        self._draw_executions(painter, colors)

        # Draw tooltip if hovering over a block
        self._draw_tooltip(painter, colors)
        
    def _draw_grid(self, painter: QPainter, grid_color: QColor):
        """
        Draw the grid for the Gantt chart.
        
        Args:
            painter (QPainter): The painter to use
            grid_color (QColor): Color to use for grid lines
        """
        grid_pen = QPen(grid_color, 0.8, Qt.DotLine) # Slightly thicker dots
        painter.setPen(grid_pen)

        # Draw vertical grid lines (time markers)
        time_step = self._calculate_time_step()
        for i in range(0, int(self.max_time_displayed / time_step) + 2): # Ensure grid covers view
            time_val = i * time_step
            # Convert float to int to avoid TypeError
            x = int(self.left_margin + time_val * self.time_scale)
            if x < self.left_margin: continue
            # Convert all coordinates to int to match drawLine's signature
            painter.drawLine(x, int(self.header_height), x, int(self.height()))

        # Draw horizontal grid lines (process boundaries)
        painter.setPen(QPen(grid_color, 0.5, Qt.SolidLine)) # Thinner solid line for rows
        for i in range(len(self.processes)):
            # Convert float to int for y coordinate
            y = int(self.header_height + (i + 1) * self.row_height)
            painter.drawLine(int(self.left_margin), y, int(self.width()), y)
        
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
            
    def _draw_timeline(self, painter: QPainter, colors: Dict[str, QColor]):
        """
        Draw the timeline axis with improved styling.
        
        Args:
            painter (QPainter): The painter to use
            colors (Dict[str, QColor]): Color palette
        """
        axis_y = int(self.header_height - 15) # Position axis lower in header
        labels_y = int(self.header_height - 35) # Position labels above axis
        title_y = 10 # Position title near the top

        # Draw Title (Optional - can be removed if too cluttered)
        # painter.setFont(QFont("Segoe UI", 11, QFont.Bold))
        # painter.setPen(colors["highlight"])
        # painter.drawText(QRect(int(self.left_margin), title_y, int(self.width() - self.left_margin), 25), Qt.AlignCenter, "Execution Timeline")

        # Draw timeline axis - Thicker and clearer
        painter.setPen(QPen(colors["axis_label"], 2)) # Increased thickness
        painter.drawLine(int(self.left_margin), axis_y, int(self.width() - 10), axis_y)

        # Determine label step based on time step
        time_step = self._calculate_time_step()
        label_step = time_step
        # Adjust label frequency based on scale for readability
        if self.time_scale < 8: label_step = max(5, time_step * 5)
        elif self.time_scale < 15: label_step = max(2, time_step * 2)
        elif self.time_scale < 30: label_step = max(1, time_step)
        else: label_step = time_step


        # Draw time markers and labels
        painter.setFont(QFont("Segoe UI", 9))
        painter.setPen(colors["text"]) # Use standard text color for labels

        for i in range(0, int(self.max_time_displayed / time_step) + 2):
            time_val = i * time_step
            x = int(self.left_margin + time_val * self.time_scale)
            if x < self.left_margin: continue # Skip ticks before the margin

            is_major_tick = (time_val % max(label_step * 2, 5) == 0) # Define major ticks
            is_labeled = (time_val % label_step == 0)

            # Draw tick mark
            tick_height = 5 if is_major_tick else 3
            painter.setPen(QPen(colors["axis_label"], 1.5 if is_major_tick else 1))
            painter.drawLine(x, axis_y - tick_height, x, axis_y) # Ticks point upwards

            # Draw time label
            if is_labeled:
                painter.setPen(colors["text"])
                label_rect = QRect(int(x - 25), labels_y, 50, 20) # Wider rect for labels
                painter.drawText(label_rect, Qt.AlignCenter, str(time_val))

        # Draw current time indicator
        if self.timeline or self.current_time > 0: # Show even if timeline is empty but time > 0
            display_time = self.current_time
            current_x = int(self.left_margin + display_time * self.time_scale)

            # Draw line - Use dedicated color
            painter.setPen(QPen(colors["timeline_marker"], 2, Qt.SolidLine))
            painter.drawLine(current_x, int(self.header_height), current_x, int(self.height()))

            # Draw time value above the line in the header
            time_str = f"{display_time:.1f}s" # Show one decimal place if needed
            metrics = QFontMetrics(painter.font())
            time_width = metrics.width(time_str)
            time_rect = QRect(current_x - time_width // 2 - 5, 5, time_width + 10, 20)

            # Background for time indicator text
            time_bg_path = QPainterPath()
            time_bg_path.addRoundedRect(QRectF(time_rect), 3, 3)
            painter.fillPath(time_bg_path, colors["timeline_marker"].darker(120))

            painter.setPen(colors["highlight_text"])
            painter.drawText(time_rect, Qt.AlignCenter, time_str)
        
    def _draw_process_labels(self, painter: QPainter, colors: Dict[str, QColor]):
        """
        Draw the process names on the left side with improved styling.
        
        Args:
            painter (QPainter): The painter to use
            colors (Dict[str, QColor]): Color palette
        """
        # Draw column header ("Processes") - Centered and styled
        painter.setFont(QFont("Segoe UI", 11, QFont.Bold))
        painter.setPen(colors["highlight"]) # Use highlight color for header
        header_rect = QRect(0, 0, self.left_margin, self.header_height)
        painter.drawText(header_rect, Qt.AlignCenter, "Processes")


        # Draw each process name
        painter.setFont(QFont("Segoe UI", 10)) # Reset font for process names
        for i, process in enumerate(self.processes):
            y = self.header_height + i * self.row_height
            row_rect = QRect(0, y, self.left_margin, self.row_height)

            # Highlight background if hovered (Subtle)
            if self.hovered_block and self.hovered_block[0] == process.pid:
                highlight_bg = QColor(colors["highlight"])
                highlight_bg.setAlpha(30) # More subtle alpha
                painter.fillRect(row_rect, highlight_bg)

            # Draw process color indicator (Larger, centered)
            indicator_size = 18
            indicator_y = y + (self.row_height - indicator_size) // 2
            color_rect = QRect(15, indicator_y, indicator_size, indicator_size) # Indent more
            path = QPainterPath()
            path.addRoundedRect(QRectF(color_rect), 5, 5) # More rounded

            process_color = self.colors.get(process.pid, QColor("gray"))
            painter.fillPath(path, process_color)

            # Add subtle border to indicator
            border_alpha = 100 if self.dark_mode else 60
            painter.setPen(QPen(process_color.darker(130), 1))
            painter.drawPath(path)


            # Draw process name and ID (Better alignment and spacing)
            painter.setPen(colors["text"])
            process_text = f"{process.name} (P{process.pid})"
            text_x = color_rect.right() + 10 # Space after indicator
            text_rect = QRect(text_x, y, self.left_margin - text_x - 15, self.row_height) # Adjust width slightly more padding
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, process_text)
            
    def _draw_executions(self, painter: QPainter, colors: Dict[str, QColor]):
        """
        Draw the process execution blocks with enhanced styling.
        
        Args:
            painter (QPainter): The painter to use
            colors (Dict[str, QColor]): Color palette
        """
        process_indices = {process.pid: i for i, process in enumerate(self.processes)}

        block_padding = 8 # Padding within the row height
        block_height = self.row_height - 2 * block_padding

        for process, start, end in self.timeline:
            if process.pid not in process_indices: continue

            row_index = process_indices[process.pid]
            y = int(self.header_height + row_index * self.row_height + block_padding)
            x_start = int(self.left_margin + start * self.time_scale)
            width = int((end - start) * self.time_scale)

            # Ensure minimum width for visibility, prevent negative width
            width = max(1, width)

            block_rect = QRectF(x_start, y, width, block_height)
            block_path = QPainterPath()
            # Slightly less rounded corners
            block_path.addRoundedRect(block_rect, 4, 4)

            # Base color
            base_color = self.colors.get(process.pid, QColor("gray"))

            # Apply subtle gradient
            gradient = QLinearGradient(block_rect.topLeft(), block_rect.bottomLeft())
            gradient.setColorAt(0, base_color.lighter(115))
            gradient.setColorAt(1, base_color) # End with base color
            painter.fillPath(block_path, gradient)

            # Add border - subtle and matches base color darkness
            border_color = base_color.darker(130)
            painter.setPen(QPen(border_color, 0.8)) # Thinner border
            painter.drawPath(block_path)

            # Highlight if hovered - Use a distinct outline
            is_hovered = (self.hovered_block and
                          self.hovered_block[0] == process.pid and
                          self.hovered_block[1] == start and
                          self.hovered_block[2] == end)
            if is_hovered:
                highlight_pen = QPen(colors["highlight"], 1.5) # Use theme highlight
                painter.setPen(highlight_pen)
                # Draw slightly outside the block for better visibility
                highlight_rect = block_rect.adjusted(-1, -1, 1, 1)
                highlight_path = QPainterPath()
                highlight_path.addRoundedRect(highlight_rect, 5, 5)
                painter.drawPath(highlight_path)


            # Draw process name inside block if it fits - Improved contrast
            painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
            # Use QFontMetrics for integer-based calculations
            metrics = QFontMetrics(painter.font())
            text_width = metrics.horizontalAdvance(process.name)

            if width > text_width + 10: # Check if text fits with padding
                # Choose text color based on background lightness
                # Use lightness() for integer comparison with QColor
                text_color = Qt.white if base_color.lightness() < 128 else Qt.black
                painter.setPen(text_color)
                # Center text vertically and horizontally within the block
                painter.drawText(block_rect.toRect(), Qt.AlignCenter, process.name) # Use toRect() for QRect
        
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
        Draw a tooltip with improved styling.
        """
        if not self.hovered_block: return

        pid, start, end = self.hovered_block
        process = next((p for p in self.processes if p.pid == pid), None)
        if not process: return

        # Tooltip content
        tooltip_text = f"<b>{process.name} (P{pid})</b><br>" \
                       f"Executed: {start}s - {end}s<br>" \
                       f"Duration: {end - start}s"

        # Use QTextDocument for rich text rendering
        doc = QTextDocument()
        doc.setDefaultFont(QFont("Segoe UI", 9))
        doc.setHtml(tooltip_text)
        doc.setTextWidth(-1) # Auto width
        doc_size = doc.size()

        tooltip_width = doc_size.width() + 20
        tooltip_height = doc_size.height() + 15

        # Position tooltip near the mouse cursor
        pos = self.mapFromGlobal(self.cursor().pos())
        tooltip_x = pos.x() + 15
        tooltip_y = pos.y() + 10

        # Adjust position if tooltip goes off-screen
        if tooltip_x + tooltip_width > self.width():
            tooltip_x = pos.x() - tooltip_width - 15
        if tooltip_y + tooltip_height > self.height():
            tooltip_y = pos.y() - tooltip_height - 10
        # Ensure tooltip doesn't go off the top or left
        tooltip_x = max(0, tooltip_x)
        tooltip_y = max(0, tooltip_y)


        tooltip_rect = QRectF(tooltip_x, tooltip_y, tooltip_width, tooltip_height)
        tooltip_path = QPainterPath()
        tooltip_path.addRoundedRect(tooltip_rect, 6, 6) # Slightly more rounded

        # Draw background with slight transparency
        painter.setPen(Qt.NoPen) # No border for the tooltip background itself
        painter.fillPath(tooltip_path, colors["tooltip_bg"])

        # Draw text using QTextDocument
        painter.translate(tooltip_rect.left() + 10, tooltip_rect.top() + 7.5) # Position text inside padding
        doc.drawContents(painter)
        painter.translate(-(tooltip_rect.left() + 10), -(tooltip_rect.top() + 7.5)) # Reset translation
        
    def _get_theme_colors(self):
        """
        Get color palette based on current theme.
        
        Returns:
            Dict[str, QColor]: Dictionary of colors for the current theme
        """
        if self.dark_mode:
            return {
                "background": QColor("#1E1E1E"),
                "text": QColor("#F0F0F0"),
                "grid": QColor("#3D3D3D"),
                "grid_minor": QColor("#2A2A2A"),
                "header": QColor("#2F2F2F"),
                "header_text": QColor("#FFFFFF"),
                "highlight": QColor("#4A90E2"),
                "highlight_text": QColor("#FFFFFF"),
                "hover": QColor("#4A90E2").lighter(150),
                "hover_text": QColor("#FFFFFF"),
                "border": QColor("#505050"),
                "idle": QColor("#444444"),
                "timeline_marker": QColor("#77C6FF"),
                "axis_label": QColor("#B0B0B0"),
                "process_name_bg": QColor("#2A2A2A"),
            }
        else:
            return {
                "background": QColor("#FFFFFF"),
                "text": QColor("#212121"),
                "grid": QColor("#E0E0E0"),
                "grid_minor": QColor("#F0F0F0"),
                "header": QColor("#F5F5F5"),
                "header_text": QColor("#212121"),
                "highlight": QColor("#1976D2"),
                "highlight_text": QColor("#FFFFFF"),
                "hover": QColor("#1976D2").lighter(150),
                "hover_text": QColor("#212121"),
                "border": QColor("#BDBDBD"),
                "idle": QColor("#EEEEEE"),
                "timeline_marker": QColor("#1976D2"),
                "axis_label": QColor("#616161"),
                "process_name_bg": QColor("#F5F5F5"),
            }
    
    def _draw_process_blocks(self, painter: QPainter, colors: Dict[str, QColor]):
        """
        Draw the process execution blocks with enhanced styling.
        
        Args:
            painter (QPainter): The painter to use
            colors (Dict[str, QColor]): Color palette
        """
        # Draw background grid (dotted lines)
        painter.setPen(QPen(colors["grid"], 1, Qt.DashLine))
        
        # Draw vertical grid lines (time markers)
        for t in range(0, self.max_time_displayed + 1):
            x = self.left_margin + t * self.time_scale
            painter.drawLine(x, self.header_height, x, self.height())
        
        # Draw horizontal grid lines (process separators)
        for i in range(len(self.processes) + 1):
            y = self.header_height + i * self.row_height
            painter.drawLine(self.left_margin, y, self.width(), y)
            
        # Draw idle periods with striped pattern
        idle_periods = self._get_idle_periods()
        if idle_periods:
            idle_brush = QBrush(colors["idle"], Qt.Dense7Pattern)  # Sparser pattern
            painter.setBrush(idle_brush)
            painter.setPen(QPen(colors["border"], 1, Qt.DashLine))  # Dashed border
            
            for start_time, end_time in idle_periods:
                x = self.left_margin + start_time * self.time_scale
                width = (end_time - start_time) * self.time_scale
                
                # Draw across all process rows
                rect = QRect(
                    x, 
                    self.header_height,
                    width,
                    len(self.processes) * self.row_height
                )
                painter.fillRect(rect, idle_brush)
                painter.drawRect(rect)
                
                # Add "IDLE" text in the middle if width permits
                if width > 40:  # Only if there's enough space
                    painter.setPen(colors["text"])
                    painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
                    text_rect = QRect(
                        x, 
                        self.header_height + len(self.processes) * self.row_height // 3,
                        width,
                        self.row_height
                    )
                    painter.drawText(text_rect, Qt.AlignCenter, "IDLE")
        
        # Draw the actual process blocks with improved visual styling
        painter.setFont(QFont("Segoe UI", 10))
        
        for process, start, end in self.timeline:
            x = self.left_margin + start * self.time_scale
            width = (end - start) * self.time_scale
            
            # Find process row index
            try:
                process_index = self.processes.index(process)
            except ValueError:
                continue  # Skip if process is no longer in the list
                
            y = self.header_height + process_index * self.row_height
            rect = QRect(x, y, width, self.row_height)
            
            # Get process color with increased saturation/lightness for dark mode
            base_color = self.colors.get(process.pid, QColor("gray"))
            # Adjust color to ensure it's visible in both themes
            if self.dark_mode:
                # In dark mode, make colors brighter and more saturated
                if base_color.lightness() < 128:
                    base_color = base_color.lighter(150)
                if base_color.saturation() < 200:
                    h, s, l, a = base_color.getHsl()
                    base_color.setHsl(h, min(255, s + 55), l, a)
            else:
                # In light mode, ensure colors are dark enough
                if base_color.lightness() > 180:
                    base_color = base_color.darker(120)
            
            # Determine if this block is being hovered
            is_hovered = (self.hovered_block and 
                         self.hovered_block[0] == process.pid and
                         self.hovered_block[1] == start and 
                         self.hovered_block[2] == end)
            
            # Fill with gradient background
            if is_hovered:
                # Apply hover effect - lighter gradient
                gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
                gradient.setColorAt(0, base_color.lighter(130))
                gradient.setColorAt(1, base_color.lighter(110))
                painter.setBrush(QBrush(gradient))
                painter.setPen(QPen(base_color.lighter(150), 2))  # Brighter border
            else:
                # Normal gradient
                gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
                gradient.setColorAt(0, base_color.lighter(105))
                gradient.setColorAt(1, base_color)
                painter.setBrush(QBrush(gradient))
                painter.setPen(QPen(base_color.darker(110), 1))  # Darker border
                
            # Draw rounded rectangle with drop shadow (implicit with gradient)
            painter.drawRoundedRect(rect, 4, 4)
            
            # Determine text color to ensure readability
            if base_color.lightness() > 150:
                text_color = QColor("#000000")  # Black for light backgrounds
            else:
                text_color = QColor("#FFFFFF")  # White for dark backgrounds
                
            # If block is very small, just show process ID
            text = f"P{process.pid}"
            if width > 80:
                # More detailed text for larger blocks
                duration = end - start
                text = f"{process.name} (P{process.pid}) - {duration} units"
            elif width > 40:
                # Medium block size
                text = f"P{process.pid} - {end - start}"
                
            # Draw text with contrasting color
            painter.setPen(text_color)
            # Center text both horizontally and vertically
            painter.drawText(rect, Qt.AlignCenter, text)
            
            # Add visual indication that process completed in this segment (checkmark)
            if process.is_completed() and end == process.completion_time:
                # Draw a subtle checkmark or completion indicator
                checkmark_size = min(24, width // 3, self.row_height // 2)
                if checkmark_size >= 10:  # Only draw if there's enough space
                    checkmark_x = x + width - checkmark_size - 5
                    checkmark_y = y + (self.row_height - checkmark_size) // 2
                    
                    # Draw circle with checkmark
                    painter.setPen(QPen(text_color, 2))
                    painter.setBrush(Qt.NoBrush)
                    painter.drawEllipse(checkmark_x, checkmark_y, checkmark_size, checkmark_size)
                    
                    # Draw checkmark (simple diagonal line)
                    painter.drawLine(
                        checkmark_x + checkmark_size // 4, 
                        checkmark_y + checkmark_size // 2,
                        checkmark_x + checkmark_size // 2, 
                        checkmark_y + checkmark_size * 3 // 4
                    )
                    painter.drawLine(
                        checkmark_x + checkmark_size // 2, 
                        checkmark_y + checkmark_size * 3 // 4,
                        checkmark_x + checkmark_size * 3 // 4, 
                        checkmark_y + checkmark_size // 4
                    )