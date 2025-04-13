import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                          QHBoxLayout, QGroupBox, QLabel, QComboBox, QSpinBox, 
                          QPushButton, QScrollArea, QFormLayout, QLineEdit, 
                          QMessageBox, QCheckBox, QTabWidget, QGridLayout,
                          QStyleFactory, QSlider, QToolButton)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QFont, QColor, QPalette
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
        
class MainWindow(QMainWindow):
    """Main window of the CPU Scheduler application."""
    
    def __init__(self):
        super().__init__()
        
        # Initialize state
        self.simulation = None
        self.simulation_thread = None
        self.current_scheduler = None
        self.process_count = 0
        self.dark_mode = False
        
        # Setup UI
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the main window UI."""
        # Set window properties
        self.setWindowTitle("CPU Scheduler Simulation")
        self.setMinimumSize(900, 650)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Top section with controls
        top_layout = QHBoxLayout()
        
        # Left panel with scheduler and process controls
        left_panel = QVBoxLayout()
        left_panel.setSpacing(10)
        
        # Create theme toggle
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Theme:"))
        theme_layout.addStretch()
        
        self.theme_toggle = QCheckBox("Dark Mode")
        self.theme_toggle.setChecked(False)
        self.theme_toggle.stateChanged.connect(self.toggle_theme)
        theme_layout.addWidget(self.theme_toggle)
        
        left_panel.addLayout(theme_layout)
        
        # Create scheduler selection section with modern look
        scheduler_group = QGroupBox("Scheduler Settings")
        scheduler_layout = QFormLayout()
        scheduler_layout.setSpacing(8)
        scheduler_group.setLayout(scheduler_layout)
        
        # Scheduler type combo box
        self.scheduler_combo = QComboBox()
        self.scheduler_combo.addItems([
            "First-Come, First-Served (FCFS)",
            "Shortest Job First (Non-Preemptive)",
            "Shortest Job First (Preemptive)",
            "Priority (Non-Preemptive)",
            "Priority (Preemptive)",
            "Round Robin"
        ])
        self.scheduler_combo.currentIndexChanged.connect(self.on_scheduler_changed)
        scheduler_layout.addRow("Scheduler Type:", self.scheduler_combo)
        
        # Time quantum for Round Robin
        self.time_quantum_spinbox = QSpinBox()
        self.time_quantum_spinbox.setRange(1, 100)
        self.time_quantum_spinbox.setValue(2)
        self.time_quantum_spinbox.setEnabled(False)  # Disabled by default
        scheduler_layout.addRow("Time Quantum:", self.time_quantum_spinbox)
        
        left_panel.addWidget(scheduler_group)
        
        # Create process controls with modern look
        process_control_group = QGroupBox("Process Control")
        process_control_layout = QGridLayout()
        process_control_layout.setSpacing(8)
        process_control_group.setLayout(process_control_layout)
        
        # Process input fields
        self.process_name_input = QLineEdit("Process 1")
        process_control_layout.addWidget(QLabel("Name:"), 0, 0)
        process_control_layout.addWidget(self.process_name_input, 0, 1)
        
        self.arrival_time_spinbox = QSpinBox()
        self.arrival_time_spinbox.setRange(0, 1000)
        process_control_layout.addWidget(QLabel("Arrival Time:"), 1, 0)
        process_control_layout.addWidget(self.arrival_time_spinbox, 1, 1)
        
        self.burst_time_spinbox = QSpinBox()
        self.burst_time_spinbox.setRange(1, 1000)
        self.burst_time_spinbox.setValue(5)  # Default value
        process_control_layout.addWidget(QLabel("Burst Time:"), 2, 0)
        process_control_layout.addWidget(self.burst_time_spinbox, 2, 1)
        
        self.priority_spinbox = QSpinBox()
        self.priority_spinbox.setRange(0, 100)
        process_control_layout.addWidget(QLabel("Priority:"), 3, 0)
        process_control_layout.addWidget(self.priority_spinbox, 3, 1)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        # Add Process button with modern styling
        self.add_process_button = QPushButton("Add Process")
        self.add_process_button.clicked.connect(self.on_add_process)
        self.add_process_button.setMinimumHeight(30)
        buttons_layout.addWidget(self.add_process_button)
        
        # Remove All button with modern styling
        self.remove_all_button = QPushButton("Remove All")
        self.remove_all_button.clicked.connect(self.on_remove_all)
        self.remove_all_button.setMinimumHeight(30)
        buttons_layout.addWidget(self.remove_all_button)
        
        # Reset button with modern styling
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.on_reset)
        self.reset_button.setMinimumHeight(30)
        buttons_layout.addWidget(self.reset_button)
        
        process_control_layout.addLayout(buttons_layout, 4, 0, 1, 2)
        
        left_panel.addWidget(process_control_group)
        
        # Simulation Controls
        sim_control_group = QGroupBox("Simulation Control")
        sim_control_layout = QVBoxLayout()
        sim_control_layout.setSpacing(8)
        sim_control_group.setLayout(sim_control_layout)
        
        # Speed control layout
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Speed:"))
        
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 10)
        self.speed_slider.setValue(1)
        self.speed_slider.setTickPosition(QSlider.TicksBelow)
        self.speed_slider.setTickInterval(1)
        self.speed_slider.valueChanged.connect(self.on_speed_changed)
        speed_layout.addWidget(self.speed_slider)
        
        self.speed_label = QLabel("1x")
        speed_layout.addWidget(self.speed_label)
        
        sim_control_layout.addLayout(speed_layout)
        
        # Buttons layout
        control_buttons_layout = QHBoxLayout()
        
        # Start button
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.on_start)
        self.start_button.setMinimumHeight(30)
        control_buttons_layout.addWidget(self.start_button)
        
        # Pause button
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.on_pause)
        self.pause_button.setEnabled(False)
        self.pause_button.setMinimumHeight(30)
        control_buttons_layout.addWidget(self.pause_button)
        
        # Resume button
        self.resume_button = QPushButton("Resume")
        self.resume_button.clicked.connect(self.on_resume)
        self.resume_button.setEnabled(False)
        self.resume_button.setMinimumHeight(30)
        control_buttons_layout.addWidget(self.resume_button)
        
        # Stop button
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.on_stop)
        self.stop_button.setEnabled(False)
        self.stop_button.setMinimumHeight(30)
        control_buttons_layout.addWidget(self.stop_button)
        
        sim_control_layout.addLayout(control_buttons_layout)
        
        # Run All At Once button
        self.run_all_button = QPushButton("Run All At Once")
        self.run_all_button.clicked.connect(self.on_run_all)
        self.run_all_button.setMinimumHeight(30)
        sim_control_layout.addWidget(self.run_all_button)
        
        left_panel.addWidget(sim_control_group)
        
        # Create statistics section
        stats_group = QGroupBox("Statistics")
        stats_layout = QVBoxLayout()
        stats_layout.setSpacing(8)
        stats_group.setLayout(stats_layout)
        
        # Average waiting time
        waiting_layout = QHBoxLayout()
        waiting_layout.addWidget(QLabel("Average Waiting Time:"))
        waiting_layout.addStretch()
        self.avg_waiting_label = QLabel("0.00")
        self.avg_waiting_label.setStyleSheet("font-weight: bold;")
        waiting_layout.addWidget(self.avg_waiting_label)
        stats_layout.addLayout(waiting_layout)
        
        # Average turnaround time
        turnaround_layout = QHBoxLayout()
        turnaround_layout.addWidget(QLabel("Average Turnaround Time:"))
        turnaround_layout.addStretch()
        self.avg_turnaround_label = QLabel("0.00")
        self.avg_turnaround_label.setStyleSheet("font-weight: bold;")
        turnaround_layout.addWidget(self.avg_turnaround_label)
        stats_layout.addLayout(turnaround_layout)
        
        left_panel.addWidget(stats_group)
        
        # Add stretch to push all widgets to the top
        left_panel.addStretch()
        
        # Right panel with tabs
        right_panel = QVBoxLayout()
        
        # Create tab widget for Process Table and Gantt Chart
        self.tab_widget = QTabWidget()
        
        # Create Process Table tab
        self.process_table = ProcessTable()
        # Set the remove callback for the process table
        self.process_table.set_remove_callback(self.on_remove_process)
        self.tab_widget.addTab(self.process_table, "Process Table")
        
        # Create Gantt Chart tab
        gantt_tab = QWidget()
        gantt_layout = QVBoxLayout(gantt_tab)
        
        self.gantt_chart = GanttChart()
        gantt_scroll_area = QScrollArea()
        gantt_scroll_area.setWidget(self.gantt_chart)
        gantt_scroll_area.setWidgetResizable(True)
        gantt_layout.addWidget(gantt_scroll_area)
        
        self.tab_widget.addTab(gantt_tab, "Gantt Chart")
        
        right_panel.addWidget(self.tab_widget)
        
        # Add left and right panels to top layout with appropriate sizes
        top_layout.addLayout(left_panel, 1)  # 1/3 of the width
        top_layout.addLayout(right_panel, 2)  # 2/3 of the width
        
        main_layout.addLayout(top_layout)
        
        # Apply initial styling
        self.apply_styles(self.dark_mode)
        
        # Initialize the first scheduler
        self.on_scheduler_changed(0)
        
    def apply_styles(self, dark_mode):
        """Apply styling to the application based on the selected theme."""
        if dark_mode:
            # Dark theme
            app = QApplication.instance()
            app.setStyle(QStyleFactory.create("Fusion"))
            
            dark_palette = QPalette()
            dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.WindowText, Qt.white)
            dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
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
                QGroupBox {
                    border: 1px solid #3A3A3A;
                    border-radius: 5px;
                    padding-top: 20px;
                    margin-top: 10px;
                    background-color: #2D2D2D;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    padding: 5px;
                    background-color: #2D2D2D;
                    color: #FFFFFF;
                    font-weight: bold;
                }
                QPushButton {
                    border: 1px solid #3A3A3A;
                    border-radius: 4px;
                    background-color: #3A3A3A;
                    color: #FFFFFF;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #4A4A4A;
                }
                QPushButton:pressed {
                    background-color: #2A2A2A;
                }
                QPushButton:disabled {
                    background-color: #2A2A2A;
                    color: #6A6A6A;
                }
                QComboBox, QSpinBox, QLineEdit {
                    border: 1px solid #3A3A3A;
                    border-radius: 4px;
                    padding: 2px 5px;
                    background-color: #2A2A2A;
                    color: #FFFFFF;
                    selection-background-color: #3A3A3A;
                }
                QTabWidget::pane {
                    border: 1px solid #3A3A3A;
                    background-color: #2D2D2D;
                }
                QTabBar::tab {
                    background-color: #2A2A2A;
                    color: #FFFFFF;
                    border: 1px solid #3A3A3A;
                    padding: 5px 10px;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                }
                QTabBar::tab:selected {
                    background-color: #3A3A3A;
                }
                QTabBar::tab:hover {
                    background-color: #4A4A4A;
                }
                QScrollBar {
                    background-color: #2A2A2A;
                }
                QScrollBar::handle {
                    background-color: #5A5A5A;
                    border-radius: 4px;
                }
                QSlider::groove:horizontal {
                    height: 8px;
                    background: #2A2A2A;
                    border-radius: 4px;
                }
                QSlider::handle:horizontal {
                    background: #5A5A5A;
                    border: 1px solid #5A5A5A;
                    width: 18px;
                    margin: -4px 0;
                    border-radius: 4px;
                }
                QSlider::handle:horizontal:hover {
                    background: #6A6A6A;
                }
            """)
        else:
            # Light theme
            app = QApplication.instance()
            app.setStyle(QStyleFactory.create("Fusion"))
            app.setPalette(app.style().standardPalette())
            
            app.setStyleSheet("""
                QGroupBox {
                    border: 1px solid #CCCCCC;
                    border-radius: 5px;
                    padding-top: 20px;
                    margin-top: 10px;
                    background-color: #F9F9F9;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    padding: 5px;
                    background-color: #F9F9F9;
                    color: #333333;
                    font-weight: bold;
                }
                QPushButton {
                    border: 1px solid #CCCCCC;
                    border-radius: 4px;
                    background-color: #F0F0F0;
                    color: #333333;
                    padding: 5px;
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
                    border-radius: 4px;
                    padding: 2px 5px;
                    background-color: #FFFFFF;
                    selection-background-color: #E0E0E0;
                }
                QTabWidget::pane {
                    border: 1px solid #CCCCCC;
                    background-color: #F9F9F9;
                }
                QTabBar::tab {
                    background-color: #F0F0F0;
                    border: 1px solid #CCCCCC;
                    padding: 5px 10px;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                }
                QTabBar::tab:selected {
                    background-color: #FFFFFF;
                }
                QTabBar::tab:hover {
                    background-color: #E0E0E0;
                }
                QScrollBar {
                    background-color: #F0F0F0;
                }
                QScrollBar::handle {
                    background-color: #CCCCCC;
                    border-radius: 4px;
                }
                QSlider::groove:horizontal {
                    height: 8px;
                    background: #E0E0E0;
                    border-radius: 4px;
                }
                QSlider::handle:horizontal {
                    background: #CCCCCC;
                    border: 1px solid #CCCCCC;
                    width: 18px;
                    margin: -4px 0;
                    border-radius: 4px;
                }
                QSlider::handle:horizontal:hover {
                    background: #BBBBBB;
                }
            """)
            
        # Update Gantt chart and Process table dark mode
        self.gantt_chart.set_dark_mode(dark_mode)
        self.process_table.set_dark_mode(dark_mode)
    
    def toggle_theme(self, state):
        """Toggle between light and dark theme."""
        self.dark_mode = bool(state)
        self.apply_styles(self.dark_mode)
    
    def on_speed_changed(self, value):
        """Handle speed slider change."""
        self.speed_label.setText(f"{value}x")
        if self.simulation:
            self.simulation.delay = 1.0 / value
    
    def on_scheduler_changed(self, index):
        """
        Handle scheduler type change.
        
        Args:
            index (int): Index of the selected scheduler
        """
        # Enable/disable time quantum field based on selected scheduler
        self.time_quantum_spinbox.setEnabled(index == 5)  # Index 5 is Round Robin
        
        # Reset simulation
        self.on_reset()
        
        # Create the new scheduler
        scheduler_name = self.scheduler_combo.currentText()
        
        if index == 0:  # FCFS
            self.current_scheduler = FCFSScheduler()
            self.priority_spinbox.setEnabled(False)
        elif index == 1:  # SJF (Non-Preemptive)
            self.current_scheduler = SJFNonPreemptiveScheduler()
            self.priority_spinbox.setEnabled(False)
        elif index == 2:  # SJF (Preemptive)
            self.current_scheduler = SJFPreemptiveScheduler()
            self.priority_spinbox.setEnabled(False)
        elif index == 3:  # Priority (Non-Preemptive)
            self.current_scheduler = PriorityNonPreemptiveScheduler()
            self.priority_spinbox.setEnabled(True)
        elif index == 4:  # Priority (Preemptive)
            self.current_scheduler = PriorityPreemptiveScheduler()
            self.priority_spinbox.setEnabled(True)
        elif index == 5:  # Round Robin
            time_quantum = self.time_quantum_spinbox.value()
            self.current_scheduler = RoundRobinScheduler(time_quantum=time_quantum)
            self.priority_spinbox.setEnabled(False)
            
        # Create simulation
        self.simulation = Simulation(self.current_scheduler, delay=1.0/self.speed_slider.value())
        
        # Register callbacks
        self.simulation.set_process_update_callback(self.process_table.update_table)
        self.simulation.set_gantt_update_callback(self.gantt_chart.update_chart)
        self.simulation.set_stats_update_callback(self.update_statistics)
        
    def on_add_process(self):
        """Add a new process to the simulation."""
        # Get process details from input fields
        name = self.process_name_input.text() or f"Process {self.process_count + 1}"
        arrival_time = self.arrival_time_spinbox.value()
        burst_time = self.burst_time_spinbox.value()
        priority = self.priority_spinbox.value()
        
        # Create new process
        process = Process(
            pid=self.process_count,
            name=name,
            arrival_time=arrival_time,
            burst_time=burst_time,
            priority=priority
        )
        
        # Add process to simulation
        self.simulation.add_process(process)
        
        # Increment process counter
        self.process_count += 1
        
        # Update process name to suggest next process
        self.process_name_input.setText(f"Process {self.process_count + 1}")
        
    def on_reset(self):
        """Reset the simulation."""
        if self.simulation:
            self.simulation.reset()
            
        # Reset process counter
        self.process_count = 0
        
        # Reset process name
        self.process_name_input.setText("Process 1")
        
        # Reset the Gantt chart
        self.gantt_chart.reset()
        
        # Reset UI state
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.resume_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.run_all_button.setEnabled(True)
        
    def on_start(self):
        """Start the simulation."""
        if not self.simulation or not self.simulation.scheduler.processes:
            QMessageBox.warning(self, "Warning", "Please add at least one process first.")
            return
            
        # Update simulation speed
        self.simulation.delay = 1.0 / self.speed_slider.value()
        
        # Create and start the simulation thread
        self.simulation_thread = SimulationThread(self.simulation)
        
        # Connect thread signals to UI update slots
        self.simulation_thread.process_updated.connect(self.process_table.update_table)
        self.simulation_thread.gantt_updated.connect(self.gantt_chart.update_chart)
        self.simulation_thread.stats_updated.connect(self.update_statistics)
        
        # Start the thread
        self.simulation_thread.start()
        
        # Update UI state
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.resume_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.run_all_button.setEnabled(False)
        
    def on_pause(self):
        """Pause the simulation."""
        if self.simulation:
            self.simulation.pause()
            
        # Update UI state
        self.pause_button.setEnabled(False)
        self.resume_button.setEnabled(True)
        
    def on_resume(self):
        """Resume the simulation."""
        if self.simulation:
            self.simulation.resume()
            
        # Update UI state
        self.pause_button.setEnabled(True)
        self.resume_button.setEnabled(False)
        
    def on_stop(self):
        """Stop the simulation."""
        if self.simulation:
            self.simulation.stop()
            
        # Update UI state
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.resume_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.run_all_button.setEnabled(True)
        
    def on_run_all(self):
        """Run all processes at once."""
        if not self.simulation or not self.simulation.scheduler.processes:
            QMessageBox.warning(self, "Warning", "Please add at least one process first.")
            return
            
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
        
    def update_statistics(self, avg_waiting: float, avg_turnaround: float):
        """
        Update the statistics display.
        
        Args:
            avg_waiting (float): Average waiting time
            avg_turnaround (float): Average turnaround time
        """
        self.avg_waiting_label.setText(f"{avg_waiting:.2f}")
        self.avg_turnaround_label.setText(f"{avg_turnaround:.2f}")
        
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
            
    def on_remove_all(self):
        """Remove all processes from the simulation."""
        if not self.simulation:
            return
            
        # Remove all processes
        self.simulation.remove_all_processes()
        
        # Reset process counter
        self.process_count = 0
        
        # Reset process name
        self.process_name_input.setText("Process 1")
        
        # Reset the Gantt chart
        self.gantt_chart.reset()
        
        # Update the UI
        if self.process_table:
            self.process_table.update_table([], self.simulation.current_time)