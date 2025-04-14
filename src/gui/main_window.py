import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                          QHBoxLayout, QGroupBox, QLabel, QComboBox, QSpinBox, 
                          QPushButton, QScrollArea, QFormLayout, QLineEdit, 
                          QMessageBox, QCheckBox, QTabWidget, QGridLayout,
                          QStyleFactory, QSlider, QToolButton, QSplitter, 
                          QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
                          QDockWidget, QMenu, QAction, QFileDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer
from PyQt5.QtGui import QIcon, QFont, QColor, QPalette, QPixmap
from typing import List, Dict, Optional, Tuple

# Import the components we've created
from ..models.process import Process
from ..core.simulation import Simulation
from ..gui.process_table import ProcessTable
from ..gui.gantt_chart import GanttChart

# Import schedulers
from ..algorithms.fcfs import FCFSScheduler
from ..algorithms.sjf_non_preemptive import SJFNonPreemptiveScheduler
from ..algorithms.sjf_preemptive import SJFPreemptiveScheduler
from ..algorithms.priority_non_preemptive import PriorityNonPreemptiveScheduler
from ..algorithms.priority_preemptive import PriorityPreemptiveScheduler
from ..algorithms.round_robin import RoundRobinScheduler

class SimulationThread(QThread):
    """Thread for running the simulation without blocking the UI."""
    
    # Define signals for thread-safe UI updates
    process_updated = pyqtSignal(list, int)
    gantt_updated = pyqtSignal(object, int)
    stats_updated = pyqtSignal(float, float)
    
    def __init__(self, simulation):
        super().__init__()
        self.simulation = simulation
        
    def run(self):
        """Run the simulation."""
        # Connect simulation callbacks to our thread signals
        self.simulation.set_process_update_callback(self.process_updated.emit)
        self.simulation.set_gantt_update_callback(self.gantt_updated.emit)
        self.simulation.set_stats_update_callback(self.stats_updated.emit)
        
        # Start the simulation
        self.simulation.start()

