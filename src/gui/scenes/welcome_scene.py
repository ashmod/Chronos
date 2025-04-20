from PyQt5.QtWidgets import (QLabel, QPushButton, QVBoxLayout, 
                           QHBoxLayout, QGroupBox, QFrame, QSizePolicy,
                           QScrollArea, QWidget, QGridLayout, QSpacerItem, QStyle)
from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor, QIcon, QBrush, QLinearGradient, QPen

from .base_scene import BaseScene

class AlgorithmCard(QFrame):
    """Visual card displaying details about a CPU scheduling algorithm."""
    
    def __init__(self, name, description, icon=None, parent=None):
        super().__init__(parent)
        self.name = name
        self.description = description
        self.icon = icon
        self.dark_mode = False
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the card UI."""
        # Set card appearance
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setMinimumHeight(120)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Setup layout
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # Header with name and icon
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)
        
        if self.icon:
            icon_label = QLabel()
            icon_label.setPixmap(self.icon.pixmap(32, 32))
            header_layout.addWidget(icon_label)
        
        name_label = QLabel(self.name)
        name_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        header_layout.addWidget(name_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Description text
        desc_label = QLabel(self.description)
        desc_label.setWordWrap(True)
        desc_label.setFont(QFont("Segoe UI", 10))
        layout.addWidget(desc_label)
        
        # Apply initial styling
        self.apply_styles(self.dark_mode)
    
    def apply_styles(self, dark_mode):
        """Apply styling based on dark/light mode."""
        self.dark_mode = dark_mode
        
        if dark_mode:
            self.setStyleSheet("""
                AlgorithmCard {
                    background-color: #2F2F2F;
                    border: 1px solid #505050;
                    border-radius: 8px;
                    padding: 12px;
                }
                AlgorithmCard:hover {
                    background-color: #353535;
                    border: 1px solid #606060;
                }
                QLabel {
                    color: #EDEDED;
                }
            """)
        else:
            self.setStyleSheet("""
                AlgorithmCard {
                    background-color: #FFFFFF;
                    border: 1px solid #D0D0D0;
                    border-radius: 8px;
                    padding: 12px;
                }
                AlgorithmCard:hover {
                    background-color: #F5F5F5;
                    border: 1px solid #BBBBBB;
                }
                QLabel {
                    color: #1A1A1A;
                }
            """)

class WelcomeScene(BaseScene):
    """Welcome scene - the first screen users see when opening the app."""
    
    def __init__(self, parent=None):
        # Initialize dark_mode attribute before calling parent's __init__
        self.dark_mode = True  # Match app's default
        super().__init__(parent)
        
    def setup_ui(self):
        """Setup the welcome scene UI."""
        super().setup_ui()
        
        # Main container with margins
        main_container = QWidget()
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Logo and title section
        top_layout = QHBoxLayout()
        
        # App logo
        logo_frame = QFrame()
        logo_frame.setFixedSize(120, 120)
        logo_frame.setStyleSheet("background: transparent;")
        logo_frame_layout = QVBoxLayout(logo_frame)
        logo_frame_layout.setContentsMargins(0, 0, 0, 0)
        
        logo_label = QLabel()
        logo_label.setFixedSize(100, 100)
        logo_pixmap = self.create_app_logo(100)
        logo_label.setPixmap(logo_pixmap)
        logo_label.setScaledContents(True)
        logo_frame_layout.addWidget(logo_label, 0, Qt.AlignCenter)
        
        top_layout.addWidget(logo_frame)
        
        # Title and subtitle
        title_layout = QVBoxLayout()
        title_layout.setSpacing(10)
        
        title = QLabel("ProcessPilot")
        title.setAlignment(Qt.AlignLeft)
        title.setFont(QFont("Segoe UI", 36, QFont.Bold))
        title_layout.addWidget(title)
        
        subtitle = QLabel("Advanced CPU Scheduler Visualization")
        subtitle.setAlignment(Qt.AlignLeft)
        subtitle.setFont(QFont("Segoe UI", 16))
        title_layout.addWidget(subtitle)
        
        tagline = QLabel("An interactive simulation tool for exploring CPU scheduling algorithms")
        tagline.setAlignment(Qt.AlignLeft)
        tagline.setFont(QFont("Segoe UI", 11))
        title_layout.addWidget(tagline)
        
        top_layout.addLayout(title_layout, 1)
        main_layout.addLayout(top_layout)
        
        # Horizontal separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setFixedHeight(1)
        main_layout.addWidget(separator)
        
        # Actions section - Get Started
        start_group = QGroupBox("Get Started")
        start_group.setFont(QFont("Segoe UI", 12, QFont.Bold))
        start_layout = QHBoxLayout()
        start_layout.setSpacing(20)
        
        # New simulation button with icon
        new_simulation_button = QPushButton("New Simulation")
        new_simulation_button.setIcon(QIcon(self.style().standardIcon(QStyle.SP_FileIcon)))
        new_simulation_button.setIconSize(QSize(24, 24))
        new_simulation_button.setMinimumHeight(50)
        new_simulation_button.setFont(QFont("Segoe UI", 12))
        new_simulation_button.setObjectName("start_button")  # For CSS styling
        new_simulation_button.clicked.connect(lambda: self.switch_scene.emit("process_input"))
        start_layout.addWidget(new_simulation_button)
        
        # Load from file button with icon
        self.load_button = QPushButton("Load Processes from File")
        self.load_button.setIcon(QIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton)))
        self.load_button.setIconSize(QSize(24, 24))
        self.load_button.setMinimumHeight(50)
        self.load_button.setFont(QFont("Segoe UI", 12))
        self.load_button.setObjectName("import_button")  # For CSS styling
        self.load_button.clicked.connect(self._on_load_clicked)
        start_layout.addWidget(self.load_button)
        
        start_group.setLayout(start_layout)
        main_layout.addWidget(start_group)
        
        # Algorithms section - scrollable cards
        algorithms_group = QGroupBox("Available Scheduling Algorithms")
        algorithms_group.setFont(QFont("Segoe UI", 12, QFont.Bold))
        
        algorithms_scroll = QScrollArea()
        algorithms_scroll.setWidgetResizable(True)
        algorithms_scroll.setFrameShape(QFrame.NoFrame)
        
        algorithms_container = QWidget()
        algorithms_layout = QGridLayout(algorithms_container)
        algorithms_layout.setContentsMargins(0, 10, 0, 10)
        algorithms_layout.setSpacing(15)
        
        # Create algorithm cards
        algo_cards = [
            AlgorithmCard("First-Come, First-Served (FCFS)", 
                          "Processes are executed in the order they arrive. Simple, non-preemptive scheduling that's easy to implement but can lead to the convoy effect.",
                          self.style().standardIcon(QStyle.SP_ArrowRight)),
            AlgorithmCard("Shortest Job First (SJF)", 
                          "Non-preemptive scheduling algorithm that executes the process with the shortest burst time first. Optimal for minimizing average waiting time.",
                          self.style().standardIcon(QStyle.SP_ArrowDown)),
            AlgorithmCard("Shortest Remaining Time First (SRTF)", 
                          "Preemptive version of SJF where the process with the shortest remaining time is selected for execution. Interrupts when a shorter process arrives.",
                          self.style().standardIcon(QStyle.SP_MediaSeekBackward)),
            AlgorithmCard("Priority Scheduling (Non-Preemptive)", 
                          "Executes processes based on priority values. Higher priority processes are executed first, but can lead to starvation of lower priority processes.",
                          self.style().standardIcon(QStyle.SP_ArrowUp)),
            AlgorithmCard("Priority Scheduling (Preemptive)", 
                          "Preemptive version of Priority Scheduling where running processes can be interrupted by higher priority processes that arrive.",
                          self.style().standardIcon(QStyle.SP_MediaSkipBackward)),
            AlgorithmCard("Round Robin (RR)", 
                          "Preemptive algorithm that allocates a small unit of time (time quantum) to each process in a circular queue. Ensures fair execution time.",
                          self.style().standardIcon(QStyle.SP_BrowserReload))
        ]
        
        # Arrange cards in a 2x3 grid
        for i, card in enumerate(algo_cards):
            row = i // 2
            col = i % 2
            algorithms_layout.addWidget(card, row, col)
            
            # Apply dark mode to each card
            card.apply_styles(self.dark_mode)
        
        algorithms_scroll.setWidget(algorithms_container)
        
        algorithms_group_layout = QVBoxLayout()
        algorithms_group_layout.addWidget(algorithms_scroll)
        algorithms_group.setLayout(algorithms_group_layout)
        
        main_layout.addWidget(algorithms_group)
        
        # Footer with version and copyright
        footer_layout = QHBoxLayout()
        
        version_label = QLabel("Version 1.0.0")
        version_label.setFont(QFont("Segoe UI", 9))
        footer_layout.addWidget(version_label)
        
        footer_layout.addStretch()
        
        copyright_label = QLabel("© 2025 ASU Operation Systems Team")
        copyright_label.setFont(QFont("Segoe UI", 9))
        copyright_label.setAlignment(Qt.AlignRight)
        footer_layout.addWidget(copyright_label)
        
        main_layout.addLayout(footer_layout)
        
        # Scroll area for the entire content to ensure it fits on small screens
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setWidget(main_container)
        
        # Add scroll area to the main layout
        self.layout.addWidget(scroll_area)
    
    def create_app_logo(self, size=100):
        """Create app logo for display in the welcome screen."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Define colors
        primary_color = QColor("#4A90E2")
        secondary_color = QColor("#66BB6A")
        
        # Draw rounded square background
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(primary_color))
        painter.drawRoundedRect(2, 2, size-4, size-4, 20, 20)
        
        # Draw CPU square
        painter.setPen(QPen(QColor("#FFFFFF"), 3))
        painter.setBrush(QBrush(secondary_color))
        cpu_size = int(size * 0.6)  # Convert to integer
        cpu_x = int((size - cpu_size) / 2)  # Convert to integer
        cpu_y = int((size - cpu_size) / 2)  # Convert to integer
        painter.drawRoundedRect(cpu_x, cpu_y, cpu_size, cpu_size, 10, 10)
        
        # Draw CPU pins
        painter.setPen(QPen(QColor("#FFFFFF"), 3))
        pin_length = int(size * 0.12)  # Convert to integer
        
        # Top pins
        for i in range(3):
            x = int(cpu_x + cpu_size * (0.25 + i * 0.25))  # Convert to integer
            painter.drawLine(x, cpu_y, x, cpu_y - pin_length)
        
        # Bottom pins
        for i in range(3):
            x = int(cpu_x + cpu_size * (0.25 + i * 0.25))  # Convert to integer
            painter.drawLine(x, cpu_y + cpu_size, x, cpu_y + cpu_size + pin_length)
        
        # Left pins
        for i in range(3):
            y = int(cpu_y + cpu_size * (0.25 + i * 0.25))  # Convert to integer
            painter.drawLine(cpu_x, y, cpu_x - pin_length, y)
        
        # Right pins
        for i in range(3):
            y = int(cpu_y + cpu_size * (0.25 + i * 0.25))  # Convert to integer
            painter.drawLine(cpu_x + cpu_size, y, cpu_x + cpu_size + pin_length, y)
        
        # Draw 'P' letter in the center
        painter.setPen(QColor("#FFFFFF"))
        font = QFont("Arial", int(size * 0.3), QFont.Bold)
        painter.setFont(font)
        painter.drawText(int(size * 0.41), int(size * 0.63), "P")
        
        painter.end()
        return pixmap
    
    def _on_load_clicked(self):
        """Handle load from file button click."""
        # Signal to switch to process input scene with load flag
        self.switch_scene.emit("process_input:load")
    
    def set_dark_mode(self, enabled):
        """Apply dark mode styling to this scene."""
        self.dark_mode = enabled
        
        # Update algorithm cards
        for i in range(self.layout.count()):
            widget = self.layout.itemAt(i).widget()
            if isinstance(widget, QScrollArea):
                scroll_content = widget.widget()
                for child in scroll_content.findChildren(AlgorithmCard):
                    child.apply_styles(enabled)