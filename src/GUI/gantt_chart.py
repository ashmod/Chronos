from PyQt5.QtWidgets import (QWidget, QScrollArea, QHBoxLayout, 
                           QVBoxLayout, QSizePolicy)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPainter, QPen, QColor

class GanttChart(QWidget):
    def __init__(self):
        super().__init__()
        self.timeline = []
        self.setMinimumHeight(80)
        
        # Create scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        
        # Create inner widget for drawing
        self.inner_widget = GanttInnerWidget()
        self.inner_widget.setMinimumHeight(80)
        self.scroll_area.setWidget(self.inner_widget)
        
        # Set up layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.scroll_area)
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    
    def update_timeline(self, timeline):
        """Update with [(pid, start_time, end_time), ...]"""
        self.timeline = timeline
        if timeline:
            # Calculate total width needed (1 pixel per time unit)
            total_time = max(end for _, _, end in timeline)
            # Add some padding for better visualization
            self.inner_widget.setMinimumWidth(total_time + 50)
            self.inner_widget.update_timeline(timeline)
        else:
            self.inner_widget.update_timeline([])
    
    def paintEvent(self, event):
        # This is now handled by the inner widget
        pass

class GanttInnerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.timeline = []
        self.setMinimumHeight(80)
        # Set size policy to allow horizontal expansion
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
    
    def update_timeline(self, timeline):
        self.timeline = timeline
        self.update()
    
    def paintEvent(self, event):
        if not self.timeline:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        total_time = max(end for _, _, end in self.timeline)
        
        # Draw grid lines
        painter.setPen(QPen(Qt.gray, 1, Qt.DotLine))
        for time in range(0, total_time + 1, 5):
            x = time
            painter.drawLine(x, 0, x, height)
        
        # Draw timeline
        for pid, start, end in self.timeline:
            x1 = start
            x2 = end
            
            # Draw process block
            color = QColor(100 + (pid * 40) % 155, 100 + (pid * 70) % 155, 200)
            painter.fillRect(x1, 0, x2 - x1, height, color)
            
            # Draw text
            painter.setPen(Qt.white)
            painter.drawText(int(x1), 0, int(x2 - x1), height, 
                           Qt.AlignCenter, f"P{pid}")
            
            # Draw border
            painter.setPen(Qt.black)
            painter.drawRect(x1, 0, x2 - x1, height)
            
            # Draw time markers
            painter.setPen(Qt.black)
            painter.drawText(int(x1), height - 5, 30, 20, 
                           Qt.AlignLeft, str(start))
            painter.drawText(int(x2) - 30, height - 5, 30, 20, 
                           Qt.AlignRight, str(end)) 