class StatsWidget(QWidget):
    """Widget to display CPU scheduler statistics."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the statistics widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # CPU Utilization gauge
        cpu_group = QGroupBox("CPU Utilization")
        cpu_layout = QVBoxLayout()
        self.cpu_label = QLabel("0%")
        self.cpu_label.setAlignment(Qt.AlignCenter)
        self.cpu_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #4CAF50;")
        cpu_layout.addWidget(self.cpu_label)
        cpu_group.setLayout(cpu_layout)
        layout.addWidget(cpu_group)
        
        # Average times
        times_group = QGroupBox("Average Times")
        times_layout = QFormLayout()
        times_layout.setVerticalSpacing(12)
        
        self.avg_waiting_label = QLabel("0.00")
        self.avg_waiting_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        times_layout.addRow(QLabel("Waiting Time:"), self.avg_waiting_label)
        
        self.avg_turnaround_label = QLabel("0.00")
        self.avg_turnaround_label.setStyleSheet("font-weight: bold; color: #FF9800;")
        times_layout.addRow(QLabel("Turnaround Time:"), self.avg_turnaround_label)
        
        self.avg_response_label = QLabel("0.00")
        self.avg_response_label.setStyleSheet("font-weight: bold; color: #9C27B0;")
        times_layout.addRow(QLabel("Response Time:"), self.avg_response_label)
        
        times_group.setLayout(times_layout)
        layout.addWidget(times_group)
        
        # Throughput
        throughput_group = QGroupBox("Throughput")
        throughput_layout = QVBoxLayout()
        self.throughput_label = QLabel("0.00 processes/unit time")
        self.throughput_label.setAlignment(Qt.AlignCenter)
        self.throughput_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #F44336;")
        throughput_layout.addWidget(self.throughput_label)
        throughput_group.setLayout(throughput_layout)
        layout.addWidget(throughput_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
    def update_stats(self, avg_waiting: float, avg_turnaround: float):
        """Update statistics display."""
        self.avg_waiting_label.setText(f"{avg_waiting:.2f}")
        self.avg_turnaround_label.setText(f"{avg_turnaround:.2f}")
        
        # Calculate and update response time (can be derived or provided separately)
        # For now, just use a placeholder calculation
        response_time = avg_waiting * 0.75  # Placeholder calculation
        self.avg_response_label.setText(f"{response_time:.2f}")
        
        # Calculate throughput if we have processes
        if avg_turnaround > 0:
            throughput = 1 / avg_turnaround
            self.throughput_label.setText(f"{throughput:.2f} processes/unit time")
        
        # Update CPU utilization (placeholder for now)
        # In a real implementation, this would be calculated from process data
        if avg_turnaround > 0:
            utilization = min(100, 80 + avg_waiting * 2)  # Placeholder calculation
            self.cpu_label.setText(f"{int(utilization)}%")

class ProcessControlWidget(QWidget):
    """Widget for process control."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.process_count = 0
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the process control UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Process details group
        process_group = QGroupBox("Process Details")
        process_form = QFormLayout()
        process_form.setVerticalSpacing(12)
        
        # Process name
        self.process_name_input = QLineEdit("Process 1")
        self.process_name_input.setPlaceholderText("Enter process name")
        self.process_name_input.setStyleSheet("padding: 8px; border-radius: 8px;")
        process_form.addRow(QLabel("Name:"), self.process_name_input)
        
        # Arrival time
        self.arrival_time_spinbox = QSpinBox()
        self.arrival_time_spinbox.setRange(0, 10000)
        self.arrival_time_spinbox.setFixedHeight(36)
        self.arrival_time_spinbox.setStyleSheet("padding: 4px; border-radius: 8px;")
        process_form.addRow(QLabel("Arrival Time:"), self.arrival_time_spinbox)
        
        # Burst time
        self.burst_time_spinbox = QSpinBox()
        self.burst_time_spinbox.setRange(1, 10000)
        self.burst_time_spinbox.setValue(5)
        self.burst_time_spinbox.setFixedHeight(36)
        self.burst_time_spinbox.setStyleSheet("padding: 4px; border-radius: 8px;")
        process_form.addRow(QLabel("Burst Time:"), self.burst_time_spinbox)
        
        # Priority
        self.priority_spinbox = QSpinBox()
        self.priority_spinbox.setRange(0, 100)
        self.priority_spinbox.setFixedHeight(36)
        self.priority_spinbox.setStyleSheet("padding: 4px; border-radius: 8px;")
        process_form.addRow(QLabel("Priority:"), self.priority_spinbox)
        
        # Color indicator
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Color:"))
        
        self.color_preview = QFrame()
        self.color_preview.setFixedSize(36, 26)
        self.color_preview.setStyleSheet("background-color: #FF6347; border-radius: 8px;")
        color_layout.addWidget(self.color_preview)
        color_layout.addStretch()
        
        process_form.addRow(color_layout)
        
        process_group.setLayout(process_form)
        layout.addWidget(process_group)
        
        # Buttons layout
        buttons_group = QGroupBox("Actions")
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(10)
        
        # Add Process button
        self.add_process_button = QPushButton("Add Process")
        self.add_process_button.setIcon(QIcon.fromTheme("list-add"))
        self.add_process_button.setFixedHeight(40)
        self.add_process_button.setStyleSheet(
            "background-color: #4CAF50; color: white; font-weight: bold; border-radius: 8px;"
        )
        buttons_layout.addWidget(self.add_process_button)
        
        # Horizontal button row for Remove/Reset
        hr_buttons = QHBoxLayout()
        hr_buttons.setSpacing(8)
        
        # Remove All button
        self.remove_all_button = QPushButton("Remove All")
        self.remove_all_button.setIcon(QIcon.fromTheme("list-remove"))
        self.remove_all_button.setFixedHeight(40)
        self.remove_all_button.setStyleSheet(
            "background-color: #F44336; color: white; font-weight: bold; border-radius: 8px;"
        )
        hr_buttons.addWidget(self.remove_all_button)
        
        # Reset button
        self.reset_button = QPushButton("Reset")
        self.reset_button.setIcon(QIcon.fromTheme("edit-clear"))
        self.reset_button.setFixedHeight(40)
        self.reset_button.setStyleSheet(
            "background-color: #FFC107; color: white; font-weight: bold; border-radius: 8px;"
        )
        hr_buttons.addWidget(self.reset_button)
        
        buttons_layout.addLayout(hr_buttons)
        
        # Import from file
        self.import_button = QPushButton("Import from CSV...")
        self.import_button.setIcon(QIcon.fromTheme("document-open"))
        self.import_button.setFixedHeight(40)
        self.import_button.setStyleSheet(
            "background-color: #2196F3; color: white; font-weight: bold; border-radius: 8px;"
        )
        buttons_layout.addWidget(self.import_button)
        
        buttons_group.setLayout(buttons_layout)
        layout.addWidget(buttons_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
    def next_process_name(self):
        """Generate the next process name."""
        self.process_count += 1
        self.process_name_input.setText(f"Process {self.process_count + 1}")
        
        # Update color preview with next color in the cycle
        process_colors = [
            "#FF6347", "#1E90FF", "#32CD32", "#FFD700", 
            "#8A2BE2", "#FF7F50", "#00CED1", "#FF1493",
            "#66BB6A", "#42A5F5"
        ]
        color_index = self.process_count % len(process_colors)
        self.color_preview.setStyleSheet(
            f"background-color: {process_colors[color_index]}; border-radius: 8px;"
        )
        
    def reset_count(self):
        """Reset the process counter."""
        self.process_count = 0
        self.process_name_input.setText("Process 1")
        self.color_preview.setStyleSheet("background-color: #FF6347; border-radius: 8px;")

class SchedulerControlWidget(QWidget):
    """Widget for scheduler control."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the scheduler control UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Scheduler selection
        scheduler_group = QGroupBox("Scheduler")
        scheduler_form = QFormLayout()
        scheduler_form.setVerticalSpacing(12)
        
        # Scheduler type combo
        self.scheduler_combo = QComboBox()
        self.scheduler_combo.addItems([
            "First-Come, First-Served (FCFS)",
            "Shortest Job First (Non-Preemptive)",
            "Shortest Job First (Preemptive)",
            "Priority (Non-Preemptive)",
            "Priority (Preemptive)",
            "Round Robin"
        ])
        self.scheduler_combo.setFixedHeight(36)
        self.scheduler_combo.setStyleSheet("padding: 8px; border-radius: 8px;")
        scheduler_form.addRow(QLabel("Algorithm:"), self.scheduler_combo)
        
        # Time quantum for Round Robin
        self.quantum_layout = QHBoxLayout()
        self.time_quantum_spinbox = QSpinBox()
        self.time_quantum_spinbox.setRange(1, 100)
        self.time_quantum_spinbox.setValue(2)
        self.time_quantum_spinbox.setEnabled(False)
        self.time_quantum_spinbox.setFixedHeight(36)
        self.time_quantum_spinbox.setStyleSheet("padding: 4px; border-radius: 8px;")
        self.quantum_layout.addWidget(self.time_quantum_spinbox)
        
        self.quantum_label = QLabel("time units")
        self.quantum_layout.addWidget(self.quantum_label)
        
        scheduler_form.addRow(QLabel("Time Quantum:"), self.quantum_layout)
        
        scheduler_group.setLayout(scheduler_form)
        layout.addWidget(scheduler_group)
        
        # Simulation control group
        control_group = QGroupBox("Simulation Control")
        control_layout = QVBoxLayout()
        control_layout.setSpacing(12)
        
        # Speed control
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Speed:"))
        
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 10)
        self.speed_slider.setValue(1)  # Start at speed 1 instead of 5
        self.speed_slider.setTickPosition(QSlider.TicksBelow)
        self.speed_slider.setTickInterval(1)
        self.speed_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 8px;
                background: #555;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #2196F3;
                border: 1px solid #2196F3;
                width: 18px;
                height: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
        """)
        speed_layout.addWidget(self.speed_slider)
        
        self.speed_label = QLabel("1x")  # Updated to show 1x by default
        self.speed_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        speed_layout.addWidget(self.speed_label)
        
        control_layout.addLayout(speed_layout)
        
        # Control buttons
        buttons_layout = QGridLayout()
        buttons_layout.setHorizontalSpacing(8)
        buttons_layout.setVerticalSpacing(8)
        
        # Start button with icon
        self.start_button = QPushButton("Start")
        self.start_button.setIcon(QIcon.fromTheme("media-playback-start"))
        self.start_button.setFixedHeight(40)
        self.start_button.setStyleSheet(
            "background-color: #4CAF50; color: white; font-weight: bold; border-radius: 8px;"
        )
        buttons_layout.addWidget(self.start_button, 0, 0)
        
        # Pause button with icon
        self.pause_button = QPushButton("Pause")
        self.pause_button.setIcon(QIcon.fromTheme("media-playback-pause"))
        self.pause_button.setEnabled(False)
        self.pause_button.setFixedHeight(40)
        self.pause_button.setStyleSheet(
            "background-color: #FFC107; color: white; font-weight: bold; border-radius: 8px;"
        )
        buttons_layout.addWidget(self.pause_button, 0, 1)
        
        # Resume button with icon
        self.resume_button = QPushButton("Resume")
        self.resume_button.setIcon(QIcon.fromTheme("media-playback-start"))
        self.resume_button.setEnabled(False)
        self.resume_button.setFixedHeight(40)
        self.resume_button.setStyleSheet(
            "background-color: #2196F3; color: white; font-weight: bold; border-radius: 8px;"
        )
        buttons_layout.addWidget(self.resume_button, 1, 0)
        
        # Stop button with icon
        self.stop_button = QPushButton("Stop")
        self.stop_button.setIcon(QIcon.fromTheme("media-playback-stop"))
        self.stop_button.setEnabled(False)
        self.stop_button.setFixedHeight(40)
        self.stop_button.setStyleSheet(
            "background-color: #F44336; color: white; font-weight: bold; border-radius: 8px;"
        )
        buttons_layout.addWidget(self.stop_button, 1, 1)
        
        control_layout.addLayout(buttons_layout)
        
        # Run all at once button
        self.run_all_button = QPushButton("Run All At Once")
        self.run_all_button.setIcon(QIcon.fromTheme("media-skip-forward"))
        self.run_all_button.setFixedHeight(40)
        self.run_all_button.setStyleSheet(
            "background-color: #9C27B0; color: white; font-weight: bold; border-radius: 8px;"
        )
        control_layout.addWidget(self.run_all_button)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()

