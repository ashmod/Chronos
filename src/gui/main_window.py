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
        
    def update_stats(self, avg_waiting: float, avg_turnaround: float, simulation=None):
        """
        Update statistics display.
        
        Args:
            avg_waiting (float): Average waiting time
            avg_turnaround (float): Average turnaround time
            simulation (Simulation, optional): The simulation object to get more detailed stats
        """
        self.avg_waiting_label.setText(f"{avg_waiting:.2f}")
        self.avg_turnaround_label.setText(f"{avg_turnaround:.2f}")
        
        # Calculate proper response time
        avg_response = 0.0
        completed_count = 0
        current_time = 0
        
        if simulation:
            # Get all processes (both running and completed)
            all_processes = simulation.scheduler.processes + simulation.scheduler.completed_processes
            
            # Calculate response time
            response_times = []
            for process in all_processes:
                if process.start_time is not None and process.arrival_time is not None:
                    # Response time = time first scheduled - arrival time
                    response_times.append(process.start_time - process.arrival_time)
            
            # Calculate average response time if we have data
            if response_times:
                avg_response = sum(response_times) / len(response_times)
                
            # Count completed processes for throughput
            completed_count = len(simulation.scheduler.completed_processes)
            
            # Get current simulation time
            current_time = simulation.scheduler.current_time
            
            # Fixed CPU utilization calculation
            if current_time > 0:
                # Create a timeline of CPU usage
                # For each time unit, track whether CPU was busy or idle
                timeline = [False] * (current_time + 1)
                
                # Mark time units where CPU was busy
                for process in all_processes:
                    for start, end in process.execution_history:
                        # Mark each time unit in this execution period as busy
                        for t in range(start, min(end, len(timeline))):
                            timeline[t] = True
                
                # Count busy time units
                busy_time = sum(1 for t in timeline if t)
                
                # Calculate utilization based on actual busy time
                cpu_utilization = (busy_time / current_time) * 100
                self.cpu_label.setText(f"{int(cpu_utilization)}%")
                
                # Update color based on utilization level
                if cpu_utilization < 50:
                    self.cpu_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #FFC107;")  # Yellow for low utilization
                elif cpu_utilization < 80:
                    self.cpu_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #4CAF50;")  # Green for good utilization
                else:
                    self.cpu_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #F44336;")  # Red for high utilization
            else:
                self.cpu_label.setText("0%")
                self.cpu_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #4CAF50;")
        
        # Update response time display
        self.avg_response_label.setText(f"{avg_response:.2f}")
        
        # Calculate and update throughput (completed processes / simulation time)
        if current_time > 0:
            throughput = completed_count / current_time
            self.throughput_label.setText(f"{throughput:.2f} processes/unit time")
        else:
            self.throughput_label.setText("0.00 processes/unit time")