class MainWindow(QMainWindow):
    """Main window of the CPU Scheduler application."""
    
    def __init__(self):
        super().__init__()
        
        # Initialize state
        self.simulation = None
        self.simulation_thread = None
        self.current_scheduler = None
        self.dark_mode = True  # Default to dark mode
        
        # Setup UI
        self.setup_ui()
        
        # Start maximized
        self.showMaximized()
        
        # Setup keyboard shortcuts
        self.setup_shortcuts()
        
    def setup_ui(self):
        """Setup the main window UI."""
        # Set window properties
        self.setWindowTitle("CPU Scheduler Simulation")
        self.setMinimumSize(1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Menu bar setup
        self.setup_menu()
        
        # Toolbar setup
        self.setup_toolbar()
        
        # Create main splitter (allows resizing panels)
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setHandleWidth(2)
        self.main_splitter.setChildrenCollapsible(False)
        
        # Left side panel with controls in a splitter
        self.left_panel = QSplitter(Qt.Vertical)
        self.left_panel.setHandleWidth(2)
        self.left_panel.setChildrenCollapsible(False)
        
        # Scheduler control widget
        self.scheduler_control = SchedulerControlWidget()
        self.left_panel.addWidget(self.scheduler_control)
        
        # Process control widget
        self.process_control = ProcessControlWidget()
        self.left_panel.addWidget(self.process_control)
        
        # Statistics widget
        self.stats_widget = StatsWidget()
        self.left_panel.addWidget(self.stats_widget)
        
        # Right side with tabs
        self.right_panel = QTabWidget()
        self.right_panel.setTabPosition(QTabWidget.North)
        self.right_panel.setDocumentMode(True)
        self.right_panel.setMovable(True)
        
        # Process Table tab
        self.process_table = ProcessTable()
        self.right_panel.addTab(self.process_table, "Process Table")
        
        # Gantt Chart tab
        gantt_widget = QWidget()
        gantt_layout = QVBoxLayout(gantt_widget)
        gantt_layout.setContentsMargins(0, 0, 0, 0)
        
        self.gantt_chart = GanttChart()
        gantt_scroll = QScrollArea()
        gantt_scroll.setWidget(self.gantt_chart)
        gantt_scroll.setWidgetResizable(True)
        gantt_layout.addWidget(gantt_scroll)
        
        self.right_panel.addTab(gantt_widget, "Gantt Chart")
        
        # Add panels to main splitter
        self.main_splitter.addWidget(self.left_panel)
        self.main_splitter.addWidget(self.right_panel)
        
        # Set initial sizes (left panel gets 1/3, right panel gets 2/3)
        self.main_splitter.setSizes([400, 800])
        
        # Add splitter to main layout
        main_layout.addWidget(self.main_splitter)
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        # Connect signals and slots
        self.connect_signals()
        
        # Set the initial theme (dark mode)
        self.apply_styles(self.dark_mode)
        
        # Initialize the first scheduler
        self.on_scheduler_changed(0)
        
    def setup_menu(self):
        """Setup the application menu."""
        # Create menu bar
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # Import from CSV
        import_action = QAction("&Import Processes from CSV...", self)
        import_action.setShortcut("Ctrl+I")
        import_action.triggered.connect(self.on_import_processes)
        file_menu.addAction(import_action)
        
        # Export results
        export_action = QAction("&Export Results...", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.on_export_results)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        # Toggle dark mode
        self.dark_mode_action = QAction("&Light Mode", self)
        self.dark_mode_action.setCheckable(True)
        self.dark_mode_action.toggled.connect(self.toggle_theme)
        view_menu.addAction(self.dark_mode_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        # About action
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.on_about)
        help_menu.addAction(about_action)
        
    def setup_toolbar(self):
        """Setup the application toolbar."""
        # Create a toolbar
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        
        # Theme toggle button with moon/sun icons
        self.theme_button = QToolButton()
        
        # Load icons from resources
        sun_icon_path = os.path.join(os.path.dirname(__file__), "resources", "sun.svg")
        moon_icon_path = os.path.join(os.path.dirname(__file__), "resources", "moon.svg")
        
        self.sun_icon = QIcon(sun_icon_path)
        self.moon_icon = QIcon(moon_icon_path)
        
        # Set initial icon based on theme
        self.theme_button.setIcon(self.sun_icon if self.dark_mode else self.moon_icon)
        self.theme_button.setText("Light Mode" if self.dark_mode else "Dark Mode")
        self.theme_button.setIconSize(QSize(24, 24))
        self.theme_button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.theme_button.setCheckable(True)
        self.theme_button.setChecked(not self.dark_mode)
        self.theme_button.toggled.connect(self.toggle_theme)
        self.theme_button.setStyleSheet("""
            QToolButton {
                padding: 8px;
                border-radius: 10px;
                background-color: transparent;
            }
            QToolButton:hover {
                background-color: rgba(150, 150, 150, 0.2);
            }
        """)
        toolbar.addWidget(self.theme_button)
        
        toolbar.addSeparator()
        
        # Start button
        start_action = QAction(QIcon.fromTheme("media-playback-start"), "Start", self)
        start_action.triggered.connect(self.on_start)
        toolbar.addAction(start_action)
        
        # Pause button
        pause_action = QAction(QIcon.fromTheme("media-playback-pause"), "Pause", self)
        pause_action.triggered.connect(self.on_pause)
        toolbar.addAction(pause_action)
        
        # Stop button
        stop_action = QAction(QIcon.fromTheme("media-playback-stop"), "Stop", self)
        stop_action.triggered.connect(self.on_stop)
        toolbar.addAction(stop_action)
        
        toolbar.addSeparator()
        
        # Run all at once button
        run_all_action = QAction(QIcon.fromTheme("media-skip-forward"), "Run All", self)
        run_all_action.triggered.connect(self.on_run_all)
        toolbar.addAction(run_all_action)
        
    def connect_signals(self):
        """Connect all signals and slots."""
        # Scheduler control signals
        self.scheduler_control.scheduler_combo.currentIndexChanged.connect(self.on_scheduler_changed)
        self.scheduler_control.speed_slider.valueChanged.connect(self.on_speed_changed)
        self.scheduler_control.start_button.clicked.connect(self.on_start)
        self.scheduler_control.pause_button.clicked.connect(self.on_pause)
        self.scheduler_control.resume_button.clicked.connect(self.on_resume)
        self.scheduler_control.stop_button.clicked.connect(self.on_stop)
        self.scheduler_control.run_all_button.clicked.connect(self.on_run_all)
        
        # Process control signals
        self.process_control.add_process_button.clicked.connect(self.on_add_process)
        self.process_control.remove_all_button.clicked.connect(self.on_remove_all)
        self.process_control.reset_button.clicked.connect(self.on_reset)
        self.process_control.import_button.clicked.connect(self.on_import_processes)
        
        # Set the process table remove callback
        self.process_table.set_remove_callback(self.on_remove_process)
        
    def apply_styles(self, dark_mode):
        """Apply styling to the application based on the selected theme."""
        if dark_mode:
            # Dark theme
            app = QApplication.instance()
            app.setStyle(QStyleFactory.create("Fusion"))
            
            dark_palette = QPalette()
            dark_palette.setColor(QPalette.Window, QColor(45, 45, 45))
            dark_palette.setColor(QPalette.WindowText, Qt.white)
            dark_palette.setColor(QPalette.Base, QColor(30, 30, 30))
            dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
            dark_palette.setColor(QPalette.ToolTipText, Qt.white)
            dark_palette.setColor(QPalette.Text, Qt.white)
            dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ButtonText, Qt.white)
            dark_palette.setColor(QPalette.BrightText, Qt.red)
            dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
            dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            dark_palette.setColor(QPalette.HighlightedText, Qt.black)
            app.setPalette(dark_palette)
            
            app.setStyleSheet("""
                QMainWindow, QDialog {
                    background-color: #2D2D2D;
                }
                QGroupBox {
                    border: 1px solid #444444;
                    border-radius: 10px;
                    padding-top: 20px;
                    margin-top: 10px;
                    background-color: #333333;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    padding: 7px;
                    background-color: #333333;
                    color: #2196F3;
                    font-weight: bold;
                    font-size: 13px;
                }
                QPushButton {
                    border-radius: 8px;
                    padding: 8px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #555555;
                }
                QPushButton:pressed {
                    background-color: #333333;
                }
                QPushButton:disabled {
                    background-color: #333333;
                    color: #777777;
                }
                QComboBox, QSpinBox, QLineEdit {
                    border: 1px solid #555555;
                    border-radius: 8px;
                    padding: 6px 10px;
                    background-color: #333333;
                    color: #FFFFFF;
                    selection-background-color: #555555;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 24px;
                }
                QTabWidget::pane {
                    border: 1px solid #555555;
                    background-color: #333333;
                    border-radius: 5px;
                }
                QTabBar::tab {
                    background-color: #333333;
                    color: #FFFFFF;
                    border: 1px solid #555555;
                    padding: 10px 15px;
                    border-top-left-radius: 8px;
                    border-top-right-radius: 8px;
                }
                QTabBar::tab:selected {
                    background-color: #2196F3;
                    color: white;
                    border-bottom-color: #2196F3;
                }
                QTabBar::tab:hover:!selected {
                    background-color: #3A3A3A;
                }
                QScrollBar {
                    background-color: #333333;
                    width: 14px;
                    height: 14px;
                }
                QScrollBar::handle {
                    background-color: #555555;
                    border-radius: 7px;
                    min-height: 30px;
                }
                QScrollBar::handle:hover {
                    background-color: #666666;
                }
                QSlider::groove:horizontal {
                    height: 8px;
                    background: #333333;
                    border-radius: 4px;
                }
                QSlider::handle:horizontal {
                    background: #2196F3;
                    border: 1px solid #2196F3;
                    width: 16px;
                    height: 16px;
                    margin: -4px 0;
                    border-radius: 8px;
                }
                QSlider::handle:horizontal:hover {
                    background: #42A5F5;
                }
                QTableWidget {
                    gridline-color: #555555;
                    background-color: #333333;
                    color: #FFFFFF;
                    selection-background-color: #444444;
                    border-radius: 8px;
                }
                QTableWidget QHeaderView::section {
                    background-color: #444444;
                    color: #FFFFFF;
                    padding: 8px;
                    border: 1px solid #555555;
                    font-weight: bold;
                }
                QToolBar {
                    background-color: #333333;
                    border: 1px solid #444444;
                    spacing: 3px;
                    padding: 3px;
                }
                QToolButton {
                    background-color: #444444;
                    border-radius: 6px;
                    padding: 6px;
                    color: white;
                }
                QToolButton:hover {
                    background-color: #555555;
                }
                QSplitter::handle {
                    background-color: #2196F3;
                }
                QSplitter::handle:horizontal {
                    width: 2px;
                }
                QSplitter::handle:vertical {
                    height: 2px;
                }
                QMenuBar {
                    background-color: #333333;
                    color: #FFFFFF;
                }
                QMenuBar::item:selected {
                    background-color: #444444;
                }
                QMenu {
                    background-color: #333333;
                    color: #FFFFFF;
                    border: 1px solid #555555;
                    border-radius: 8px;
                }
                QMenu::item:selected {
                    background-color: #444444;
                }
                QStatusBar {
                    background-color: #333333;
                    color: #FFFFFF;
                    padding: 5px;
                }
                QLabel {
                    color: #EEEEEE;
                }
            """)
            
            # Update toolbar theme button text
            self.theme_button.setText("Light Mode")
            
            # Update menu action text
            self.dark_mode_action.setText("&Light Mode")
        else:
            # Light theme
            app = QApplication.instance()
            app.setStyle(QStyleFactory.create("Fusion"))
            app.setPalette(app.style().standardPalette())
            
            app.setStyleSheet("""
                QMainWindow, QDialog {
                    background-color: #F5F5F5;
                }
                QGroupBox {
                    border: 1px solid #CCCCCC;
                    border-radius: 10px;
                    padding-top: 20px;
                    margin-top: 10px;
                    background-color: #FFFFFF;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    padding: 7px;
                    background-color: #FFFFFF;
                    color: #1976D2;
                    font-weight: bold;
                    font-size: 13px;
                }
                QPushButton {
                    border-radius: 8px;
                    padding: 8px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #E0E0E0;
                }
                QPushButton:pressed {
                    background-color: #D0D0D0;
                }
                QPushButton:disabled {
                    background-color: #F0F0F0;
                    color: #AAAAAA;
                }
                QComboBox, QSpinBox, QLineEdit {
                    border: 1px solid #CCCCCC;
                    border-radius: 8px;
                    padding: 6px 10px;
                    background-color: #FFFFFF;
                    selection-background-color: #E0E0E0;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 24px;
                }
                QTabWidget::pane {
                    border: 1px solid #CCCCCC;
                    background-color: #FFFFFF;
                    border-radius: 5px;
                }
                QTabBar::tab {
                    background-color: #F0F0F0;
                    border: 1px solid #CCCCCC;
                    padding: 10px 15px;
                    border-top-left-radius: 8px;
                    border-top-right-radius: 8px;
                }
                QTabBar::tab:selected {
                    background-color: #2196F3;
                    color: white;
                    border-bottom-color: #2196F3;
                }
                QTabBar::tab:hover:!selected {
                    background-color: #E5E5E5;
                }
                QScrollBar {
                    background-color: #F0F0F0;
                    width: 14px;
                    height: 14px;
                }
                QScrollBar::handle {
                    background-color: #CCCCCC;
                    border-radius: 7px;
                    min-height: 30px;
                }
                QScrollBar::handle:hover {
                    background-color: #BBBBBB;
                }
                QSlider::groove:horizontal {
                    height: 8px;
                    background: #E0E0E0;
                    border-radius: 4px;
                }
                QSlider::handle:horizontal {
                    background: #2196F3;
                    border: 1px solid #2196F3;
                    width: 16px;
                    height: 16px;
                    margin: -4px 0;
                    border-radius: 8px;
                }
                QSlider::handle:horizontal:hover {
                    background: #42A5F5;
                }
                QTableWidget {
                    gridline-color: #DDDDDD;
                    background-color: #FFFFFF;
                    selection-background-color: #F0F0F0;
                    border-radius: 8px;
                }
                QTableWidget QHeaderView::section {
                    background-color: #F5F5F5;
                    padding: 8px;
                    border: 1px solid #DDDDDD;
                    font-weight: bold;
                }
                QToolBar {
                    background-color: #F5F5F5;
                    border: 1px solid #E0E0E0;
                    spacing: 3px;
                    padding: 3px;
                }
                QToolButton {
                    background-color: #F0F0F0;
                    border-radius: 6px;
                    padding: 6px;
                }
                QToolButton:hover {
                    background-color: #E0E0E0;
                }
                QSplitter::handle {
                    background-color: #2196F3;
                }
                QSplitter::handle:horizontal {
                    width: 2px;
                }
                QSplitter::handle:vertical {
                    height: 2px;
                }
                QMenuBar {
                    background-color: #F5F5F5;
                }
                QMenuBar::item:selected {
                    background-color: #E0E0E0;
                }
                QMenu {
                    background-color: #FFFFFF;
                    border: 1px solid #CCCCCC;
                    border-radius: 8px;
                }
                QMenu::item:selected {
                    background-color: #F0F0F0;
                }
                QStatusBar {
                    background-color: #F5F5F5;
                    padding: 5px;
                }
            """)
            
            # Update toolbar theme button text
            self.theme_button.setText("Dark Mode")
            
            # Update menu action text
            self.dark_mode_action.setText("&Dark Mode")
            
        # Update Gantt chart and Process table dark mode
        self.gantt_chart.set_dark_mode(dark_mode)
        self.process_table.set_dark_mode(dark_mode)
        
        # Update toolbar theme button state
        self.theme_button.setChecked(not dark_mode)
        
        # Update menu action state
        self.dark_mode_action.setChecked(not dark_mode)
    
    def toggle_theme(self, state):
        """Toggle between light and dark theme."""
        self.dark_mode = not state  # Invert because the action/button text says "Light Mode" when in dark mode
        self.apply_styles(self.dark_mode)
    
    def on_speed_changed(self, value):
        """Handle speed slider change."""
        self.scheduler_control.speed_label.setText(f"{value}x")
        if self.simulation:
            self.simulation.delay = 1.0 / value
    
    def on_scheduler_changed(self, index):
        """
        Handle scheduler type change.
        
        Args:
            index (int): Index of the selected scheduler
        """
        # Enable/disable time quantum field based on selected scheduler
        is_round_robin = index == 5  # Index 5 is Round Robin
        self.scheduler_control.time_quantum_spinbox.setEnabled(is_round_robin)
        self.scheduler_control.quantum_label.setEnabled(is_round_robin)
        
        # Enable/disable priority field based on selected scheduler
        is_priority = index in [3, 4]  # Indices 3, 4 are Priority schedulers
        self.process_control.priority_spinbox.setEnabled(is_priority)
        
        # Reset simulation
        self.on_reset()
        
        # Create the new scheduler
        scheduler_name = self.scheduler_control.scheduler_combo.currentText()
        
        if index == 0:  # FCFS
            self.current_scheduler = FCFSScheduler()
        elif index == 1:  # SJF (Non-Preemptive)
            self.current_scheduler = SJFNonPreemptiveScheduler()
        elif index == 2:  # SJF (Preemptive)
            self.current_scheduler = SJFPreemptiveScheduler()
        elif index == 3:  # Priority (Non-Preemptive)
            self.current_scheduler = PriorityNonPreemptiveScheduler()
        elif index == 4:  # Priority (Preemptive)
            self.current_scheduler = PriorityPreemptiveScheduler()
        elif index == 5:  # Round Robin
            time_quantum = self.scheduler_control.time_quantum_spinbox.value()
            self.current_scheduler = RoundRobinScheduler(time_quantum=time_quantum)
            
        # Create simulation
        self.simulation = Simulation(
            self.current_scheduler, 
            delay=1.0/self.scheduler_control.speed_slider.value()
        )
        
        # Register callbacks
        self.simulation.set_process_update_callback(self.process_table.update_table)
        self.simulation.set_gantt_update_callback(self.gantt_chart.update_chart)
        self.simulation.set_stats_update_callback(self.update_statistics)
        
        # Update status bar
        self.statusBar().showMessage(f"Selected scheduler: {scheduler_name}")
        
    def on_add_process(self):
        """Add a new process to the simulation."""
        if not self.simulation:
            return
            
        # Get process details from input fields
        name = self.process_control.process_name_input.text() or f"Process {self.process_control.process_count + 1}"
        arrival_time = self.process_control.arrival_time_spinbox.value()
        burst_time = self.process_control.burst_time_spinbox.value()
        priority = self.process_control.priority_spinbox.value()
        
        # Create new process
        process = Process(
            pid=self.process_control.process_count,
            name=name,
            arrival_time=arrival_time,
            burst_time=burst_time,
            priority=priority
        )
        
        # Add process to simulation
        self.simulation.add_process(process)
        
        # Update the process counter and name
        self.process_control.next_process_name()
        
        # Show status message
        self.statusBar().showMessage(f"Added process: {name}", 3000)
        
    def on_remove_process(self, pid):
        """
        Remove a process from the simulation.
        
        Args:
            pid (int): Process ID to remove
        """
        if not self.simulation:
            return
        
        # Find and remove the process from the scheduler
        self.simulation.remove_process(pid)
        
        # Update the UI
        if self.process_table:
            self.process_table.update_table(self.simulation.scheduler.processes, self.simulation.current_time)
        
        # Update the Gantt chart - it needs a complete reset when removing a process
        if self.gantt_chart:
            self.gantt_chart.reset()
            # Re-add the timeline for remaining processes
            for process in self.simulation.scheduler.processes:
                for start, end in process.execution_history:
                    for t in range(start, end):
                        self.gantt_chart.update_chart(process, t)
        
        # Show status message
        self.statusBar().showMessage(f"Removed process with ID: {pid}", 3000)
            
    def on_remove_all(self):
        """Remove all processes from the simulation."""
        if not self.simulation:
            return
            
        # Remove all processes
        self.simulation.remove_all_processes()
        
        # Reset process control
        self.process_control.reset_count()
        
        # Reset the Gantt chart
        self.gantt_chart.reset()
        
        # Update the UI
        if self.process_table:
            self.process_table.update_table([], self.simulation.current_time)
            
        # Show status message
        self.statusBar().showMessage("All processes removed", 3000)
        
    def on_reset(self):
        """Reset the simulation."""
        if self.simulation:
            self.simulation.reset()
            
        # Reset process control
        self.process_control.reset_count()
        
        # Reset the Gantt chart
        self.gantt_chart.reset()
        
        # Reset UI state
        self.scheduler_control.start_button.setEnabled(True)
        self.scheduler_control.pause_button.setEnabled(False)
        self.scheduler_control.resume_button.setEnabled(False)
        self.scheduler_control.stop_button.setEnabled(False)
        self.scheduler_control.run_all_button.setEnabled(True)
        
        # Show status message
        self.statusBar().showMessage("Simulation reset", 3000)
        
    def on_start(self):
        """Start the simulation."""
        if not self.simulation or not self.simulation.scheduler.processes:
            QMessageBox.warning(self, "Warning", "Please add at least one process first.")
            return
            
        # Update simulation speed
        self.simulation.delay = 1.0 / self.scheduler_control.speed_slider.value()
        
        # Update time quantum for Round Robin if needed
        if isinstance(self.current_scheduler, RoundRobinScheduler):
            self.current_scheduler.time_quantum = self.scheduler_control.time_quantum_spinbox.value()
        
        # Create and start the simulation thread
        self.simulation_thread = SimulationThread(self.simulation)
        
        # Connect thread signals to UI update slots
        self.simulation_thread.process_updated.connect(self.process_table.update_table)
        self.simulation_thread.gantt_updated.connect(self.gantt_chart.update_chart)
        self.simulation_thread.stats_updated.connect(self.update_statistics)
        
        # Start the thread
        self.simulation_thread.start()
        
        # Update UI state
        self.scheduler_control.start_button.setEnabled(False)
        self.scheduler_control.pause_button.setEnabled(True)
        self.scheduler_control.resume_button.setEnabled(False)
        self.scheduler_control.stop_button.setEnabled(True)
        self.scheduler_control.run_all_button.setEnabled(False)
        
        # Show status message
        self.statusBar().showMessage("Simulation started")
        
    def on_pause(self):
        """Pause the simulation."""
        if self.simulation:
            self.simulation.pause()
            
        # Update UI state
        self.scheduler_control.pause_button.setEnabled(False)
        self.scheduler_control.resume_button.setEnabled(True)
        
        # Show status message
        self.statusBar().showMessage("Simulation paused")
        
    def on_resume(self):
        """Resume the simulation."""
        if self.simulation:
            self.simulation.resume()
            
        # Update UI state
        self.scheduler_control.pause_button.setEnabled(True)
        self.scheduler_control.resume_button.setEnabled(False)
        
        # Show status message
        self.statusBar().showMessage("Simulation resumed")
        
    def on_stop(self):
        """Stop the simulation."""
        if self.simulation:
            self.simulation.stop()
            
        # Wait for thread to finish
        if self.simulation_thread and self.simulation_thread.isRunning():
            self.simulation_thread.wait()
            
        # Update UI state
        self.scheduler_control.start_button.setEnabled(True)
        self.scheduler_control.pause_button.setEnabled(False)
        self.scheduler_control.resume_button.setEnabled(False)
        self.scheduler_control.stop_button.setEnabled(False)
        self.scheduler_control.run_all_button.setEnabled(True)
        
        # Show status message
        self.statusBar().showMessage("Simulation stopped")
        
    def on_run_all(self):
        """Run all processes at once."""
        if not self.simulation or not self.simulation.scheduler.processes:
            QMessageBox.warning(self, "Warning", "Please add at least one process first.")
            return
            
        # Update time quantum for Round Robin if needed
        if isinstance(self.current_scheduler, RoundRobinScheduler):
            self.current_scheduler.time_quantum = self.scheduler_control.time_quantum_spinbox.value()
        
        # Create a temporary thread for running all at once
        class RunAllThread(QThread):
            process_updated = pyqtSignal(list, int)
            gantt_updated = pyqtSignal(object, int)
            stats_updated = pyqtSignal(float, float)
            
            def __init__(self, simulation):
                super().__init__()
                self.simulation = simulation
                
            def run(self):
                # Connect signals to simulation callbacks
                self.simulation.set_process_update_callback(self.process_updated.emit)
                self.simulation.set_gantt_update_callback(self.gantt_updated.emit)
                self.simulation.set_stats_update_callback(self.stats_updated.emit)
                
                # Run all at once
                self.simulation.run_all_at_once()
        
        # Create and start the thread
        run_all_thread = RunAllThread(self.simulation)
        
        # Connect thread signals to UI slots
        run_all_thread.process_updated.connect(self.process_table.update_table)
        run_all_thread.gantt_updated.connect(self.gantt_chart.update_chart)
        run_all_thread.stats_updated.connect(self.update_statistics)
        
        # Start the thread
        run_all_thread.start()
        
        # Store reference to prevent garbage collection
        self.run_all_thread = run_all_thread
        
        # Show status message
        self.statusBar().showMessage("Running all processes at once")
        
    def update_statistics(self, avg_waiting: float, avg_turnaround: float):
        """
        Update the statistics display.
        
        Args:
            avg_waiting (float): Average waiting time
            avg_turnaround (float): Average turnaround time
        """
        self.stats_widget.update_stats(avg_waiting, avg_turnaround)
        
    def on_import_processes(self):
        """Import processes from a CSV file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Processes", "", "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return
            
        try:
            # For now, just show a placeholder message
            # In a real implementation, we would parse the CSV and add processes
            QMessageBox.information(
                self, 
                "Import Processes", 
                f"CSV import from '{file_path}' would be processed here."
            )
            
            # Example of actual implementation (pseudo-code):
            # with open(file_path, 'r') as f:
            #     for line in f.readlines():
            #         name, arrival, burst, priority = line.strip().split(',')
            #         process = Process(...)
            #         self.simulation.add_process(process)
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import processes: {str(e)}")
        
    def on_export_results(self):
        """Export simulation results to a file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Results", "", "CSV Files (*.csv);;Text Files (*.txt);;All Files (*)"
        )
        
        if not file_path:
            return
            
        try:
            # For now, just show a placeholder message
            # In a real implementation, we would export results to the file
            QMessageBox.information(
                self, 
                "Export Results", 
                f"Results would be exported to '{file_path}'."
            )
            
            # Example of actual implementation (pseudo-code):
            # with open(file_path, 'w') as f:
            #     f.write("Process,Arrival,Burst,Priority,Waiting,Turnaround\n")
            #     for process in self.simulation.scheduler.processes:
            #         f.write(f"{process.name},{process.arrival_time},{process.burst_time},{process.priority},{process.waiting_time},{process.turnaround_time}\n")
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export results: {str(e)}")
            
    def on_about(self):
        """Show the about dialog."""
        QMessageBox.about(
            self,
            "About CPU Scheduler Simulation",
            """<html>
            <h1 style="color: #2196F3;">CPU Scheduler Simulation</h1>
            <p>A visualization tool for CPU scheduling algorithms.</p>
            <p>Developed for ASU Senior Project - Operating Systems</p>
            <p>Version 2.0 - April 2025</p>
            </html>"""
        )
        
    def closeEvent(self, event):
        """
        Handle window close event.
        
        Args:
            event: The close event
        """
        if self.simulation:
            self.simulation.stop()
            
        if self.simulation_thread and self.simulation_thread.isRunning():
            self.simulation_thread.quit()
            self.simulation_thread.wait()
            
        event.accept()
        
    def setup_shortcuts(self):
        """Setup keyboard shortcuts for common actions."""
        # Add process shortcut (Ctrl+A)
        add_shortcut = QAction("Add Process", self)
        add_shortcut.setShortcut("Ctrl+A")
        add_shortcut.triggered.connect(self.on_add_process)
        self.addAction(add_shortcut)
        
        # Start simulation shortcut (F5)
        start_shortcut = QAction("Start", self)
        start_shortcut.setShortcut("F5")
        start_shortcut.triggered.connect(self.on_start)
        self.addAction(start_shortcut)
        
        # Pause simulation shortcut (F6)
        pause_shortcut = QAction("Pause", self)
        pause_shortcut.setShortcut("F6")
        pause_shortcut.triggered.connect(self.on_pause)
        self.addAction(pause_shortcut)
        
        # Stop simulation shortcut (F8)
        stop_shortcut = QAction("Stop", self)
        stop_shortcut.setShortcut("F8")
        stop_shortcut.triggered.connect(self.on_stop)
        self.addAction(stop_shortcut)
        
        # Run all shortcut (F9)
        run_all_shortcut = QAction("Run All", self)
        run_all_shortcut.setShortcut("F9")
        run_all_shortcut.triggered.connect(self.on_run_all)
        self.addAction(run_all_shortcut)
        
        # Reset shortcut (Ctrl+R)
        reset_shortcut = QAction("Reset", self)
        reset_shortcut.setShortcut("Ctrl+R")
        reset_shortcut.triggered.connect(self.on_reset)
        self.addAction(reset_shortcut)
        
        # Toggle theme shortcut (Ctrl+T)
        theme_shortcut = QAction("Toggle Theme", self)
        theme_shortcut.setShortcut("Ctrl+T")
        theme_shortcut.triggered.connect(lambda: self.toggle_theme(not self.dark_mode))
        self.addAction(theme_shortcut)