class ProcessControlWidget(QWidget):
    """Widget for process control."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.process_count = 0
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the process control UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8) # Reduced margins
        layout.setSpacing(10) # Reduced spacing
        
        # Process details group
        process_group = QGroupBox("Process Details")
        process_form = QFormLayout()
        process_form.setVerticalSpacing(10) # Reduced spacing
        process_form.setHorizontalSpacing(15) # Added horizontal spacing
        
        # Process name
        self.process_name_input = QLineEdit("Process 1")
        self.process_name_input.setPlaceholderText("Enter process name")
        self.process_name_input.setStyleSheet("""
            padding: 8px 12px; /* Adjusted padding */
            border-radius: 8px; /* Slightly less rounded */
            font-size: 18px;
            border: 1px solid transparent; /* Use 1px border */
        """)
        process_form.addRow(QLabel("Name:"), self.process_name_input)
        
        # Arrival time
        self.arrival_time_spinbox = QSpinBox()
        self.arrival_time_spinbox.setRange(0, 10000)
        self.arrival_time_spinbox.setFixedHeight(38) # Adjusted height
        self.arrival_time_spinbox.setStyleSheet("""
            padding: 8px 12px; /* Adjusted padding */
            border-radius: 8px; /* Slightly less rounded */
            font-size: 18px;
            border: 1px solid transparent; /* Use 1px border */
        """)
        process_form.addRow(QLabel("Arrival:"), self.arrival_time_spinbox) # Shortened label
        
        # Burst time
        self.burst_time_spinbox = QSpinBox()
        self.burst_time_spinbox.setRange(1, 10000)
        self.burst_time_spinbox.setValue(5)
        self.burst_time_spinbox.setFixedHeight(38) # Adjusted height
        self.burst_time_spinbox.setStyleSheet("""
            padding: 8px 12px; /* Adjusted padding */
            border-radius: 8px; /* Slightly less rounded */
            font-size: 18px;
            border: 1px solid transparent; /* Use 1px border */
        """)
        process_form.addRow(QLabel("Burst:"), self.burst_time_spinbox) # Shortened label
        
        # Priority
        self.priority_spinbox = QSpinBox()
        self.priority_spinbox.setRange(0, 100)
        self.priority_spinbox.setFixedHeight(38) # Adjusted height
        self.priority_spinbox.setStyleSheet("""
            padding: 8px 12px; /* Adjusted padding */
            border-radius: 8px; /* Slightly less rounded */
            font-size: 18px;
            border: 1px solid transparent; /* Use 1px border */
        """)
        process_form.addRow(QLabel("Priority:"), self.priority_spinbox)
        
        # Color indicator
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Color:"))
        
        self.color_preview = QFrame()
        self.color_preview.setFixedSize(38, 30) # Adjusted size
        self.color_preview.setStyleSheet("background-color: #FF6347; border-radius: 8px;") # Slightly less rounded
        color_layout.addWidget(self.color_preview)
        color_layout.addStretch()
        
        process_form.addRow(color_layout)
        
        process_group.setLayout(process_form)
        layout.addWidget(process_group)
        
        # Buttons layout
        buttons_group = QGroupBox("Actions")
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(8) # Reduced spacing
        
        # Add Process button
        self.add_process_button = QPushButton("Add Process")
        self.add_process_button.setIcon(QIcon.fromTheme("list-add"))
        self.add_process_button.setFixedHeight(40) # Adjusted height
        self.add_process_button.setObjectName("add_process_button")
        buttons_layout.addWidget(self.add_process_button)
        
        # Horizontal button row for Remove/Reset
        hr_buttons = QHBoxLayout()
        hr_buttons.setSpacing(8) # Reduced spacing
        
        # Remove All button
        self.remove_all_button = QPushButton("Clear All") # Changed text
        self.remove_all_button.setIcon(QIcon.fromTheme("edit-clear")) # Changed icon to match Reset
        self.remove_all_button.setFixedHeight(40) # Adjusted height
        self.remove_all_button.setObjectName("remove_all_button")
        hr_buttons.addWidget(self.remove_all_button)
        
        # Reset button
        self.reset_button = QPushButton("Reset")
        self.reset_button.setIcon(QIcon.fromTheme("edit-clear"))
        self.reset_button.setFixedHeight(40) # Adjusted height
        self.reset_button.setObjectName("reset_button")
        hr_buttons.addWidget(self.reset_button)
        
        buttons_layout.addLayout(hr_buttons)
        
        # Horizontal button row for Import/Export
        file_buttons = QHBoxLayout()
        file_buttons.setSpacing(8) # Reduced spacing
        
        # Import from file
        self.import_button = QPushButton("Import CSV")
        self.import_button.setIcon(QIcon.fromTheme("document-open"))
        self.import_button.setFixedHeight(40) # Adjusted height
        self.import_button.setObjectName("import_button")
        file_buttons.addWidget(self.import_button)
        
        # Export to CSV
        self.export_button = QPushButton("Export CSV")
        self.export_button.setIcon(QIcon.fromTheme("document-save"))
        self.export_button.setFixedHeight(40) # Adjusted height
        self.export_button.setObjectName("export_button")
        file_buttons.addWidget(self.export_button)
        
        buttons_layout.addLayout(file_buttons)
        
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
            f"background-color: {process_colors[color_index]}; border-radius: 8px;" # Slightly less rounded
        )
        
    def reset_count(self):
        """Reset the process counter."""
        self.process_count = 0
        self.process_name_input.setText("Process 1")
        self.color_preview.setStyleSheet("background-color: #FF6347; border-radius: 8px;") # Slightly less rounded

class SchedulerControlWidget(QWidget):
    """Widget for scheduler control."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the scheduler control UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8) # Reduced margins
        layout.setSpacing(10) # Reduced spacing
        
        # Scheduler selection
        scheduler_group = QGroupBox("Scheduler")
        scheduler_form = QFormLayout()
        scheduler_form.setVerticalSpacing(10) # Reduced spacing
        scheduler_form.setHorizontalSpacing(15) # Added horizontal spacing
        
        # Scheduler type combo
        self.scheduler_combo = QComboBox()
        self.scheduler_combo.addItems([
            "FCFS", # Shortened
            "SJF (Non-Preemptive)", # Shortened
            "SJF (Preemptive)", # Shortened
            "Priority (Non-Preemptive)", # Shortened
            "Priority (Preemptive)", # Shortened
            "Round Robin"
        ])
        self.scheduler_combo.setFixedHeight(38) # Adjusted height
        self.scheduler_combo.setStyleSheet("""
            padding: 8px 12px; /* Adjusted padding */
            border-radius: 8px; /* Slightly less rounded */
            font-size: 18px;
            border: 1px solid transparent; /* Use 1px border */
        """)
        scheduler_form.addRow(QLabel("Algorithm:"), self.scheduler_combo)
        
        # Time quantum for Round Robin
        self.quantum_layout = QHBoxLayout()
        self.time_quantum_spinbox = QSpinBox()
        self.time_quantum_spinbox.setRange(1, 100)
        self.time_quantum_spinbox.setValue(2)
        self.time_quantum_spinbox.setEnabled(False)
        self.time_quantum_spinbox.setFixedHeight(38) # Adjusted height
        self.time_quantum_spinbox.setStyleSheet("""
            padding: 8px 12px; /* Adjusted padding */
            border-radius: 8px; /* Slightly less rounded */
            font-size: 18px;
            border: 1px solid transparent; /* Use 1px border */
        """)
        self.quantum_layout.addWidget(self.time_quantum_spinbox)
        
        self.quantum_label = QLabel("Quantum") # Shortened label
        self.quantum_layout.addWidget(self.quantum_label)
        
        scheduler_form.addRow(QLabel("RR Quantum:"), self.quantum_layout) # Shortened label
        
        scheduler_group.setLayout(scheduler_form)
        layout.addWidget(scheduler_group)
        
        # Simulation control group
        control_group = QGroupBox("Simulation Control")
        control_layout = QVBoxLayout()
        control_layout.setSpacing(8) # Reduced spacing
        
        # Speed control
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Speed:"))
        
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 10)
        self.speed_slider.setValue(1)  # Start at speed 1 instead of 5
        self.speed_slider.setTickPosition(QSlider.TicksBelow)
        self.speed_slider.setTickInterval(1)
        # Styles moved to apply_styles
        speed_layout.addWidget(self.speed_slider)
        
        self.speed_label = QLabel("1x")
        self.speed_label.setStyleSheet("font-weight: bold; color: #2980B9; font-size: 18px;")
        speed_layout.addWidget(self.speed_label)
        
        control_layout.addLayout(speed_layout)
        
        # Control buttons
        buttons_layout = QGridLayout()
        buttons_layout.setHorizontalSpacing(8) # Reduced spacing
        buttons_layout.setVerticalSpacing(8) # Reduced spacing
        
        # Start button with icon
        self.start_button = QPushButton("Start")
        self.start_button.setIcon(QIcon.fromTheme("media-playback-start"))
        self.start_button.setFixedHeight(40) # Adjusted height
        self.start_button.setObjectName("start_button")
        buttons_layout.addWidget(self.start_button, 0, 0)
        
        # Combined Pause/Resume button with icon
        self.pause_resume_button = QPushButton("Pause/Resume")
        self.pause_resume_button.setIcon(QIcon.fromTheme("media-playback-pause"))
        self.pause_resume_button.setEnabled(False)
        self.pause_resume_button.setFixedHeight(40) # Adjusted height
        self.pause_resume_button.setObjectName("pause_resume_button")
        buttons_layout.addWidget(self.pause_resume_button, 0, 1)
        
        control_layout.addLayout(buttons_layout)
        
        # Run all at once button
        self.run_all_button = QPushButton("Run All") # Shortened text
        self.run_all_button.setIcon(QIcon.fromTheme("media-skip-forward"))
        self.run_all_button.setFixedHeight(40) # Adjusted height
        self.run_all_button.setObjectName("run_all_button")
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
        
        # Left side panel with controls in a splitter with scroll support
        self.left_scroll_area = QScrollArea()
        self.left_scroll_area.setWidgetResizable(True)
        self.left_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.left_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.left_scroll_area.setFrameShape(QFrame.NoFrame)  # Hide the border
        
        left_scroll_content = QWidget()
        left_scroll_layout = QVBoxLayout(left_scroll_content)
        
        # Left panel with controls in a splitter
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
        
        # Add left panel to scroll area
        left_scroll_layout.addWidget(self.left_panel)
        self.left_scroll_area.setWidget(left_scroll_content)
        
        # Right side with tabs (with scroll support)
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
        self.main_splitter.addWidget(self.left_scroll_area)
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
        
        # Set initial icon based on theme - sun for dark mode, moon for light mode
        # This is the correct way: show sun in dark mode (to switch to light) and moon in light mode (to switch to dark)
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
        
        # Pause button (which can also resume)
        pause_action = QAction(QIcon.fromTheme("media-playback-pause"), "Pause/Resume", self)
        pause_action.triggered.connect(self.on_pause_resume)
        toolbar.addAction(pause_action)
        
        # Run all at once button
        run_all_action = QAction(QIcon.fromTheme("media-skip-forward"), "Run All", self)
        run_all_action.triggered.connect(self.on_run_all)
        toolbar.addAction(run_all_action)
        
        toolbar.addSeparator()
        
        # Export to CSV button
        export_action = QAction(QIcon.fromTheme("document-save"), "Export to CSV", self)
        export_action.triggered.connect(self.on_export_results)
        toolbar.addAction(export_action)
        
    def connect_signals(self):
        """Connect all signals and slots."""
        # Scheduler control signals
        self.scheduler_control.scheduler_combo.currentIndexChanged.connect(self.on_scheduler_changed)
        self.scheduler_control.speed_slider.valueChanged.connect(self.on_speed_changed)
        self.scheduler_control.start_button.clicked.connect(self.on_start)
        self.scheduler_control.pause_resume_button.clicked.connect(self.on_pause_resume)
        self.scheduler_control.run_all_button.clicked.connect(self.on_run_all)
        
        # Process control signals
        self.process_control.add_process_button.clicked.connect(self.on_add_process)
        self.process_control.remove_all_button.clicked.connect(self.on_remove_all)
        self.process_control.reset_button.clicked.connect(self.on_reset)
        self.process_control.import_button.clicked.connect(self.on_import_processes)
        self.process_control.export_button.clicked.connect(self.on_export_results)
        
        # Set the process table remove callback
        self.process_table.set_remove_callback(self.on_remove_process)
        
    def apply_styles(self, dark_mode):
        """Apply styling to the application based on the selected theme."""
        # Common font
        font = QFont("Segoe UI", 10) # Use a standard modern font
        QApplication.setFont(font)

        # Define color palettes (Darker Buttons, Adjusted Contrast)
        dark_colors = {
            "window": "#2B2B2B", # Slightly darker window
            "base": "#212121", # Darker base
            "alternate_base": "#272727",
            "button": "#3E3E3E", # Darker button base
            "button_hover": "#4A4A4A",
            "button_pressed": "#353535",
            "text": "#EDEDED", # Slightly brighter text
            "highlight": "#4A90E2", # Brighter highlight blue
            "highlighted_text": "#FFFFFF",
            "border": "#505050", # Adjusted border
            "group_bg": "#2F2F2F", # Adjusted group bg
            "group_title": "#77C6FF", # Adjusted title color
            # Button Colors (Darker Tones)
            "red": "#C62828", # Darker Red
            "red_hover": "#D32F2F",
            "green": "#2E7D32", # Darker Green
            "green_hover": "#388E3C",
            "blue": "#1565C0", # Darker Blue
            "blue_hover": "#1976D2",
            "amber": "#EF6C00", # Darker Amber/Orange
            "amber_hover": "#F57C00",
            "purple": "#6A1B9A", # Darker Purple
            "purple_hover": "#7B1FA2",
            "slider_groove": "#404040",
            "slider_handle": "#77C6FF",
            "slider_handle_border": "#4A90E2",
            "table_header": "#3A3A3A",
            "scrollbar_bg": "#333333",
            "scrollbar_handle": "#555555",
            "scrollbar_handle_hover": "#666666",
        }

        light_colors = {
            "window": "#F9F9F9", # Slightly off-white
            "base": "#FFFFFF",
            "alternate_base": "#F0F0F0", # More distinct alternate
            "button": "#DCDCDC", # Darker button base
            "button_hover": "#CFCFCF",
            "button_pressed": "#BDBDBD",
            "text": "#1A1A1A", # Darker text
            "highlight": "#007AFF", # Standard vibrant blue
            "highlighted_text": "#FFFFFF",
            "border": "#C0C0C0", # Darker border
            "group_bg": "#FFFFFF",
            "group_title": "#005EB8", # Darker title blue
             # Button Colors (Darker Tones)
            "red": "#D32F2F", # Darker Red
            "red_hover": "#C62828",
            "green": "#388E3C", # Darker Green
            "green_hover": "#2E7D32",
            "blue": "#1976D2", # Darker Blue
            "blue_hover": "#1565C0",
            "amber": "#F57C00", # Darker Amber/Orange
            "amber_hover": "#EF6C00",
            "purple": "#7B1FA2", # Darker Purple
            "purple_hover": "#6A1B9A",
            "slider_groove": "#E0E0E0",
            "slider_handle": "#007AFF",
            "slider_handle_border": "#005EB8",
            "table_header": "#EAEAEA",
            "scrollbar_bg": "#F0F0F0",
            "scrollbar_handle": "#BDBDBD",
            "scrollbar_handle_hover": "#ADADAD",
        }

        colors = dark_colors if dark_mode else light_colors
        # Ensure good contrast for text on colored buttons
        button_text_color = "#FFFFFF" # White generally works well
        # Amber/Yellow might need dark text in light mode
        amber_button_text_color = colors["text"] if dark_mode else "#1A1A1A"
        # Theme button text color should match general text color
        theme_button_text_color = colors["text"]

        app = QApplication.instance()
        app.setStyle(QStyleFactory.create("Fusion"))

        # Apply palette colors
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(colors["window"]))
        palette.setColor(QPalette.WindowText, QColor(colors["text"]))
        palette.setColor(QPalette.Base, QColor(colors["base"]))
        palette.setColor(QPalette.AlternateBase, QColor(colors["alternate_base"]))
        palette.setColor(QPalette.ToolTipBase, QColor(colors["base"]))
        palette.setColor(QPalette.ToolTipText, QColor(colors["text"]))
        palette.setColor(QPalette.Text, QColor(colors["text"]))
        palette.setColor(QPalette.Button, QColor(colors["button"]))
        palette.setColor(QPalette.ButtonText, QColor(colors["text"])) # Default button text
        palette.setColor(QPalette.BrightText, QColor(colors["red"]))
        palette.setColor(QPalette.Link, QColor(colors["highlight"]))
        palette.setColor(QPalette.Highlight, QColor(colors["highlight"]))
        palette.setColor(QPalette.HighlightedText, QColor(colors["highlighted_text"]))
        # Set disabled colors for better visibility
        disabled_text_color = QColor(colors["text"]).lighter(150) if dark_mode else QColor(colors["text"]).darker(150)
        disabled_button_color = QColor(colors["button"]).lighter(110) if dark_mode else QColor(colors["button"]).darker(110)
        palette.setColor(QPalette.Disabled, QPalette.Text, disabled_text_color)
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, disabled_text_color)
        palette.setColor(QPalette.Disabled, QPalette.Button, disabled_button_color)

        app.setPalette(palette)

        # Apply global stylesheet (with updated colors and potentially minor tweaks)
        app.setStyleSheet(f"""\
            QMainWindow, QDialog {{
                background-color: {colors["window"]};
                color: {colors["text"]};
            }}
            QWidget {{ /* Apply font size globally */
                font-size: 10pt; /* Base font size */
            }}
            QGroupBox {{
                border: 1px solid {colors["border"]};
                border-radius: 8px;
                padding-top: 20px;
                margin-top: 10px;
                background-color: {colors["group_bg"]};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px 10px;
                margin-left: 12px;
                background-color: {colors["group_bg"]};
                color: {colors["group_title"]};
                font-weight: bold;
                font-size: 11pt;
                border-radius: 4px;
            }}

            /* Base Button Styles */
            QPushButton {{
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                border: 1px solid {colors["border"]};
                color: {colors["text"]};
                background-color: {colors["button"]};
                min-height: 30px;
                min-width: 70px;
            }}
            QPushButton:hover {{
                background-color: {colors["button_hover"]};
                border-color: {QColor(colors["border"]).lighter(120).name() if dark_mode else QColor(colors["border"]).darker(120).name()};
            }}
            QPushButton:pressed {{ background-color: {colors["button_pressed"]}; }}
            QPushButton:disabled {{
                background-color: {palette.color(QPalette.Disabled, QPalette.Button).name()};
                color: {palette.color(QPalette.Disabled, QPalette.ButtonText).name()};
                border-color: {palette.color(QPalette.Disabled, QPalette.Button).name()};
            }}

            /* Colored Buttons */
            QPushButton#add_process_button {{ background-color: {colors["green"]}; color: {button_text_color}; border-color: {colors["green"]}; }}
            QPushButton#add_process_button:hover {{ background-color: {colors["green_hover"]}; border-color: {colors["green_hover"]}; }}
            QPushButton#remove_all_button {{ background-color: {colors["red"]}; color: {button_text_color}; border-color: {colors["red"]}; }}
            QPushButton#remove_all_button:hover {{ background-color: {colors["red_hover"]}; border-color: {colors["red_hover"]}; }}
            QPushButton#reset_button {{ background-color: {colors["amber"]}; color: {amber_button_text_color}; border-color: {colors["amber"]}; }}
            QPushButton#reset_button:hover {{ background-color: {colors["amber_hover"]}; border-color: {colors["amber_hover"]}; }}
            QPushButton#import_button, QPushButton#export_button {{ background-color: {colors["blue"]}; color: {button_text_color}; border-color: {colors["blue"]}; }}
            QPushButton#import_button:hover, QPushButton#export_button:hover {{ background-color: {colors["blue_hover"]}; border-color: {colors["blue_hover"]}; }}
            QPushButton#start_button {{ background-color: {colors["green"]}; color: {button_text_color}; border-color: {colors["green"]}; }}
            QPushButton#start_button:hover {{ background-color: {colors["green_hover"]}; border-color: {colors["green_hover"]}; }}
            QPushButton#pause_resume_button {{ background-color: {colors["amber"]}; color: {amber_button_text_color}; border-color: {colors["amber"]}; }}
            QPushButton#pause_resume_button:hover {{ background-color: {colors["amber_hover"]}; border-color: {colors["amber_hover"]}; }}
            QPushButton#run_all_button {{ background-color: {colors["purple"]}; color: {button_text_color}; border-color: {colors["purple"]}; }}
            QPushButton#run_all_button:hover {{ background-color: {colors["purple_hover"]}; border-color: {colors["purple_hover"]}; }}

            /* Form Elements */
            QComboBox, QSpinBox, QLineEdit {{
                border: 1px solid {colors["border"]};
                border-radius: 6px;
                padding: 6px 10px;
                background-color: {colors["base"]};
                color: {colors["text"]};
                selection-background-color: {colors["highlight"]};
                selection-color: {colors["highlighted_text"]};
                min-height: 28px;
                font-size: 10pt; /* Ensure font size consistency */
            }}
            QComboBox QAbstractItemView {{ /* Style the dropdown list */
                background-color: {colors["base"]};
                color: {colors["text"]};
                border: 1px solid {colors["border"]};
                selection-background-color: {colors["highlight"]};
                selection-color: {colors["highlighted_text"]};
                padding: 4px;
            }}
            QComboBox:hover, QSpinBox:hover, QLineEdit:hover {{
                border-color: {QColor(colors["border"]).lighter(130).name() if dark_mode else QColor(colors["border"]).darker(130).name()};
            }}
            QComboBox:focus, QSpinBox:focus, QLineEdit:focus {{
                border-color: {colors["highlight"]};
                background-color: {QColor(colors["base"]).lighter(105).name() if dark_mode else QColor(colors["base"]).darker(102).name()};
            }}
            QComboBox::drop-down {{
                border: none;
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 28px;
                border-left: 1px solid {colors["border"]};
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
                background-color: {colors["button"]};
            }}
            QComboBox::drop-down:hover {{ background-color: {colors["button_hover"]}; }}
            QComboBox::down-arrow {{
                width: 14px; height: 14px;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                 subcontrol-origin: border;
                 width: 22px;
                 border-left: 1px solid {colors["border"]};
                 background-color: {colors["button"]};
                 border-radius: 0px;
            }}
            QSpinBox::up-button {{ subcontrol-position: top right; border-top-right-radius: 6px; }}
            QSpinBox::down-button {{ subcontrol-position: bottom right; border-bottom-right-radius: 6px; }}
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {{ background-color: {colors["button_hover"]}; }}
            QSpinBox::up-arrow {{ width: 12px; height: 12px; }}
            QSpinBox::down-arrow {{ width: 12px; height: 12px; }}

            /* Tabs */
            QTabWidget::pane {{
                border: 1px solid {colors["border"]};
                background-color: {colors["base"]}; /* Pane background */
                border-radius: 8px;
                border-top-left-radius: 0px; /* Align with tabs */
                margin-top: -1px; /* Overlap with tab bar */
                padding: 12px;
            }}
            QTabBar {{
                qproperty-drawBase: 0; /* Remove the default base line under the tabs */
                margin-bottom: -1px; /* Ensure tabs slightly overlap the pane */
                alignment: Qt.AlignLeft; /* Align tabs to the left */
            }}
            QTabBar::tab {{
                background-color: transparent; /* Make inactive tabs transparent */
                color: {QColor(colors["text"]).darker(130).name() if not dark_mode else QColor(colors["text"]).lighter(130).name()}; /* Dim inactive tab text more */
                border: 1px solid transparent; /* Transparent border initially */
                border-bottom: 2px solid {colors["border"]}; /* Slightly thicker underline for inactive tabs */
                padding: 10px 25px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 5px;
                min-width: 140px;
                font-weight: normal;
                font-size: 11pt;
                /* Removed transition property - Qt stylesheets don't support CSS transitions directly */
            }}
            QTabBar::tab:selected {{
                background-color: {colors["base"]}; /* Selected tab matches pane background */
                color: {colors["highlight"]}; /* Highlight color for selected tab text */
                font-weight: bold;
                border: 1px solid {colors["border"]};
                border-bottom: 2px solid {colors["base"]}; /* Make bottom border match background to blend */
                margin-bottom: -1px; /* Pull selected tab down slightly */
                border-top: 3px solid {colors["highlight"]}; /* Thicker highlight top border */
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {QColor(colors["button_hover"]).lighter(105).name() if dark_mode else QColor(colors["button_hover"]).darker(105).name()}; /* Subtle hover background */
                color: {colors["text"]}; /* Full text color on hover */
                border: 1px solid transparent; /* Keep border transparent on hover */
                border-bottom: 2px solid {QColor(colors["border"]).lighter(110).name() if dark_mode else QColor(colors["border"]).darker(110).name()}; /* Slightly change underline on hover */
            }}
            QTabBar::tab:last {{
                margin-right: 0; /* No margin for the last tab */
            }}

            /* Scrollbars */
            QScrollBar:vertical {{
                background-color: {colors["scrollbar_bg"]};
                width: 12px;
                margin: 0px 0px 0px 0px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {colors["scrollbar_handle"]};
                min-height: 30px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {colors["scrollbar_handle_hover"]};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
                background: none;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
             QScrollBar:horizontal {{
                background-color: {colors["scrollbar_bg"]};
                height: 12px;
                margin: 0px 0px 0px 0px;
                border-radius: 6px;
            }}
            QScrollBar::handle:horizontal {{
                background-color: {colors["scrollbar_handle"]};
                min-width: 30px;
                border-radius: 6px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: {colors["scrollbar_handle_hover"]};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
                background: none;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: none;
            }}

            /* Slider */
            QSlider::groove:horizontal {{
                height: 8px;
                background: {colors["slider_groove"]};
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {colors["slider_handle"]};
                border: 1px solid {colors["slider_handle_border"]};
                width: 18px;
                height: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {QColor(colors["slider_handle"]).lighter(115).name()};
                border: 1px solid {QColor(colors["slider_handle_border"]).lighter(115).name()};
            }}

            /* Tables */
            QTableWidget {{
                gridline-color: transparent; /* Hide grid lines */
                background-color: {colors["base"]};
                alternate-background-color: {colors["alternate_base"]};
                border: 1px solid {colors["border"]};
                border-radius: 8px;
                padding: 0px; /* Remove padding around the table itself */
                selection-background-color: {colors["highlight"]}; /* Explicit selection color */
                selection-color: {colors["highlighted_text"]};
            }}
            QHeaderView::section {{ /* Style for both horizontal and vertical headers */
                background-color: {colors["table_header"]};
                color: {colors["text"]};
                padding: 10px 8px; /* Increased padding */
                border: none; /* Remove default borders */
                font-weight: bold;
                font-size: 10pt;
            }}
            QHeaderView::section:horizontal {{
                border-bottom: 2px solid {colors["highlight"]}; /* Highlight bottom border */
                border-right: 1px solid {colors["border"]}; /* Separator line */
            }}
            QHeaderView::section:horizontal:last {{
                border-right: none; /* No right border for the last header */
            }}
            QTableWidget::item {{ /* Style for individual cells */
                padding: 10px 8px; /* Increased cell padding */
                border: none; /* Remove default cell borders */
                /* Use alternating row colors defined in palette */
            }}
            /* Add subtle bottom border to rows, except the last one */
            QTableWidget QAbstractItemView::item {{
                 border-bottom: 1px solid {colors["border"]};
            }}
            /* Remove bottom border for items in the last visible row */
            /* Note: This is tricky with stylesheets, might not be perfect */

            QTableWidget::item:selected {{
                /* Selection colors handled by QTableWidget setting */
            }}
            /* Status Item Styling - More distinct backgrounds */
            QTableWidget QTableWidgetItem[userRole="Running"] {{
                background-color: {QColor(colors['green']).lighter(150).name() if dark_mode else QColor(colors['green']).lighter(180).name()};
                color: {'#000000' if dark_mode else '#000000'}; /* Ensure contrast */
                font-weight: bold;
            }}
            QTableWidget QTableWidgetItem[userRole="Completed"] {{
                background-color: {QColor(colors['border']).lighter(105).name() if dark_mode else QColor(colors['border']).lighter(140).name()};
                color: {QColor(colors['text']).darker(130).name() if dark_mode else QColor(colors['text']).darker(160).name()};
                font-style: italic;
            }}
            QTableWidget QTableWidgetItem[userRole="Waiting"] {{
                background-color: {QColor(colors['amber']).lighter(150).name() if dark_mode else QColor(colors['amber']).lighter(180).name()};
                color: {'#000000' if dark_mode else '#000000'}; /* Ensure contrast */
            }}
            QTableWidget QTableWidgetItem[userRole="Not Arrived"] {{
                background-color: transparent;
                color: {QColor(colors['text']).darker(140).name() if dark_mode else QColor(colors['text']).darker(170).name()};
                font-style: italic;
            }}
            /* Summary Row Styling - Clearer separation */
            QTableWidget QTableWidgetItem[userRole="summary_label"] {{
                background-color: {QColor(colors["table_header"]).lighter(110).name() if dark_mode else QColor(colors["table_header"]).darker(105).name()};
                color: {colors["text"]};
                padding-right: 15px;
                border-top: 1px solid {colors["highlight"]}; /* Separator line above */
                border-bottom: none;
            }}
             QTableWidget QTableWidgetItem[userRole="summary_value"] {{
                background-color: {QColor(colors["table_header"]).lighter(110).name() if dark_mode else QColor(colors["table_header"]).darker(105).name()};
                color: {colors["highlight"]};
                border-top: 1px solid {colors["highlight"]}; /* Separator line above */
                border-bottom: none;
            }}

            /* Progress Bar in Table - More refined look */
            QTableView QProgressBar {{
                border: 1px solid {colors["border"]};
                border-radius: 6px; /* Slightly less rounded */
                background-color: {colors["base"]};
                text-align: center;
                color: {colors["text"]};
                font-size: 9pt;
                height: 18px; /* Consistent height */
                margin: 2px 0; /* Add slight vertical margin */
            }}
            QTableView QProgressBar::chunk {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {QColor(colors['highlight']).lighter(115).name()}, stop:1 {colors['highlight']});
                border-radius: 6px;
                margin: 1px; /* Add margin to chunk for inset effect */
            }}

            /* Remove Button in Table - More visible hover/pressed */
            QPushButton#remove_table_button {{
                background-color: {colors['red']}; /* Red background */
                color: {button_text_color}; /* White text */
                border: none;
                border-radius: 4px; /* Match other buttons */
                padding: 5px; /* Increased padding */
                qproperty-iconSize: 20px 20px; /* Slightly larger icon */
                margin: 0; /* Remove any default margin */
                font-weight: bold; /* Make text bold */
            }}
            QPushButton#remove_table_button:hover {{
                background-color: {colors['red_hover']}; /* Darker red hover */
            }}
            QPushButton#remove_table_button:pressed {{
                background-color: {QColor(colors['red']).darker(120).name()}; /* Even darker red when pressed */
            }}

            /* Tabs */
            QTabWidget::pane {{
                border: 1px solid {colors["border"]};
                background-color: {colors["base"]}; /* Pane background */
                border-radius: 8px;
                border-top-left-radius: 0px; /* Align with tabs */
                margin-top: -1px; /* Overlap with tab bar */
                padding: 12px;
            }}
            QTabBar {{
                qproperty-drawBase: 0; /* Remove the default base line under the tabs */
                margin-bottom: -1px; /* Ensure tabs slightly overlap the pane */
                alignment: Qt.AlignLeft; /* Align tabs to the left */
            }}
            QTabBar::tab {{
                background-color: transparent; /* Make inactive tabs transparent */
                color: {QColor(colors["text"]).darker(130).name() if not dark_mode else QColor(colors["text"]).lighter(130).name()}; /* Dim inactive tab text more */
                border: 1px solid transparent; /* Transparent border initially */
                border-bottom: 2px solid {colors["border"]}; /* Slightly thicker underline for inactive tabs */
                padding: 10px 25px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 5px;
                min-width: 140px;
                font-weight: normal;
                font-size: 11pt;
                /* Removed transition property - Qt stylesheets don't support CSS transitions directly */
            }}
            QTabBar::tab:selected {{
                background-color: {colors["base"]}; /* Selected tab matches pane background */
                color: {colors["highlight"]}; /* Highlight color for selected tab text */
                font-weight: bold;
                border: 1px solid {colors["border"]};
                border-bottom: 2px solid {colors["base"]}; /* Make bottom border match background to blend */
                margin-bottom: -1px; /* Pull selected tab down slightly */
                border-top: 3px solid {colors["highlight"]}; /* Thicker highlight top border */
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {QColor(colors["button_hover"]).lighter(105).name() if dark_mode else QColor(colors["button_hover"]).darker(105).name()}; /* Subtle hover background */
                color: {colors["text"]}; /* Full text color on hover */
                border: 1px solid transparent; /* Keep border transparent on hover */
                border-bottom: 2px solid {QColor(colors["border"]).lighter(110).name() if dark_mode else QColor(colors["border"]).darker(110).name()}; /* Slightly change underline on hover */
            }}
            QTabBar::tab:last {{
                margin-right: 0; /* No margin for the last tab */
            }}

            /* Scrollbars */
            QScrollBar:vertical {{
                background-color: {colors["scrollbar_bg"]};
                width: 12px;
                margin: 0px 0px 0px 0px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {colors["scrollbar_handle"]};
                min-height: 30px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {colors["scrollbar_handle_hover"]};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
                background: none;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
             QScrollBar:horizontal {{
                background-color: {colors["scrollbar_bg"]};
                height: 12px;
                margin: 0px 0px 0px 0px;
                border-radius: 6px;
            }}
            QScrollBar::handle:horizontal {{
                background-color: {colors["scrollbar_handle"]};
                min-width: 30px;
                border-radius: 6px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: {colors["scrollbar_handle_hover"]};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
                background: none;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: none;
            }}

            /* Slider */
            QSlider::groove:horizontal {{
                height: 8px;
                background: {colors["slider_groove"]};
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {colors["slider_handle"]};
                border: 1px solid {colors["slider_handle_border"]};
                width: 18px;
                height: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {QColor(colors["slider_handle"]).lighter(115).name()};
                border: 1px solid {QColor(colors["slider_handle_border"]).lighter(115).name()};
            }}

            /* Tables */
            QTableWidget {{
                gridline-color: transparent; /* Hide grid lines */
                background-color: {colors["base"]};
                alternate-background-color: {colors["alternate_base"]};
                border: 1px solid {colors["border"]};
                border-radius: 8px;
                padding: 0px; /* Remove padding around the table itself */
                selection-background-color: {colors["highlight"]}; /* Explicit selection color */
                selection-color: {colors["highlighted_text"]};
            }}
            QHeaderView::section {{ /* Style for both horizontal and vertical headers */
                background-color: {colors["table_header"]};
                color: {colors["text"]};
                padding: 10px 8px; /* Increased padding */
                border: none; /* Remove default borders */
                font-weight: bold;
                font-size: 10pt;
            }}
            QHeaderView::section:horizontal {{
                border-bottom: 2px solid {colors["highlight"]}; /* Highlight bottom border */
                border-right: 1px solid {colors["border"]}; /* Separator line */
            }}
            QHeaderView::section:horizontal:last {{
                border-right: none; /* No right border for the last header */
            }}
            QTableWidget::item {{ /* Style for individual cells */
                padding: 10px 8px; /* Increased cell padding */
                border: none; /* Remove default cell borders */
                /* Use alternating row colors defined in palette */
            }}
            /* Add subtle bottom border to rows, except the last one */
            QTableWidget QAbstractItemView::item {{
                 border-bottom: 1px solid {colors["border"]};
            }}
            /* Remove bottom border for items in the last visible row */
            /* Note: This is tricky with stylesheets, might not be perfect */

            QTableWidget::item:selected {{
                /* Selection colors handled by QTableWidget setting */
            }}
            /* Status Item Styling - More distinct backgrounds */
            QTableWidget QTableWidgetItem[userRole="Running"] {{
                background-color: {QColor(colors['green']).lighter(150).name() if dark_mode else QColor(colors['green']).lighter(180).name()};
                color: {'#000000' if dark_mode else '#000000'}; /* Ensure contrast */
                font-weight: bold;
            }}
            QTableWidget QTableWidgetItem[userRole="Completed"] {{
                background-color: {QColor(colors['border']).lighter(105).name() if dark_mode else QColor(colors['border']).lighter(140).name()};
                color: {QColor(colors['text']).darker(130).name() if dark_mode else QColor(colors['text']).darker(160).name()};
                font-style: italic;
            }}
            QTableWidget QTableWidgetItem[userRole="Waiting"] {{
                background-color: {QColor(colors['amber']).lighter(150).name() if dark_mode else QColor(colors['amber']).lighter(180).name()};
                color: {'#000000' if dark_mode else '#000000'}; /* Ensure contrast */
            }}
            QTableWidget QTableWidgetItem[userRole="Not Arrived"] {{
                background-color: transparent;
                color: {QColor(colors['text']).darker(140).name() if dark_mode else QColor(colors['text']).darker(170).name()};
                font-style: italic;
            }}
            /* Summary Row Styling - Clearer separation */
            QTableWidget QTableWidgetItem[userRole="summary_label"] {{
                background-color: {QColor(colors["table_header"]).lighter(110).name() if dark_mode else QColor(colors["table_header"]).darker(105).name()};
                color: {colors["text"]};
                padding-right: 15px;
                border-top: 1px solid {colors["highlight"]}; /* Separator line above */
                border-bottom: none;
            }}
             QTableWidget QTableWidgetItem[userRole="summary_value"] {{
                background-color: {QColor(colors["table_header"]).lighter(110).name() if dark_mode else QColor(colors["table_header"]).darker(105).name()};
                color: {colors["highlight"]};
                border-top: 1px solid {colors["highlight"]}; /* Separator line above */
                border-bottom: none;
            }}

            /* Progress Bar in Table - More refined look */
            QTableView QProgressBar {{
                border: 1px solid {colors["border"]};
                border-radius: 6px; /* Slightly less rounded */
                background-color: {colors["base"]};
                text-align: center;
                color: {colors["text"]};
                font-size: 9pt;
                height: 18px; /* Consistent height */
                margin: 2px 0; /* Add slight vertical margin */
            }}
            QTableView QProgressBar::chunk {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {QColor(colors['highlight']).lighter(115).name()}, stop:1 {colors['highlight']});
                border-radius: 6px;
                margin: 1px; /* Add margin to chunk for inset effect */
            }}

            /* Remove Button in Table - More visible hover/pressed */
            QPushButton#remove_table_button {{
                background-color: {colors['red']}; /* Red background */
                color: {button_text_color}; /* White text */
                border: none;
                border-radius: 4px; /* Match other buttons */
                padding: 5px; /* Increased padding */
                qproperty-iconSize: 20px 20px; /* Slightly larger icon */
                margin: 0; /* Remove any default margin */
                font-weight: bold; /* Make text bold */
            }}
            QPushButton#remove_table_button:hover {{
                background-color: {colors['red_hover']}; /* Darker red hover */
            }}
            QPushButton#remove_table_button:pressed {{
                background-color: {QColor(colors['red']).darker(120).name()}; /* Even darker red when pressed */
            }}

            /* Tabs */
            QTabWidget::pane {{
                border: 1px solid {colors["border"]};
                background-color: {colors["base"]}; /* Pane background */
                border-radius: 8px;
                border-top-left-radius: 0px; /* Align with tabs */
                margin-top: -1px; /* Overlap with tab bar */
                padding: 12px;
            }}
            QTabBar {{
                qproperty-drawBase: 0; /* Remove the default base line under the tabs */
                margin-bottom: -1px; /* Ensure tabs slightly overlap the pane */
                alignment: Qt.AlignLeft; /* Align tabs to the left */
            }}
            QTabBar::tab {{
                background-color: transparent; /* Make inactive tabs transparent */
                color: {QColor(colors["text"]).darker(130).name() if not dark_mode else QColor(colors["text"]).lighter(130).name()}; /* Dim inactive tab text more */
                border: 1px solid transparent; /* Transparent border initially */
                border-bottom: 2px solid {colors["border"]}; /* Slightly thicker underline for inactive tabs */
                padding: 10px 25px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 5px;
                min-width: 140px;
                font-weight: normal;
                font-size: 11pt;
                /* Removed transition property - Qt stylesheets don't support CSS transitions directly */
            }}
            QTabBar::tab:selected {{
                background-color: {colors["base"]}; /* Selected tab matches pane background */
                color: {colors["highlight"]}; /* Highlight color for selected tab text */
                font-weight: bold;
                border: 1px solid {colors["border"]};
                border-bottom: 2px solid {colors["base"]}; /* Make bottom border match background to blend */
                margin-bottom: -1px; /* Pull selected tab down slightly */
                border-top: 3px solid {colors["highlight"]}; /* Thicker highlight top border */
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {QColor(colors["button_hover"]).lighter(105).name() if dark_mode else QColor(colors["button_hover"]).darker(105).name()}; /* Subtle hover background */
                color: {colors["text"]}; /* Full text color on hover */
                border: 1px solid transparent; /* Keep border transparent on hover */
                border-bottom: 2px solid {QColor(colors["border"]).lighter(110).name() if dark_mode else QColor(colors["border"]).darker(110).name()}; /* Slightly change underline on hover */
            }}
            QTabBar::tab:last {{
                margin-right: 0; /* No margin for the last tab */
            }}

            /* Scrollbars */
            QScrollBar:vertical {{
                background-color: {colors["scrollbar_bg"]};
                width: 12px;
                margin: 0px 0px 0px 0px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {colors["scrollbar_handle"]};
                min-height: 30px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {colors["scrollbar_handle_hover"]};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
                background: none;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
             QScrollBar:horizontal {{
                background-color: {colors["scrollbar_bg"]};
                height: 12px;
                margin: 0px 0px 0px 0px;
                border-radius: 6px;
            }}
            QScrollBar::handle:horizontal {{
                background-color: {colors["scrollbar_handle"]};
                min-width: 30px;
                border-radius: 6px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: {colors["scrollbar_handle_hover"]};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
                background: none;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: none;
            }}

            /* Slider */
            QSlider::groove:horizontal {{
                height: 8px;
                background: {colors["slider_groove"]};
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {colors["slider_handle"]};
                border: 1px solid {colors["slider_handle_border"]};
                width: 18px;
                height: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {QColor(colors["slider_handle"]).lighter(115).name()};
                border: 1px solid {QColor(colors["slider_handle_border"]).lighter(115).name()};
            }}

            /* Tables */
            QTableWidget {{
                gridline-color: transparent; /* Hide grid lines */
                background-color: {colors["base"]};
                alternate-background-color: {colors["alternate_base"]};
                border: 1px solid {colors["border"]};
                border-radius: 8px;
                padding: 0px; /* Remove padding around the table itself */
                selection-background-color: {colors["highlight"]}; /* Explicit selection color */
                selection-color: {colors["highlighted_text"]};
            }}
            QHeaderView::section {{ /* Style for both horizontal and vertical headers */
                background-color: {colors["table_header"]};
                color: {colors["text"]};
                padding: 10px 8px; /* Increased padding */
                border: none; /* Remove default borders */
                font-weight: bold;
                font-size: 10pt;
            }}
            QHeaderView::section:horizontal {{
                border-bottom: 2px solid {colors["highlight"]}; /* Highlight bottom border */
                border-right: 1px solid {colors["border"]}; /* Separator line */
            }}
            QHeaderView::section:horizontal:last {{
                border-right: none; /* No right border for the last header */
            }}
            QTableWidget::item {{ /* Style for individual cells */
                padding: 10px 8px; /* Increased cell padding */
                border: none; /* Remove default cell borders */
                /* Use alternating row colors defined in palette */
            }}
            /* Add subtle bottom border to rows, except the last one */
            QTableWidget QAbstractItemView::item {{
                 border-bottom: 1px solid {colors["border"]};
            }}
            /* Remove bottom border for items in the last visible row */
            /* Note: This is tricky with stylesheets, might not be perfect */

            QTableWidget::item:selected {{
                /* Selection colors handled by QTableWidget setting */
            }}
            /* Status Item Styling - More distinct backgrounds */
            QTableWidget QTableWidgetItem[userRole="Running"] {{
                background-color: {QColor(colors['green']).lighter(150).name() if dark_mode else QColor(colors['green']).lighter(180).name()};
                color: {'#000000' if dark_mode else '#000000'}; /* Ensure contrast */
                font-weight: bold;
            }}
            QTableWidget QTableWidgetItem[userRole="Completed"] {{
                background-color: {QColor(colors['border']).lighter(105).name() if dark_mode else QColor(colors['border']).lighter(140).name()};
                color: {QColor(colors['text']).darker(130).name() if dark_mode else QColor(colors['text']).darker(160).name()};
                font-style: italic;
            }}
            QTableWidget QTableWidgetItem[userRole="Waiting"] {{
                background-color: {QColor(colors['amber']).lighter(150).name() if dark_mode else QColor(colors['amber']).lighter(180).name()};
                color: {'#000000' if dark_mode else '#000000'}; /* Ensure contrast */
            }}
            QTableWidget QTableWidgetItem[userRole="Not Arrived"] {{
                background-color: transparent;
                color: {QColor(colors['text']).darker(140).name() if dark_mode else QColor(colors['text']).darker(170).name()};
                font-style: italic;
            }}
            /* Summary Row Styling - Clearer separation */
            QTableWidget QTableWidgetItem[userRole="summary_label"] {{
                background-color: {QColor(colors["table_header"]).lighter(110).name() if dark_mode else QColor(colors["table_header"]).darker(105).name()};
                color: {colors["text"]};
                padding-right: 15px;
                border-top: 1px solid {colors["highlight"]}; /* Separator line above */
                border-bottom: none;
            }}
             QTableWidget QTableWidgetItem[userRole="summary_value"] {{
                background-color: {QColor(colors["table_header"]).lighter(110).name() if dark_mode else QColor(colors["table_header"]).darker(105).name()};
                color: {colors["highlight"]};
                border-top: 1px solid {colors["highlight"]}; /* Separator line above */
                border-bottom: none;
            }}

            /* Progress Bar in Table - More refined look */
            QTableView QProgressBar {{
                border: 1px solid {colors["border"]};
                border-radius: 6px; /* Slightly less rounded */
                background-color: {colors["base"]};
                text-align: center;
                color: {colors["text"]};
                font-size: 9pt;
                height: 18px; /* Consistent height */
                margin: 2px 0; /* Add slight vertical margin */
            }}
            QTableView QProgressBar::chunk {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {QColor(colors['highlight']).lighter(115).name()}, stop:1 {colors['highlight']});
                border-radius: 6px;
                margin: 1px; /* Add margin to chunk for inset effect */
            }}

            /* Remove Button in Table - More visible hover/pressed */
            QPushButton#remove_table_button {{
                background-color: {colors['red']}; /* Red background */
                color: {button_text_color}; /* White text */
                border: none;
                border-radius: 4px; /* Match other buttons */
                padding: 5px; /* Increased padding */
                qproperty-iconSize: 20px 20px; /* Slightly larger icon */
                margin: 0; /* Remove any default margin */
                font-weight: bold; /* Make text bold */
            }}
            QPushButton#remove_table_button:hover {{
                background-color: {colors['red_hover']}; /* Darker red hover */
            }}
            QPushButton#remove_table_button:pressed {{
                background-color: {QColor(colors['red']).darker(120).name()}; /* Even darker red when pressed */
            }}

            /* Tabs */
            QTabWidget::pane {{
                border: 1px solid {colors["border"]};
                background-color: {colors["base"]}; /* Pane background */
                border-radius: 8px;
                border-top-left-radius: 0px; /* Align with tabs */
                margin-top: -1px; /* Overlap with tab bar */
                padding: 12px;
            }}
            QTabBar {{
                qproperty-drawBase: 0; /* Remove the default base line under the tabs */
                margin-bottom: -1px; /* Ensure tabs slightly overlap the pane */
                alignment: Qt.AlignLeft; /* Align tabs to the left */
            }}
            QTabBar::tab {{
                background-color: transparent; /* Make inactive tabs transparent */
                color: {QColor(colors["text"]).darker(130).name() if not dark_mode else QColor(colors["text"]).lighter(130).name()}; /* Dim inactive tab text more */
                border: 1px solid transparent; /* Transparent border initially */
                border-bottom: 2px solid {colors["border"]}; /* Slightly thicker underline for inactive tabs */
                padding: 10px 25px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 5px;
                min-width: 140px;
                font-weight: normal;
                font-size: 11pt;
                /* Removed transition property - Qt stylesheets don't support CSS transitions directly */
            }}
            QTabBar::tab:selected {{
                background-color: {colors["base"]}; /* Selected tab matches pane background */
                color: {colors["highlight"]}; /* Highlight color for selected tab text */
                font-weight: bold;
                border: 1px solid {colors["border"]};
                border-bottom: 2px solid {colors["base"]}; /* Make bottom border match background to blend */
                margin-bottom: -1px; /* Pull selected tab down slightly */
                border-top: 3px solid {colors["highlight"]}; /* Thicker highlight top border */
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {QColor(colors["button_hover"]).lighter(105).name() if dark_mode else QColor(colors["button_hover"]).darker(105).name()}; /* Subtle hover background */
                color: {colors["text"]}; /* Full text color on hover */
                border: 1px solid transparent; /* Keep border transparent on hover */
                border-bottom: 2px solid {QColor(colors["border"]).lighter(110).name() if dark_mode else QColor(colors["border"]).darker(110).name()}; /* Slightly change underline on hover */
            }}
            QTabBar::tab:last {{
                margin-right: 0; /* No margin for the last tab */
            }}

            /* Scrollbars */
            QScrollBar:vertical {{
                background-color: {colors["scrollbar_bg"]};
                width: 12px;
                margin: 0px 0px 0px 0px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {colors["scrollbar_handle"]};
                min-height: 30px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {colors["scrollbar_handle_hover"]};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
                background: none;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
             QScrollBar:horizontal {{
                background-color: {colors["scrollbar_bg"]};
                height: 12px;
                margin: 0px 0px 0px 0px;
                border-radius: 6px;
            }}
            QScrollBar::handle:horizontal {{
                background-color: {colors["scrollbar_handle"]};
                min-width: 30px;
                border-radius: 6px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: {colors["scrollbar_handle_hover"]};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
                background: none;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: none;
            }}

            /* Slider */
            QSlider::groove:horizontal {{
                height: 8px;
                background: {colors["slider_groove"]};
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {colors["slider_handle"]};
                border: 1px solid {colors["slider_handle_border"]};
                width: 18px;
                height: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {QColor(colors["slider_handle"]).lighter(115).name()};
                border: 1px solid {QColor(colors["slider_handle_border"]).lighter(115).name()};
            }}

            /* Tables */
            QTableWidget {{
                gridline-color: transparent; /* Hide grid lines */
                background-color: {colors["base"]};
                alternate-background-color: {colors["alternate_base"]};
                border: 1px solid {colors["border"]};
                border-radius: 8px;
                padding: 0px; /* Remove padding around the table itself */
                selection-background-color: {colors["highlight"]}; /* Explicit selection color */
                selection-color: {colors["highlighted_text"]};
            }}
            QHeaderView::section {{ /* Style for both horizontal and vertical headers */
                background-color: {colors["table_header"]};
                color: {colors["text"]};
                padding: 10px 8px; /* Increased padding */
                border: none; /* Remove default borders */
                font-weight: bold;
                font-size: 10pt;
            }}
            QHeaderView::section:horizontal {{
                border-bottom: 2px solid {colors["highlight"]}; /* Highlight bottom border */
                border-right: 1px solid {colors["border"]}; /* Separator line */
            }}
            QHeaderView::section:horizontal:last {{
                border-right: none; /* No right border for the last header */
            }}
            QTableWidget::item {{ /* Style for individual cells */
                padding: 10px 8px; /* Increased cell padding */
                border: none; /* Remove default cell borders */
                /* Use alternating row colors defined in palette */
            }}
            /* Add subtle bottom border to rows, except the last one */
            QTableWidget QAbstractItemView::item {{
                 border-bottom: 1px solid {colors["border"]};
            }}
            /* Remove bottom border for items in the last visible row */
            /* Note: This is tricky with stylesheets, might not be perfect */

            QTableWidget::item:selected {{
                /* Selection colors handled by QTableWidget setting */
            }}
            /* Status Item Styling - More distinct backgrounds */
            QTableWidget QTableWidgetItem[userRole="Running"] {{
                background-color: {QColor(colors['green']).lighter(150).name() if dark_mode else QColor(colors['green']).lighter(180).name()};
                color: {'#000000' if dark_mode else '#000000'}; /* Ensure contrast */
                font-weight: bold;
            }}
            QTableWidget QTableWidgetItem[userRole="Completed"] {{
                background-color: {QColor(colors['border']).lighter(105).name() if dark_mode else QColor(colors['border']).lighter(140).name()};
                color: {QColor(colors['text']).darker(130).name() if dark_mode else QColor(colors['text']).darker(160).name()};
                font-style: italic;
            }}
            QTableWidget QTableWidgetItem[userRole="Waiting"] {{
                background-color: {QColor(colors['amber']).lighter(150).name() if dark_mode else QColor(colors['amber']).lighter(180).name()};
                color: {'#000000' if dark_mode else '#000000'}; /* Ensure contrast */
            }}
            QTableWidget QTableWidgetItem[userRole="Not Arrived"] {{
                background-color: transparent;
                color: {QColor(colors['text']).darker(140).name() if dark_mode else QColor(colors['text']).darker(170).name()};
                font-style: italic;
            }}
            /* Summary Row Styling - Clearer separation */
            QTableWidget QTableWidgetItem[userRole="summary_label"] {{
                background-color: {QColor(colors["table_header"]).lighter(110).name() if dark_mode else QColor(colors["table_header"]).darker(105).name()};
                color: {colors["text"]};
                padding-right: 15px;
                border-top: 1px solid {colors["highlight"]}; /* Separator line above */
                border-bottom: none;
            }}
             QTableWidget QTableWidgetItem[userRole="summary_value"] {{
                background-color: {QColor(colors["table_header"]).lighter(110).name() if dark_mode else QColor(colors["table_header"]).darker(105).name()};
                color: {colors["highlight"]};
                border-top: 1px solid {colors["highlight"]}; /* Separator line above */
                border-bottom: none;
            }}

            /* Progress Bar in Table - More refined look */
            QTableView QProgressBar {{
                border: 1px solid {colors["border"]};
                border-radius: 6px; /* Slightly less rounded */
                background-color: {colors["base"]};
                text-align: center;
                color: {colors["text"]};
                font-size: 9pt;
                height: 18px; /* Consistent height */
                margin: 2px 0; /* Add slight vertical margin */
            }}
            QTableView QProgressBar::chunk {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {QColor(colors['highlight']).lighter(115).name()}, stop:1 {colors['highlight']});
                border-radius: 6px;
                margin: 1px; /* Add margin to chunk for inset effect */
            }}

            /* Remove Button in Table - More visible hover/pressed */
            QPushButton#remove_table_button {{
                background-color: {colors['red']}; /* Red background */
                color: {button_text_color}; /* White text */
                border: none;
                border-radius: 4px; /* Match other buttons */
                padding: 5px; /* Increased padding */
                qproperty-iconSize: 20px 20px; /* Slightly larger icon */
                margin: 0; /* Remove any default margin */
                font-weight: bold; /* Make text bold */
            }}
            QPushButton#remove_table_button:hover {{
                background-color: {colors['red_hover']}; /* Darker red hover */
            }}
            QPushButton#remove_table_button:pressed {{
                background-color: {QColor(colors['red']).darker(120).name()}; /* Even darker red when pressed */
            }}

            /* Tabs */
            QTabWidget::pane {{
                border: 1px solid {colors["border"]};
                background-color: {colors["base"]}; /* Pane background */
                border-radius: 8px;
                border-top-left-radius: 0px; /* Align with tabs */
                margin-top: -1px; /* Overlap with tab bar */
                padding: 12px;
            }}
            QTabBar {{
                qproperty-drawBase: 0; /* Remove the default base line under the tabs */
                margin-bottom: -1px; /* Ensure tabs slightly overlap the pane */
                alignment: Qt.AlignLeft; /* Align tabs to the left */
            }}
            QTabBar::tab {{
                background-color: transparent; /* Make inactive tabs transparent */
                color: {QColor(colors["text"]).darker(130).name() if not dark_mode else QColor(colors["text"]).lighter(130).name()}; /* Dim inactive tab text more */
                border: 1px solid transparent; /* Transparent border initially */
                border-bottom: 2px solid {colors["border"]}; /* Slightly thicker underline for inactive tabs */
                padding: 10px 25px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 5px;
                min-width: 140px;
                font-weight: normal;
                font-size: 11pt;
                /* Removed transition property - Qt stylesheets don't support CSS transitions directly */
            }}
            QTabBar::tab:selected {{
                background-color: {colors["base"]}; /* Selected tab matches pane background */
                color: {colors["highlight"]}; /* Highlight color for selected tab text */
                font-weight: bold;
                border: 1px solid {colors["border"]};
                border-bottom: 2px solid {colors["base"]}; /* Make bottom border match background to blend */
                margin-bottom: -1px; /* Pull selected tab down slightly */
                border-top: 3px solid {colors["highlight"]}; /* Thicker highlight top border */
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {QColor(colors["button_hover"]).lighter(105).name() if dark_mode else QColor(colors["button_hover"]).darker(105).name()}; /* Subtle hover background */
                color: {colors["text"]}; /* Full text color on hover */
                border: 1px solid transparent; /* Keep border transparent on hover */
                border-bottom: 2px solid {QColor(colors["border"]).lighter(110).name() if dark_mode else QColor(colors["border"]).darker(110).name()}; /* Slightly change underline on hover */
            }}
            QTabBar::tab:last {{
                margin-right: 0; /* No margin for the last tab */
            }}

            /* Scrollbars */
            QScrollBar:vertical {{
                background-color: {colors["scrollbar_bg"]};
                width: 12px;
                margin: 0px 0px 0px 0px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {colors["scrollbar_handle"]};
                min-height: 30px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {colors["scrollbar_handle_hover"]};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
                background: none;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
             QScrollBar:horizontal {{
                background-color: {colors["scrollbar_bg"]};
                height: 12px;
                margin: 0px 0px 0px 0px;
                border-radius: 6px;
            }}
            QScrollBar::handle:horizontal {{
                background-color: {colors["scrollbar_handle"]};
                min-width: 30px;
                border-radius: 6px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: {colors["scrollbar_handle_hover"]};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
                background: none;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: none;
            }}

            /* Slider */
            QSlider::groove:horizontal {{
                height: 8px;
                background: {colors["slider_groove"]};
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {colors["slider_handle"]};
                border: 1px solid {colors["slider_handle_border"]};
                width: 18px;
                height: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {QColor(colors["slider_handle"]).lighter(115).name()};
                border: 1px solid {QColor(colors["slider_handle_border"]).lighter(115).name()};
            }}

            /* Tables */
            QTableWidget {{
                gridline-color: transparent; /* Hide grid lines */
                background-color: {colors["base"]};
                alternate-background-color: {colors["alternate_base"]};
                border: 1px solid {colors["border"]};
                border-radius: 8px;
                padding: 0px; /* Remove padding around the table itself */
                selection-background-color: {colors["highlight"]}; /* Explicit selection color */
                selection-color: {colors["highlighted_text"]};
            }}
            QHeaderView::section {{ /* Style for both horizontal and vertical headers */
                background-color: {colors["table_header"]};
                color: {colors["text"]};
                padding: 10px 8px; /* Increased padding */
                border: none; /* Remove default borders */
                font-weight: bold;
                font-size: 10pt;
            }}
            QHeaderView::section:horizontal {{
                border-bottom: 2px solid {colors["highlight"]}; /* Highlight bottom border */
                border-right: 1px solid {colors["border"]}; /* Separator line */
            }}
            QHeaderView::section:horizontal:last {{
                border-right: none; /* No right border for the last header */
            }}
            QTableWidget::item {{ /* Style for individual cells */
                padding: 10px 8px; /* Increased cell padding */
                border: none; /* Remove default cell borders */
                /* Use alternating row colors defined in palette */
            }}
            /* Add subtle bottom border to rows, except the last one */
            QTableWidget QAbstractItemView::item {{
                 border-bottom: 1px solid {colors["border"]};
            }}
            /* Remove bottom border for items in the last visible row */
            /* Note: This is tricky with stylesheets, might not be perfect */

            QTableWidget::item:selected {{
                /* Selection colors handled by QTableWidget setting */
            }}
            /* Status Item Styling - More distinct backgrounds */
            QTableWidget QTableWidgetItem[userRole="Running"] {{
                background-color: {QColor(colors['green']).lighter(150).name() if dark_mode else QColor(colors['green']).lighter(180).name()};
                color: {'#000000' if dark_mode else '#000000'}; /* Ensure contrast */
                font-weight: bold;
            }}
            QTableWidget QTableWidgetItem[userRole="Completed"] {{
                background-color: {QColor(colors['border']).lighter(105).name() if dark_mode else QColor(colors['border']).lighter(140).name()};
                color: {QColor(colors['text']).darker(130).name() if dark_mode else QColor(colors['text']).darker(160).name()};
                font-style: italic;
            }}
            QTableWidget QTableWidgetItem[userRole="Waiting"] {{
                background-color: {QColor(colors['amber']).lighter(150).name() if dark_mode else QColor(colors['amber']).lighter(180).name()};
                color: {'#000000' if dark_mode else '#000000'}; /* Ensure contrast */
            }}
            QTableWidget QTableWidgetItem[userRole="Not Arrived"] {{
                background-color: transparent;
                color: {QColor(colors['text']).darker(140).name() if dark_mode else QColor(colors['text']).darker(170).name()};
                font-style: italic;
            }}
            /* Summary Row Styling - Clearer separation */
            QTableWidget QTableWidgetItem[userRole="summary_label"] {{
                background-color: {QColor(colors["table_header"]).lighter(110).name() if dark_mode else QColor(colors["table_header"]).darker(105).name()};
                color: {colors["text"]};
                padding-right: 15px;
                border-top: 1px solid {colors["highlight"]}; /* Separator line above */
                border-bottom: none;
            }}
             QTableWidget QTableWidgetItem[userRole="summary_value"] {{
                background-color: {QColor(colors["table_header"]).lighter(110).name() if dark_mode else QColor(colors["table_header"]).darker(105).name()};
                color: {colors["highlight"]};
                border-top: 1px solid {colors["highlight"]}; /* Separator line above */
                border-bottom: none;
            }}

            /* Progress Bar in Table - More refined look */
            QTableView QProgressBar {{
                border: 1px solid {colors["border"]};
                border-radius: 6px; /* Slightly less rounded */
                background-color: {colors["base"]};
                text-align: center;
                color: {colors["text"]};
                font-size: 9pt;
                height: 18px; /* Consistent height */
                margin: 2px 0; /* Add slight vertical margin */
            }}
            QTableView QProgressBar::chunk {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {QColor(colors['highlight']).lighter(115).name()}, stop:1 {colors['highlight']});
                border-radius: 6px;
                margin: 1px; /* Add margin to chunk for inset effect */
            }}

            /* Remove Button in Table - More visible hover/pressed */
            QPushButton#remove_table_button {{
                background-color: {colors['red']}; /* Red background */
                color: {button_text_color}; /* White text */
                border: none;
                border-radius: 4px; /* Match other buttons */
                padding: 5px; /* Increased padding */
                qproperty-iconSize: 20px 20px; /* Slightly larger icon */
                margin: 0; /* Remove any default margin */
                font-weight: bold; /* Make text bold */
            }}
            QPushButton#remove_table_button:hover {{
                background-color: {colors['red_hover']}; /* Darker red hover */
            }}
            QPushButton#remove_table_button:pressed {{
                background-color: {QColor(colors['red']).darker(120).name()}; /* Even darker red when pressed */
            }}

            /* Tabs */
            QTabWidget::pane {{
                border: 1px solid {colors["border"]};
                background-color: {colors["base"]}; /* Pane background */
                border-radius: 8px;
                border-top-left-radius: 0px; /* Align with tabs */
                margin-top: -1px; /* Overlap with tab bar */
                padding: 12px;
            }}
            QTabBar {{
                qproperty-drawBase: 0; /* Remove the default base line under the tabs */
                margin-bottom: -1px; /* Ensure tabs slightly overlap the pane */
                alignment: Qt.AlignLeft; /* Align tabs to the left */
            }}
            QTabBar::tab {{
                background-color: transparent; /* Make inactive tabs transparent */
                color: {QColor(colors["text"]).darker(130).name() if not dark_mode else QColor(colors["text"]).lighter(130).name()}; /* Dim inactive tab text more */
                border: 1px solid transparent; /* Transparent border initially */
                border-bottom: 2px solid {colors["border"]}; /* Slightly thicker underline for inactive tabs */
                padding: 10px 25px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 5px;
                min-width: 140px;
                font-weight: normal;
                font-size: 11pt;
                /* Removed transition property - Qt stylesheets don't support CSS transitions directly */
            }}
            QTabBar::tab:selected {{
                background-color: {colors["base"]}; /* Selected tab matches pane background */
                color: {colors["highlight"]}; /* Highlight color for selected tab text */
                font-weight: bold;
                border: 1px solid {colors["border"]};
                border-bottom: 2px solid {colors["base"]}; /* Make bottom border match background to blend */
                margin-bottom: -1px; /* Pull selected tab down slightly */
                border-top: 3px solid {colors["highlight"]}; /* Thicker highlight top border */
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {QColor(colors["button_hover"]).lighter(105).name() if dark_mode else QColor(colors["button_hover"]).darker(105).name()}; /* Subtle hover background */
                color: {colors["text"]}; /* Full text color on hover */
                border: 1px solid transparent; /* Keep border transparent on hover */
                border-bottom: 2px solid {QColor(colors["border"]).lighter(110).name() if dark_mode else QColor(colors["border"]).darker(110).name()}; /* Slightly change underline on hover */
            }}
            QTabBar::tab:last {{
                margin-right: 0; /* No margin for the last tab */
            }}

            /* Scrollbars */
            QScrollBar:vertical {{
                background-color: {colors["scrollbar_bg"]};
                width: 12px;
                margin: 0px 0px 0px 0px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {colors["scrollbar_handle"]};
                min-height: 30px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {colors["scrollbar_handle_hover"]};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
                background: none;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
             QScrollBar:horizontal {{
                background-color: {colors["scrollbar_bg"]};
                height: 12px;
                margin: 0px 0px 0px 0px;
                border-radius: 6px;
            }}
            QScrollBar::handle:horizontal {{
                background-color: {colors["scrollbar_handle"]};
                min-width: 30px;
                border-radius: 6px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: {colors["scrollbar_handle_hover"]};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
                background: none;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: none;
            }}

            /* Slider */
            QSlider::groove:horizontal {{
                height: 8px;
                background: {colors["slider_groove"]};
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {colors["slider_handle"]};
                border: 1px solid {colors["slider_handle_border"]};
                width: 18px;
                height: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {QColor(colors["slider_handle"]).lighter(115).name()};
                border: 1px solid {QColor(colors["slider_handle_border"]).lighter(115).name()};
            }}

            /* Tables */
            QTableWidget {{
                gridline-color: transparent; /* Hide grid lines */
                background-color: {colors["base"]};
                alternate-background-color: {colors["alternate_base"]};
                border: 1px solid {colors["border"]};
                border-radius: 8px;
                padding: 0px; /* Remove padding around the table itself */
                selection-background-color: {colors["highlight"]}; /* Explicit selection color */
                selection-color: {colors["highlighted_text"]};
            }}
            QHeaderView::section {{ /* Style for both horizontal and vertical headers */
                background-color: {colors["table_header"]};
                color: {colors["text"]};
                padding: 10px 8px; /* Increased padding */
                border: none; /* Remove default borders */
                font-weight: bold;
                font-size: 10pt;
            }}
            QHeaderView::section:horizontal {{
                border-bottom: 2px solid {colors["highlight"]}; /* Highlight bottom border */
                border-right: 1px solid {colors["border"]}; /* Separator line */
            }}
            QHeaderView::section:horizontal:last {{
                border-right: none; /* No right border for the last header */
            }}
            QTableWidget::item {{ /* Style for individual cells */
                padding: 10px 8px; /* Increased cell padding */
                border: none; /* Remove default cell borders */
                /* Use alternating row colors defined in palette */
            }}
            /* Add subtle bottom border to rows, except the last one */
            QTableWidget QAbstractItemView::item {{
                 border-bottom: 1px solid {colors["border"]};
            }}
            /* Remove bottom border for items in the last visible row */
            /* Note: This is tricky with stylesheets, might not be perfect */

            QTableWidget::item:selected {{
                /* Selection colors handled by QTableWidget setting */
            }}
            /* Status Item Styling - More distinct backgrounds */
            QTableWidget QTableWidgetItem[userRole="Running"] {{
                background-color: {QColor(colors['green']).lighter(150).name() if dark_mode else QColor(colors['green']).lighter(180).name()};
                color: {'#000000' if dark_mode else '#000000'}; /* Ensure contrast */
                font-weight: bold;
            }}
            QTableWidget QTableWidgetItem[userRole="Completed"] {{
                background-color: {QColor(colors['border']).lighter(105).name() if dark_mode else QColor(colors['border']).lighter(140).name()};
                color: {QColor(colors['text']).darker(130).name() if dark_mode else QColor(colors['text']).darker(160).name()};
                font-style: italic;
            }}
            QTableWidget QTableWidgetItem[userRole="Waiting"] {{
                background-color: {QColor(colors['amber']).lighter(150).name() if dark_mode else QColor(colors['amber']).lighter(180).name()};
                color: {'#000000' if dark_mode else '#000000'}; /* Ensure contrast */
            }}
            QTableWidget QTableWidgetItem[userRole="Not Arrived"] {{
                background-color: transparent;
                color: {QColor(colors['text']).darker(140).name() if dark_mode else QColor(colors['text']).darker(170).name()};
                font-style: italic;
            }}
            /* Summary Row Styling - Clearer separation */
            QTableWidget QTableWidgetItem[userRole="summary_label"] {{
                background-color: {QColor(colors["table_header"]).lighter(110).name() if dark_mode else QColor(colors["table_header"]).darker(105).name()};
                color: {colors["text"]};
                padding-right: 15px;
                border-top: 1px solid {colors["highlight"]}; /* Separator line above */
                border-bottom: none;
            }}
             QTableWidget QTableWidgetItem[userRole="summary_value"] {{
                background-color: {QColor(colors["table_header"]).lighter(110).name() if dark_mode else QColor(colors["table_header"]).darker(105).name()};
                color: {colors["highlight"]};
                border-top: 1px solid {colors["highlight"]}; /* Separator line above */
                border-bottom: none;
            }}

            /* Progress Bar in Table - More refined look */
            QTableView QProgressBar {{
                border: 1px solid {colors["border"]};
                border-radius: 6px; /* Slightly less rounded */
                background-color: {colors["base"]};
                text-align: center;
                color: {colors["text"]};
                font-size: 9pt;
                height: 18px; /* Consistent height */
                margin: 2px 0; /* Add slight vertical margin */
            }}
            QTableView QProgressBar::chunk {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {QColor(colors['highlight']).lighter(115).name()}, stop:1 {colors['highlight']});
                border-radius: 6px;
                margin: 1px; /* Add margin to chunk for inset effect */
            }}

            /* Remove Button in Table - More visible hover/pressed */
            QPushButton#remove_table_button {{
                background-color: {colors['red']}; /* Red background */
                color: {button_text_color}; /* White text */
                border: none;
                border-radius: 4px; /* Match other buttons */
                padding: 5px; /* Increased padding */
                qproperty-iconSize: 20px 20px; /* Slightly larger icon */
                margin: 0; /* Remove any default margin */
                font-weight: bold; /* Make text bold */
            }}
            QPushButton#remove_table_button:hover {{
                background-color: {colors['red_hover']}; /* Darker red hover */
            }}
            QPushButton#remove_table_button:pressed {{
                background-color: {QColor(colors['red']).darker(120).name()}; /* Even darker red when pressed */
            }}

            /* Tabs */
            QTabWidget::pane {{
                border: 1px solid {colors["border"]};
                background-color: {colors["base"]}; /* Pane background */
                border-radius: 8px;
                border-top-left-radius: 0px; /* Align with tabs */
                margin-top: -1px; /* Overlap with tab bar */
                padding: 12px;
            }}
            QTabBar {{
                qproperty-drawBase: 0; /* Remove the default base line under the tabs */
                margin-bottom: -1px; /* Ensure tabs slightly overlap the pane */
                alignment: Qt.AlignLeft; /* Align tabs to the left */
            }}
            QTabBar::tab {{
                background-color: transparent; /* Make inactive tabs transparent */
                color: {QColor(colors["text"]).darker(130).name() if not dark_mode else QColor(colors["text"]).lighter(130).name()}; /* Dim inactive tab text more */
                border: 1px solid transparent; /* Transparent border initially */
                border-bottom: 2px solid {colors["border"]}; /* Slightly thicker underline for inactive tabs */
                padding: 10px 25px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 5px;
                min-width: 140px;
                font-weight: normal;
                font-size: 11pt;
                /* Removed transition property - Qt stylesheets don't support CSS transitions directly */
            }}
            QTabBar::tab:selected {{
                background-color: {colors["base"]}; /* Selected tab matches pane background */
                color: {colors["highlight"]}; /* Highlight color for selected tab text */
                font-weight: bold;
                border: 1px solid {colors["border"]};
                border-bottom: 2px solid {colors["base"]}; /* Make bottom border match background to blend */
                margin-bottom: -1px; /* Pull selected tab down slightly */
                border-top: 3px solid {colors["highlight"]}; /* Thicker highlight top border */
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {QColor(colors["button_hover"]).lighter(105).name() if dark_mode else QColor(colors["button_hover"]).darker(105).name()}; /* Subtle hover background */
                color: {colors["text"]}; /* Full text color on hover */
                border: 1px solid transparent; /* Keep border transparent on hover */
                border-bottom: 2px solid {QColor(colors["border"]).lighter(110).name() if dark_mode else QColor(colors["border"]).darker(110).name()}; /* Slightly change underline on hover */
            }}
            QTabBar::tab:last {{
                margin-right: 0; /* No margin for the last tab */
            }}

            /* Scrollbars */
            QScrollBar:vertical {{
                background-color: {colors["scrollbar_bg"]};
                width: 12px;
                margin: 0px 0px 0px 0px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {colors["scrollbar_handle"]};
                min-height: 30px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {colors["scrollbar_handle_hover"]};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
                background: none;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
             QScrollBar:horizontal {{
                background-color: {colors["scrollbar_bg"]};
                height: 12px;
                margin: 0px 0px 0px 0px;
                border-radius: 6px;
            }}
            QScrollBar::handle:horizontal {{
                background-color: {colors["scrollbar_handle"]};
                min-width: 30px;
                border-radius: 6px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: {colors["scrollbar_handle_hover"]};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
                background: none;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: none;
            }}

            /* Slider */
            QSlider::groove:horizontal {{
                height: 8px;
                background: {colors["slider_groove"]};
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {colors["slider_handle"]};
                border: 1px solid {colors["slider_handle_border"]};
                width: 18px;
                height: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {QColor(colors["slider_handle"]).lighter(115).name()};
                border: 1px solid {QColor(colors["slider_handle_border"]).lighter(115).name()};
            }}

            /* Tables */
            QTableWidget {{
                gridline-color: transparent; /* Hide grid lines */
                background-color: {colors["base"]};
                alternate-background-color: {colors["alternate_base"]};
                border: 1px solid {colors["border"]};
                border-radius: 8px;
                padding: 0px; /* Remove padding around the table itself */
                selection-background-color: {colors["highlight"]}; /* Explicit selection color */
                selection-color: {colors["highlighted_text"]};
            }}
            QHeaderView::section {{ /* Style for both horizontal and vertical headers */
                background-color: {colors["table_header"]};
                color: {colors["text"]};
                padding: 10px 8px; /* Increased padding */
                border: none; /* Remove default borders */
                font-weight: bold;
                font-size: 10pt;
            }}
            QHeaderView::section:horizontal {{
                border-bottom: 2px solid {colors["highlight"]}; /* Highlight bottom border */
                border-right: 1px solid {colors["border"]}; /* Separator line */
            }}
            QHeaderView::section:horizontal:last {{
                border-right: none; /* No right border for the last header */
            }}
            QTableWidget::item {{ /* Style for individual cells */
                padding: 10px 8px; /* Increased cell padding */
                border: none; /* Remove default cell borders */
                /* Use alternating row colors defined in palette */
            }}
            /* Add subtle bottom border to rows, except the last one */
            QTableWidget QAbstractItemView::item {{
                 border-bottom: 1px solid {colors["border"]};
            }}
            /* Remove bottom border for items in the last visible row */
            /* Note: This is tricky with stylesheets, might not be perfect */

            QTableWidget::item:selected {{
                /* Selection colors handled by QTableWidget setting */
            }}
            /* Status Item Styling - More distinct backgrounds */
            QTableWidget QTableWidgetItem[userRole="Running"] {{
                background-color: {QColor(colors['green']).lighter(150).name() if dark_mode else QColor(colors['green']).lighter(180).name()};
                color: {'#000000' if dark_mode else '#000000'}; /* Ensure contrast */
                font-weight: bold;
            }}
            QTableWidget QTableWidgetItem[userRole="Completed"] {{
                background-color: {QColor(colors['border']).lighter(105).name() if dark_mode else QColor(colors['border']).lighter(140).name()};
                color: {QColor(colors['text']).darker(130).name() if dark_mode else QColor(colors['text']).darker(160).name()};
                font-style: italic;
            }}
            QTableWidget QTableWidgetItem[userRole="Waiting"] {{
                background-color: {QColor(colors['amber']).lighter(150).name() if dark_mode else QColor(colors['amber']).lighter(180).name()};
                color: {'#000000' if dark_mode else '#000000'}; /* Ensure contrast */
            }}
            QTableWidget QTableWidgetItem[userRole="Not Arrived"] {{
                background-color: transparent;
                color: {QColor(colors['text']).darker(140).name() if dark_mode else QColor(colors['text']).darker(170).name()};
                font-style: italic;
            }}
            /* Summary Row Styling - Clearer separation */
            QTableWidget QTableWidgetItem[userRole="summary_label"] {{
                background-color: {QColor(colors["table_header"]).lighter(110).name() if dark_mode else QColor(colors["table_header"]).darker(105).name()};
                color: {colors["text"]};
                padding-right: 15px;
                border-top: 1px solid {colors["highlight"]}; /* Separator line above */
                border-bottom: none;
            }}
             QTableWidget QTableWidgetItem[userRole="summary_value"] {{
                background-color: {QColor(colors["table_header"]).lighter(110).name() if dark_mode else QColor(colors["table_header"]).darker(105).name()};
                color: {colors["highlight"]};
                border-top: 1px solid {colors["highlight"]}; /* Separator line above */
                border-bottom: none;
            }}

            /* Progress Bar in Table - More refined look */
            QTableView QProgressBar {{
                border: 1px solid {colors["border"]};
                border-radius: 6px; /* Slightly less rounded */
                background-color: {colors["base"]};
                text-align: center;
                color: {colors["text"]};
                font-size: 9pt;
                height: 18px; /* Consistent height */
                margin: 2px 0; /* Add slight vertical margin */
            }}
            QTableView QProgressBar::chunk {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {QColor(colors['highlight']).lighter(115).name()}, stop:1 {colors['highlight']});
                border-radius: 6px;
                margin: 1px; /* Add margin to chunk for inset effect */
            }}

            /* Remove Button in Table - More visible hover/pressed */
            QPushButton#remove_table_button {{
                background-color: {colors['red']}; /* Red background */
                color: {button_text_color}; /* White text */
                border: none;
                border-radius: 4px; /* Match other buttons */
                padding: 5px; /* Increased padding */
                qproperty-iconSize: 20px 20px; /* Slightly larger icon */
                margin: 0; /* Remove any default margin */
                font-weight: bold; /* Make text bold */
            }}
            QPushButton#remove_table_button:hover {{
                background-color: {colors['red_hover']}; /* Darker red hover */
            }}
            QPushButton#remove_table_button:pressed {{
                background-color: {QColor(colors['red']).darker(120).name()}; /* Even darker red when pressed */
            }}

            /* Tabs */
            QTabWidget::pane {{
                border: 1px solid {colors["border"]};
                background-color: {colors["base"]}; /* Pane background */
                border-radius: 8px;
                border-top-left-radius: 0px; /* Align with tabs */
                margin-top: -1px; /* Overlap with tab bar */
                padding: 12px;
            }}
            QTabBar {{
                qproperty-drawBase: 0; /* Remove the default base line under the tabs */
                margin-bottom: -1px; /* Ensure tabs slightly overlap the pane */
                alignment: Qt.AlignLeft; /* Align tabs to the left */
            }}
            QTabBar::tab {{
                background-color: transparent; /* Make inactive tabs transparent */
                color: {QColor(colors["text"]).darker(130).name() if not dark_mode else QColor(colors["text"]).lighter(130).name()}; /* Dim inactive tab text more */
                border: 1px solid transparent; /* Transparent border initially */
                border-bottom: 2px solid {colors["border"]}; /* Slightly thicker underline for inactive tabs */
                padding: 10px 25px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 5px;
                min-width: 140px;
                font-weight: normal;
                font-size: 11pt;
                /* Removed transition property - Qt stylesheets don't support CSS transitions directly */
            }}
            QTabBar::tab:selected {{
                background-color: {colors["base"]}; /* Selected tab matches pane background */
                color: {colors["highlight"]}; /* Highlight color for selected tab text */
                font-weight: bold;
                border: 1px solid {colors["border"]};
                border-bottom: 2px solid {colors["base"]}; /* Make bottom border match background to blend */
                margin-bottom: -1px; /* Pull selected tab down slightly */
                border-top: 3px solid {colors["highlight"]}; /* Thicker highlight top border */
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {QColor(colors["button_hover"]).lighter(105).name() if dark_mode else QColor(colors["button_hover"]).darker(105).name()}; /* Subtle hover background */
                color: {colors["text"]}; /* Full text color on hover */
                border: 1px solid transparent; /* Keep border transparent on hover */
                border-bottom: 2px solid {QColor(colors["border"]).lighter(110).name() if dark_mode else QColor(colors["border"]).darker(110).name()}; /* Slightly change underline on hover */
            }}
            QTabBar::tab:last {{
                margin-right: 0; /* No margin for the last tab */
            }}

            /* Scrollbars */
            QScrollBar:vertical {{
                background-color: {colors["scrollbar_bg"]};
                width: 12px;
                margin: 0px 0px 0px 0px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {colors["scrollbar_handle"]};
                min-height: 30px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {colors["scrollbar_handle_hover"]};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
                background: none;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
             QScrollBar:horizontal {{
                background-color: {colors["scrollbar_bg"]};
                height: 12px;
                margin: 0px 0px 0px 0px;
                border-radius: 6px;
            }}
            QScrollBar::handle:horizontal {{
                background-color: {colors["scrollbar_handle"]};
                min-width: 30px;
                border-radius: 6px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: {colors["scrollbar_handle_hover"]};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
                background: none;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: none;
            }}

            /* Slider */
            QSlider::groove:horizontal {{
                height: 8px;
                background: {colors["slider_groove"]};
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {colors["slider_handle"]};
                border: 1px solid {colors["slider_handle_border"]};
                width: 18px;
                height: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {QColor(colors["slider_handle"]).lighter(115).name()};
                border: 1px solid {QColor(colors["slider_handle_border"]).lighter(115).name()};
            }}

            /* Tables */
            QTableWidget {{
                gridline-color: transparent; /* Hide grid lines */
                background-color: {colors["base"]};
                alternate-background-color: {colors["alternate_base"]};
                border: 1px solid {colors["border"]};
                border-radius: 8px;
                padding: 0px; /* Remove padding around the table itself */
                selection-background-color: {colors["highlight"]}; /* Explicit selection color */
                selection-color: {colors["highlighted_text"]};
            }}
            QHeaderView::section {{ /* Style for both horizontal and vertical headers */
                background-color: {colors["table_header"]};
                color: {colors["text"]};
                padding: 10px 8px; /* Increased padding */
                border: none; /* Remove default borders */
                font-weight: bold;
                font-size: 10pt;
            }}
            QHeaderView::section:horizontal {{
                border-bottom: 2px solid {colors["highlight"]}; /* Highlight bottom border */
                border-right: 1px solid {colors["border"]}; /* Separator line */
            }}
            QHeaderView::section:horizontal:last {{
                border-right: none; /* No right border for the last header */
            }}
            QTableWidget::item {{ /* Style for individual cells */
                padding: 10px 8px; /* Increased cell padding */
                border: none; /* Remove default cell borders */
                /* Use alternating row colors defined in palette */
            }}
            /* Add subtle bottom border to rows, except the last one */
            QTableWidget QAbstractItemView::item {{
                 border-bottom: 1px solid {colors["border"]};
            }}
            /* Remove bottom border for items in the last visible row */
            /* Note: This is tricky with stylesheets, might not be perfect */

            QTableWidget::item:selected {{
                /* Selection colors handled by QTableWidget setting */
            }}
            /* Status Item Styling - More distinct backgrounds */
            QTableWidget QTableWidgetItem[userRole="Running"] {{
                background-color: {QColor(colors['green']).lighter(150).name() if dark_mode else QColor(colors['green']).lighter(180).name()};
                color: {'#000000' if dark_mode else '#000000'}; /* Ensure contrast */
                font-weight: bold;
            }}
            QTableWidget QTableWidgetItem[userRole="Completed"] {{
                background-color: {QColor(colors['border']).lighter(105).name() if dark_mode else QColor(colors['border']).lighter(140).name()};
                color: {QColor(colors['text']).darker(130).name() if dark_mode else QColor(colors['text']).darker(160).name()};
                font-style: italic;
            }}
            QTableWidget QTableWidgetItem[userRole="Waiting"] {{
                background-color: {QColor(colors['amber']).lighter(150).name() if dark_mode else QColor(colors['amber']).lighter(180).name()};
                color: {'#000000' if dark_mode else '#000000'}; /* Ensure contrast */
            }}
            QTableWidget QTableWidgetItem[userRole="Not Arrived"] {{
                background-color: transparent;
                color: {QColor(colors['text']).darker(140).name() if dark_mode else QColor(colors['text']).darker(170).name()};
                font-style: italic;
            }}
            /* Summary Row Styling - Clearer separation */
            QTableWidget QTableWidgetItem[userRole="summary_label"] {{
                background-color: {QColor(colors["table_header"]).lighter(110).name() if dark_mode else QColor(colors["table_header"]).darker(105).name()};
                color: {colors["text"]};
                padding-right: 15px;
                border-top: 1px solid {colors["highlight"]}; /* Separator line above */
                border-bottom: none;
            }}
             QTableWidget QTableWidgetItem[userRole="summary_value"] {{
                background-color: {QColor(colors["table_header"]).lighter(110).name() if dark_mode else QColor(colors["table_header"]).darker(105).name()};
                color: {colors["highlight"]};
                border-top: 1px solid {colors["highlight"]}; /* Separator line above */
                border-bottom: none;
            }}

            /* Progress Bar in Table - More refined look */
            QTableView QProgressBar {{
                border: 1px solid {colors["border"]};
                border-radius: 6px; /* Slightly less rounded */
                background-color: {colors["base"]};
                text-align: center;
                color: {colors["text"]};
                font-size: 9pt;
                height: 18px; /* Consistent height */
                margin: 2px 0; /* Add slight vertical margin */
            }}
            QTableView QProgressBar::chunk {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {QColor(colors['highlight']).lighter(115).name()}, stop:1 {colors['highlight']});
                border-radius: 6px;
                margin: 1px; /* Add margin to chunk for inset effect */
            }}

            /* Remove Button in Table - More visible hover/pressed */
            QPushButton#remove_table_button {{
                background-color: {colors['red']}; /* Red background */
                color: {button_text_color}; /* White text */
                border: none;
                border-radius: 4px; /* Match other buttons */
                padding: 5px; /* Increased padding */
                qproperty-iconSize: 20px 20px; /* Slightly larger icon */
                margin: 0; /* Remove any default margin */
                font-weight: bold; /* Make text bold */
            }}
            QPushButton#remove_table_button:hover {{
                background-color: {colors['red_hover']}; /* Darker red hover */
            }}
            QPushButton#remove_table_button:pressed {{
                background-color: {QColor(colors['red']).darker(120).name()}; /* Even darker red when pressed */
            }}

            /* Tabs */
            QTabWidget::pane {{
                border: 1px solid {colors["border"]};
                background-color: {colors["base"]}; /* Pane background */
                border-radius: 8px;
                border-top-left-radius: 0px; /* Align with tabs */
                margin-top: -1px; /* Overlap with tab bar */
                padding: 12px;
            }}
            QTabBar {{
                qproperty-drawBase: 0; /* Remove the default base line under the tabs */
                margin-bottom: -1px; /* Ensure tabs slightly overlap the pane */
                alignment: Qt.AlignLeft; /* Align tabs to the left */
            }}
            QTabBar::tab {{
                background-color: transparent; /* Make inactive tabs transparent */
                color: {QColor(colors["text"]).darker(130).name() if not dark_mode else QColor(colors["text"]).lighter(130).name()}; /* Dim inactive tab text more */
                border: 1px solid transparent; /* Transparent border initially */
                border-bottom: 2px solid {colors["border"]}; /* Slightly thicker underline for inactive tabs */
                padding: 10px 25px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 5px;
                min-width: 140px;
                font-weight: normal;
                font-size: 11pt;
                /* Removed transition property - Qt stylesheets don't support CSS transitions directly */
            }}
            QTabBar::tab:selected {{
                background-color: {colors["base"]}; /* Selected tab matches pane background */
                color: {colors["highlight"]}; /* Highlight color for selected tab text */
                font-weight: bold;
                border: 1px solid {colors["border"]};
                border-bottom: 2px solid {colors["base"]}; /* Make bottom border match background to blend */
                margin-bottom: -1px; /* Pull selected tab down slightly */
                border-top: 3px solid {colors["highlight"]}; /* Thicker highlight top border */
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {QColor(colors["button_hover"]).lighter(105).name() if dark_mode else QColor(colors["button_hover"]).darker(105).name()}; /* Subtle hover background */
                color: {colors["text"]}; /* Full text color on hover */
                border: 1px solid transparent; /* Keep border transparent on hover */
                border-bottom: 2px solid {QColor(colors["border"]).lighter(110).name() if dark_mode else QColor(colors["border"]).darker(110).name()}; /* Slightly change underline on hover */
            }}
            QTabBar::tab:last {{
                margin-right: 0; /* No margin for the last tab */
            }}
        """)

        # Update toolbar theme button text and icon
        self.theme_button.setIcon(self.sun_icon if self.dark_mode else self.moon_icon)
        self.theme_button.setText("Light Mode" if self.dark_mode else "Dark Mode")
        self.theme_button.setChecked(not self.dark_mode) # Ensure checked state matches theme

        # Update menu action text
        self.dark_mode_action.setText("&Light Mode" if self.dark_mode else "&Dark Mode")
        self.dark_mode_action.setChecked(not self.dark_mode) # Ensure checked state matches theme

        # Update Gantt chart and Process table dark mode
        self.gantt_chart.set_dark_mode(dark_mode)
        self.process_table.set_dark_mode(dark_mode)

        # Force style refresh on specific widgets if needed (sometimes helps)
        self.process_table.style().unpolish(self.process_table)
        self.process_table.style().polish(self.process_table)
        self.gantt_chart.style().unpolish(self.gantt_chart)
        self.gantt_chart.style().polish(self.gantt_chart)
        # Force refresh on controls too
        self.scheduler_control.style().unpolish(self.scheduler_control)
        self.scheduler_control.style().polish(self.scheduler_control)
        self.process_control.style().unpolish(self.process_control)
        self.process_control.style().polish(self.process_control)
    
    def toggle_theme(self, state):
        """Toggle between light and dark theme."""
        # The 'state' argument from the button/action reflects the *new* checked state.
        # If checked (state=True), it means the user clicked to activate "Light Mode" (from dark) or "Dark Mode" (from light).
        # So, if state is True, we want the *opposite* of the current dark_mode.
        # If state is False, we want the *current* dark_mode.
        # A simpler way: the new dark_mode is the opposite of the checked state.
        self.dark_mode = not state

        # Apply styles for the new theme
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
        # Stop any running simulation thread first
        if self.simulation:
            # Make sure the simulation is stopped
            self.simulation.stop()
            
            # Wait for thread to finish if it's running
            if hasattr(self, 'simulation_thread') and self.simulation_thread and self.simulation_thread.isRunning():
                self.simulation_thread.wait()
            
            # Now reset the simulation
            self.simulation.reset()
            
        # Reset process control
        self.process_control.reset_count()
        
        # Reset the Gantt chart
        self.gantt_chart.reset()
        
        # Reset UI state
        self.scheduler_control.start_button.setEnabled(True)
        self.scheduler_control.pause_resume_button.setEnabled(False)
        # Reset pause/resume button text and icon to initial state
        self.scheduler_control.pause_resume_button.setText("Pause")
        self.scheduler_control.pause_resume_button.setIcon(QIcon.fromTheme("media-playback-pause"))
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
        self.scheduler_control.pause_resume_button.setEnabled(True)
        self.scheduler_control.run_all_button.setEnabled(False)
        
        # Show status message
        self.statusBar().showMessage("Simulation started")
        
    def on_pause(self):
        """Pause the simulation."""
        if self.simulation:
            self.simulation.pause()
            
        # Update UI state
        self.scheduler_control.pause_resume_button.setText("Resume")
        self.scheduler_control.pause_resume_button.setIcon(QIcon.fromTheme("media-playback-start"))
        
        # Show status message
        self.statusBar().showMessage("Simulation paused")
        
    def on_resume(self):
        """Resume the simulation."""
        if self.simulation:
            self.simulation.resume()
            
        # Update UI state
        self.scheduler_control.pause_resume_button.setText("Pause")
        self.scheduler_control.pause_resume_button.setIcon(QIcon.fromTheme("media-playback-pause"))
        
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
        self.scheduler_control.pause_resume_button.setEnabled(False)
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
        self.stats_widget.update_stats(avg_waiting, avg_turnaround, self.simulation)
        
    def on_import_processes(self):
        """Import processes from a CSV file."""
        # Open file dialog to select CSV file
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Import Processes", 
            "", 
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return
            
        try:
            # Read CSV file
            import csv
            with open(file_path, 'r') as file:
                reader = csv.reader(file)
                header = next(reader)  # Skip header row
                
                # Check if header is correct
                expected_header = ["Process Name", "Arrival Time", "Burst Time", "Priority"]
                if not all(h in header for h in expected_header[:3]):  # Priority might be optional
                    QMessageBox.warning(
                        self, 
                        "Invalid CSV Format", 
                        "CSV file must have columns: Process Name, Arrival Time, Burst Time, and optionally Priority."
                    )
                    return
                    
                # Remove all existing processes
                self.on_remove_all()
                
                # Reset process counter
                self.process_control.process_count = 0
                
                # Add processes from CSV
                for row in reader:
                    if len(row) >= 3:  # Need at least 3 columns (name, arrival, burst)
                        name = row[0]
                        arrival_time = int(row[1])
                        burst_time = int(row[2])
                        priority = int(row[3]) if len(row) > 3 else 0
                        
                        # Create and add process
                        process = Process(
                            pid=self.process_control.process_count,
                            name=name,
                            arrival_time=arrival_time,
                            burst_time=burst_time,
                            priority=priority
                        )
                        
                        self.simulation.add_process(process)
                        self.process_control.next_process_name()
                        
                # Show success message
                self.statusBar().showMessage(f"Imported {len(self.simulation.scheduler.processes)} processes from {file_path}", 5000)
                
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Import Error", 
                f"Failed to import processes: {str(e)}"
            )
            
    def on_export_results(self):
        """Export simulation results to a CSV file."""
        # Check if there are results to export
        if not self.simulation or not self.simulation.has_results():
            QMessageBox.warning(
                self,
                "Nothing to Export",
                "There are no simulation results to export. Please run the simulation first."
            )
            return
            
        # Open file dialog to save CSV file
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Results",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return
            
        try:
            # Add .csv extension if not already present
            if not file_path.lower().endswith('.csv'):
                file_path += '.csv'
                
            # Get all processes (both running and completed)
            all_processes = self.simulation.scheduler.processes + self.simulation.scheduler.completed_processes
            
            # Remove duplicates (a process might be in both lists)
            process_dict = {process.pid: process for process in all_processes}
            processes = list(process_dict.values())
            
            # Sort by process ID
            processes.sort(key=lambda p: p.pid)
            
            # Get scheduler type
            scheduler_name = self.scheduler_control.scheduler_combo.currentText()
            
            # Get time quantum for Round Robin
            time_quantum = None
            if isinstance(self.current_scheduler, RoundRobinScheduler):
                self.scheduler_control.time_quantum_spinbox.value()
            
            # Write CSV file
            import csv
            import time  # Added for timestamp in export
            with open(file_path, 'w', newline='') as file:
                writer = csv.writer(file)
                
                # Write header with scheduler info
                writer.writerow(["CPU Scheduler Simulation Results"])
                writer.writerow([f"Scheduler: {scheduler_name}"])
                if time_quantum is not None:
                    writer.writerow([f"Time Quantum: {time_quantum}"])
                writer.writerow([])
                
                # Write process data header
                writer.writerow([
                    "Process ID", 
                    "Process Name", 
                    "Arrival Time", 
                    "Burst Time", 
                    "Priority",
                    "Start Time", 
                    "Completion Time",  # Changed from "Finish Time" to "Completion Time" 
                    "Turnaround Time", 
                    "Waiting Time", 
                    "Response Time"
                ])
                
                # Write process data
                for process in processes:
                    # Calculate response time (time from arrival to first CPU burst)
                    response_time = "-"
                    if process.start_time is not None:
                        response_time = process.start_time - process.arrival_time
                    
                    # Handle cases where process hasn't completed yet
                    completion_time = process.completion_time if process.completion_time is not None else "-"
                    turnaround_time = process.turnaround_time if process.completion_time is not None else "-"
                    waiting_time = process.waiting_time if process.completion_time is not None else "-"
                    
                    writer.writerow([
                        process.pid,
                        process.name,
                        process.arrival_time,
                        process.burst_time,
                        process.priority,
                        process.start_time if process.start_time is not None else "-",
                        completion_time,  # Using completion_time consistently
                        turnaround_time,
                        waiting_time,
                        response_time
                    ])
                
                # Write average metrics
                writer.writerow([])
                avg_waiting, avg_turnaround = self.simulation.scheduler.calculate_metrics()
                writer.writerow(["Average Waiting Time:", f"{avg_waiting:.2f}"])
                writer.writerow(["Average Turnaround Time:", f"{avg_turnaround:.2f}"])
                
                # Calculate and write average response time and throughput
                completed_processes = [p for p in processes if p.completion_time is not None]
                if completed_processes:
                    # Calculate average response time
                    response_times = [(p.start_time - p.arrival_time) for p in completed_processes 
                                     if p.start_time is not None]
                    if response_times:
                        avg_response = sum(response_times) / len(response_times)
                        writer.writerow(["Average Response Time:", f"{avg_response:.2f}"])
                    
                    # Calculate throughput
                    max_completion_time = max(p.completion_time for p in completed_processes)
                    if max_completion_time > 0:
                        throughput = len(completed_processes) / max_completion_time
                        writer.writerow(["Throughput:", f"{throughput:.4f} processes/time unit"])
                
                # Add system settings
                writer.writerow([])
                writer.writerow(["Simulation Settings:"])
                writer.writerow(["Simulation Speed:", f"{self.scheduler_control.speed_slider.value()}x"])
                writer.writerow(["Export Date:", time.strftime("%Y-%m-%d %H:%M:%S")])
            
            # Show success message
            self.statusBar().showMessage(f"Results exported to {file_path}", 5000)
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export results: {str(e)}"
            )
            
    def on_about(self):
        """Show the about dialog."""
        QMessageBox.about(
            self,
            "About CPU Scheduler Simulation",
            """
            <h1>CPU Scheduler Simulation</h1>
            <p style="font-size: 14pt;">An interactive tool for learning and visualizing CPU scheduling algorithms.</p>
            <p>Algorithms implemented:</p>
            <ul>
                <li>First-Come, First-Served (FCFS)</li>
                <li>Shortest Job First (Non-Preemptive)</li>
                <li>Shortest Job First (Preemptive)</li>
                <li>Priority (Non-Preemptive)</li>
                <li>Priority (Preemptive)</li>
                <li>Round Robin</li>
            </ul>
            <p>Created as part of ASU Senior Project for Operating Systems course.</p>
            <p>© 2025 ASU Operation Systems Team</p>
            """
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
        
    def on_pause_resume(self):
        """Toggle between pause and resume states."""
        if not self.simulation:
            return
            
        # If simulation is paused, resume it
        if self.simulation.paused:
            self.on_resume()
        # Otherwise, pause it
        else:
            self.on_pause()