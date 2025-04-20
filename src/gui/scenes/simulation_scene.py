from PyQt5.QtWidgets import (QSplitter, QTabWidget, QWidget, QVBoxLayout, 
                          QHBoxLayout, QScrollArea, QMessageBox, QPushButton, QFrame)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon

from .base_scene import BaseScene
from ..scheduler_control_widget import SchedulerControlWidget
from ..stats_widget import StatsWidget
from ..process_table import ProcessTable
from ..gantt_chart import GanttChart
from ..simulation_thread import SimulationThread
from ..process_control_widget import ProcessControlWidget

from ...core.simulation import Simulation
from ...models.process import Process

# Import schedulers
from ...algorithms.fcfs import FCFSScheduler
from ...algorithms.sjf_non_preemptive import SJFNonPreemptiveScheduler
from ...algorithms.sjf_preemptive import SJFPreemptiveScheduler
from ...algorithms.priority_non_preemptive import PriorityNonPreemptiveScheduler
from ...algorithms.priority_preemptive import PriorityPreemptiveScheduler
from ...algorithms.round_robin import RoundRobinScheduler

class SimulationScene(BaseScene):
    """Scene for running and visualizing the simulation."""
    
    def __init__(self, parent=None):
        # Initialize variables
        self.processes = []
        self.current_scheduler = None
        self.simulation = None
        self.simulation_thread = None
        self.is_paused = False
        self.scheduler_control = None
        self.process_table = None
        self.gantt_chart = None
        self.stats_widget = None
        self.process_control = None  # Added for live process addition
        self.next_pid = 1  # Track the next process ID
        
        super().__init__(parent)
        
    def setup_ui(self):
        """Setup the simulation scene UI."""        
        super().setup_ui()
        
        # Main vertical layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        
        # Main splitter (horizontal) - Control panels on left, visualization on right
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setHandleWidth(2)
        self.main_splitter.setChildrenCollapsible(False)
        
        # Left side - Controls
        left_scroll_area = QScrollArea()
        left_scroll_area.setWidgetResizable(True)
        left_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        left_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        left_scroll_area.setFrameShape(QFrame.NoFrame)  # Use QFrame.NoFrame instead of None
        
        left_scroll_content = QWidget()
        left_layout = QVBoxLayout(left_scroll_content)
        
        left_panel = QSplitter(Qt.Vertical)
        left_panel.setHandleWidth(2)
        left_panel.setChildrenCollapsible(False)
        
        # Scheduler control widget
        self.scheduler_control = SchedulerControlWidget()
        left_panel.addWidget(self.scheduler_control)
        
        # Process control widget - For adding processes during simulation (with is_runtime=True)
        self.process_control = ProcessControlWidget(is_runtime=True)
        left_panel.addWidget(self.process_control)
        
        # Statistics widget
        self.stats_widget = StatsWidget()
        left_panel.addWidget(self.stats_widget)
        
        left_layout.addWidget(left_panel)
        left_scroll_area.setWidget(left_scroll_content)
        
        # Right side - Visualization tabs
        self.right_panel = QTabWidget()
        self.right_panel.setTabPosition(QTabWidget.North)
        self.right_panel.setDocumentMode(True)
        self.right_panel.setMovable(True)
        
        # Process table tab
        self.process_table = ProcessTable()
        self.right_panel.addTab(self.process_table, "Process Table")
        
        # Gantt chart tab
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
        self.main_splitter.addWidget(left_scroll_area)
        self.main_splitter.addWidget(self.right_panel)
        
        # Set initial sizes (left panel gets 1/3, right panel gets 2/3)
        self.main_splitter.setSizes([400, 800])
        
        # Add splitter to main layout
        main_layout.addWidget(self.main_splitter, 1)
        
        # Navigation buttons at bottom
        nav_layout = QHBoxLayout()
        nav_layout.addStretch(1)
        
        # View Results button
        self.view_results_button = QPushButton("View Detailed Results")
        self.view_results_button.clicked.connect(self.on_view_results)
        self.view_results_button.setEnabled(False)  # Disabled until simulation completes
        nav_layout.addWidget(self.view_results_button)
        
        main_layout.addLayout(nav_layout)
        
        # Set the main layout
        self.layout.addLayout(main_layout)
        
        # Connect signals and slots
        self.connect_signals()
        
    def connect_signals(self):
        """Connect all signals and slots."""        
        # Scheduler control signals
        self.scheduler_control.algorithm_group.buttonClicked.connect(self.on_scheduler_changed)
        self.scheduler_control.speed_slider.valueChanged.connect(self.on_speed_changed)
        self.scheduler_control.start_button.clicked.connect(self.on_start)
        self.scheduler_control.pause_resume_button.clicked.connect(self.on_pause_resume)
        self.scheduler_control.run_all_button.clicked.connect(self.on_run_all)
        
        # Process control signals - For live process addition
        self.process_control.add_process_button.clicked.connect(self.on_add_process_during_simulation)
        self.process_control.remove_all_button.clicked.connect(self.on_remove_all_processes)
        # Connect the Reset Gantt Chart button
        self.process_control.reset_gantt_button.clicked.connect(self.on_reset_gantt_chart)
        
    # Add the handler for the Reset Gantt Chart button
    def on_reset_gantt_chart(self):
        """Handle resetting the Gantt chart visualization and stop execution."""
        # Stop any running simulation
        self.stop_simulation()
        
        # Reset the Gantt Chart
        if self.gantt_chart:
            self.gantt_chart.reset()
            
        # Reset the process table
        self._update_process_table()
            
        # Show the reset was successful
        QMessageBox.information(
            self,
            "Simulation Reset",
            "The simulation has been reset. Press Start to begin again.",
            QMessageBox.Ok
        )
        
        # Focus on the Gantt Chart tab so users can see the reset happened
        self.right_panel.setCurrentIndex(1)  # Index of Gantt Chart tab
        
        # Ensure the start button is enabled
        self.scheduler_control.start_button.setEnabled(True)
        
    def on_add_process_during_simulation(self):
        """Handle adding a process during simulation execution."""
        if not self.simulation or not self.simulation_thread:
            return
            
        # Get values from the process control widget
        name = self.process_control.process_name_input.text()
        burst_time = self.process_control.burst_time_spinbox.value()
        priority = self.process_control.priority_spinbox.value()
        
        # Use current simulation time as arrival time
        current_time = self.simulation.scheduler.current_time
        
        # Use the specialized method to add a process during live execution
        process = self.simulation.add_live_process(
            name=name,
            burst_time=burst_time,
            priority=priority,
            pid=self.next_pid
        )
        
        # Increment PID counter
        self.next_pid += 1
        
        # Add to processes list (it's already in the simulation)
        self.processes.append(process)
        
        # Generate next process name
        self.process_control.next_process_name()
        
        # Show confirmation message that clearly indicates the arrival time
        QMessageBox.information(
            self,
            "Process Added",
            f"Added {name} with arrival time {current_time} (current simulation time)"
        )
        
    def on_remove_all_processes(self):
        """Handle removing all processes."""        
        if not self.simulation:
            return
            
        reply = QMessageBox.question(
            self,
            "Remove All Processes",
            "Are you sure you want to remove all processes?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.simulation.remove_all_processes()
            self.processes = []
        
    def enter_scene(self, processes=None):
        """
        Handle entering the scene, optionally with processes.
        
        Args:
            processes (list, optional): List of Process objects to simulate
        """
        if processes and isinstance(processes, list) and all(isinstance(p, Process) for p in processes):
            self.processes = processes
            # Set the next_pid for future additions
            self.next_pid = max(p.pid for p in processes) + 1 if processes else 1
            self._update_process_table()
        elif not self.processes:
            # If no processes were passed and we don't have any, go back to process input
            QMessageBox.warning(
                self,
                "No Processes",
                "Please add processes before starting the simulation."
            )
            self.switch_scene.emit("process_input")
            return
            
        # Initialize the first scheduler
        self.on_scheduler_changed(0)
        
        # Set up process control for live additions
        self.process_control.process_count = len(self.processes)
        self.process_control.next_process_name()
        
    def exit_scene(self):
        """Handle exiting the scene."""        
        # Stop any running simulation
        self.stop_simulation()
        
    def set_dark_mode(self, enabled):
        """
        Enable or disable dark mode for the simulation scene.
        
        Args:
            enabled (bool): Whether dark mode should be enabled
        """
        # Update dark mode for component widgets
        if self.process_table:
            self.process_table.set_dark_mode(enabled)
        if self.gantt_chart:
            self.gantt_chart.set_dark_mode(enabled)
        
    def on_scheduler_changed(self, index):
        """
        Handle scheduler type change.
        
        Args:
            index (int): Index of the selected scheduler in the combo box
        """
        # Get the current algorithm index from the radio buttons
        index = self.scheduler_control.get_selected_algorithm_index()
        
        scheduler_types = [
            FCFSScheduler,
            SJFNonPreemptiveScheduler, 
            SJFPreemptiveScheduler,
            PriorityNonPreemptiveScheduler,
            PriorityPreemptiveScheduler,
            RoundRobinScheduler
        ]
        
        if 0 <= index < len(scheduler_types):
            scheduler_class = scheduler_types[index]
            
            # For Round Robin, get the quantum value
            if index == 5:  # Round Robin
                quantum = self.scheduler_control.time_quantum_spinbox.value()
                self.current_scheduler = scheduler_class(time_quantum=quantum)
            else:
                self.current_scheduler = scheduler_class()
        
    def on_speed_changed(self, value):
        """
        Update simulation speed.
        
        Args:
            value (int): New speed multiplier
        """
        # Update the speed label
        self.scheduler_control.update_speed_label(value)
        
        # Update simulation speed if one exists
        if self.simulation:
            self.simulation.set_speed(value)
        
    def on_start(self):
        """Handle start button click."""        
        if not self.processes:
            QMessageBox.warning(
                self, 
                "No Processes", 
                "Please add processes before starting the simulation."
            )
            return
            
        # Stop any existing simulation
        self.stop_simulation()
        
        # Reset components
        self.gantt_chart.reset()
        self._update_process_table()
        
        # Get current scheduler settings from radio buttons
        index = self.scheduler_control.get_selected_algorithm_index()
        if index == 5:  # Round Robin
            quantum = self.scheduler_control.time_quantum_spinbox.value()
            self.current_scheduler = RoundRobinScheduler(time_quantum=quantum)
        
        # Clone processes to prevent modifying originals
        processes = [p.clone() for p in self.processes]
        
        # Add processes to the scheduler
        for process in processes:
            self.current_scheduler.add_process(process)
        
        # Calculate simulation speed from slider
        speed_factor = self.scheduler_control.speed_slider.value()
        delay = 1.0 / speed_factor if speed_factor > 0 else 0.01
        
        # Create new simulation with the configured scheduler
        self.simulation = Simulation(
            scheduler=self.current_scheduler,
            delay=delay
        )
        
        # Update UI state
        self.scheduler_control.start_button.setEnabled(False)
        self.scheduler_control.pause_resume_button.setEnabled(True)
        self.scheduler_control.pause_resume_button.setText("Pause")
        self.scheduler_control.pause_resume_button.setIcon(QIcon.fromTheme("media-playback-pause"))
        self.view_results_button.setEnabled(False)
        self.is_paused = False
        
        # Create and start the simulation thread
        self.simulation_thread = SimulationThread(self.simulation)
        self.simulation_thread.process_updated.connect(self.on_processes_updated)
        self.simulation_thread.gantt_updated.connect(self.on_gantt_updated)
        self.simulation_thread.stats_updated.connect(self.on_stats_updated)
        self.simulation_thread.finished.connect(self.on_simulation_finished)
        self.simulation_thread.start()
        
    def on_pause_resume(self):
        """Handle pause/resume button click."""        
        if not self.simulation or not self.simulation_thread:
            return
            
        if self.is_paused:
            # Resume
            self.simulation.resume()
            self.scheduler_control.pause_resume_button.setText("Pause")
            self.scheduler_control.pause_resume_button.setIcon(QIcon.fromTheme("media-playback-pause"))
            self.is_paused = False
        else:
            # Pause
            self.simulation.pause()
            self.scheduler_control.pause_resume_button.setText("Resume")
            self.scheduler_control.pause_resume_button.setIcon(QIcon.fromTheme("media-playback-start"))
            self.is_paused = True
            
    def on_run_all(self):
        """Handle run all at once button click."""        
        if not self.processes:
            QMessageBox.warning(
                self, 
                "No Processes", 
                "Please add processes before starting the simulation."
            )
            return
            
        # Confirmation dialog
        reply = QMessageBox.question(
            self,
            "Run All At Once",
            "This will complete the simulation instantly. Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return
            
        # Stop any existing simulation
        self.stop_simulation()
        
        # Reset components
        self.gantt_chart.reset()
        self._update_process_table()
        
        # Get current scheduler settings from radio buttons
        index = self.scheduler_control.get_selected_algorithm_index()
        
        scheduler_types = [
            FCFSScheduler,
            SJFNonPreemptiveScheduler, 
            SJFPreemptiveScheduler,
            PriorityNonPreemptiveScheduler,
            PriorityPreemptiveScheduler,
            RoundRobinScheduler
        ]
        
        if 0 <= index < len(scheduler_types):
            scheduler_class = scheduler_types[index]
            
            # Create a fresh scheduler instance
            if index == 5:  # Round Robin
                quantum = self.scheduler_control.time_quantum_spinbox.value()
                self.current_scheduler = scheduler_class(time_quantum=quantum)
            else:
                self.current_scheduler = scheduler_class()
        
        # Clone processes to prevent modifying originals
        processes = [p.clone() for p in self.processes]
        
        # Add processes to the scheduler
        for process in processes:
            self.current_scheduler.add_process(process)
        
        # Create new simulation with minimal delay for instant execution
        self.simulation = Simulation(
            scheduler=self.current_scheduler,
            delay=0.001  # Very small delay for "instant" execution
        )
        
        # Run all at once using run_all_at_once method
        self.simulation.run_all_at_once()
        
        # Update the UI with results
        self.on_processes_updated(self.simulation.scheduler.processes, self.simulation.current_time)
        
        self.gantt_chart.reset()
        # We need to get timeline entries from the simulation
        # Since get_timeline_entries doesn't exist, we'll reconstruct it from process execution history
        for process in self.simulation.scheduler.processes:
            if process.execution_history:
                for start, end in process.execution_history:
                    # Update chart for each execution period
                    self.gantt_chart.update_chart(process, end)
            
        # Update stats
        avg_waiting = self.simulation.scheduler.get_average_waiting_time()
        avg_turnaround = self.simulation.scheduler.get_average_turnaround_time()
        avg_response = self.simulation.scheduler.get_average_response_time()
        
        # These methods don't exist in the current Simulation class
        # Let's calculate them directly or use alternative methods
        try:
            cpu_util = self.simulation.get_cpu_utilization() * 100  # Convert to percentage
        except AttributeError:
            # Calculate CPU utilization manually if method doesn't exist
            total_burst_time = sum(p.burst_time for p in self.simulation.scheduler.processes)
            last_completion = max((p.completion_time for p in self.simulation.scheduler.processes 
                                  if p.completion_time is not None), default=0)
            cpu_util = (total_burst_time / last_completion * 100) if last_completion > 0 else 0
            
        try:
            throughput = self.simulation.get_throughput()
        except AttributeError:
            # Calculate throughput manually if method doesn't exist
            completed_count = sum(1 for p in self.simulation.scheduler.processes 
                                 if p.completion_time is not None)
            last_completion = max((p.completion_time for p in self.simulation.scheduler.processes 
                                  if p.completion_time is not None), default=0)
            throughput = (completed_count / last_completion) if last_completion > 0 else 0
        
        self.stats_widget.update_stats(
            avg_waiting=avg_waiting,
            avg_turnaround=avg_turnaround,
            avg_response=avg_response,
            cpu_utilization=cpu_util,
            throughput=throughput
        )
        
        # Update UI state
        self.scheduler_control.start_button.setEnabled(True)
        self.scheduler_control.pause_resume_button.setEnabled(False)
        self.view_results_button.setEnabled(True)
        
        # Show completion message
        QMessageBox.information(
            self,
            "Simulation Complete",
            "The simulation has completed. You can view the detailed results."
        )
            
    def on_processes_updated(self, processes, current_time):
        """
        Handle process update signal from the simulation thread.
        
        Args:
            processes (list): Updated process list
            current_time (int): Current simulation time
        """
        self.process_table.update_table(processes, current_time)
        
    def on_gantt_updated(self, current_process, current_time):
        """
        Handle Gantt chart update signal from the simulation thread.
        
        Args:
            current_process (Process): Currently running process, or None if CPU is idle
            current_time (int): Current simulation time
        """
        self.gantt_chart.update_chart(current_process, current_time)
        
    def on_stats_updated(self, avg_waiting, avg_turnaround):
        """
        Handle statistics update signal from the simulation thread.
        
        Args:
            avg_waiting (float): Average waiting time
            avg_turnaround (float): Average turnaround time
        """
        if not self.simulation:
            return
            
        # Calculate additional statistics
        avg_response = self.simulation.scheduler.get_average_response_time()
        cpu_util = self.simulation.get_cpu_utilization() * 100  # Convert to percentage
        throughput = self.simulation.get_throughput()
        
        # Update the statistics widget
        self.stats_widget.update_stats(
            avg_waiting=avg_waiting,
            avg_turnaround=avg_turnaround,
            avg_response=avg_response,
            cpu_utilization=cpu_util,
            throughput=throughput
        )
        
    def on_simulation_finished(self):
        """Handle simulation completion."""        
        # Enable/disable UI elements
        self.scheduler_control.start_button.setEnabled(True)
        self.scheduler_control.pause_resume_button.setEnabled(False)
        self.view_results_button.setEnabled(True)
        
        # Reset the pause state
        self.is_paused = False
        
    def stop_simulation(self):
        """Stop the current simulation if one is running."""        
        if self.simulation:
            self.simulation.stop()
            
        if self.simulation_thread and self.simulation_thread.isRunning():
            self.simulation_thread.wait()
            
        # Reset variables
        self.simulation = None
        self.simulation_thread = None
        self.is_paused = False
        
        # Reset UI state
        self.scheduler_control.start_button.setEnabled(True)
        self.scheduler_control.pause_resume_button.setEnabled(False)
        
    def on_view_results(self):
        """Handle view results button click."""        
        # Prepare results data
        if not self.simulation:
            return
            
        # Get the scheduler name based on selected radio button
        algorithm_names = [
            "First Come First Served (FCFS)",
            "Shortest Job First (Non-Preemptive)",
            "Shortest Job First (Preemptive)",
            "Priority (Non-Preemptive)",
            "Priority (Preemptive)",
            "Round Robin (RR)"
        ]
        index = self.scheduler_control.get_selected_algorithm_index()
        scheduler_name = algorithm_names[index] if 0 <= index < len(algorithm_names) else "Unknown"
        
        # Calculate statistics
        stats = {
            'avg_waiting': self.simulation.scheduler.get_average_waiting_time(),
            'avg_turnaround': self.simulation.scheduler.get_average_turnaround_time(),
            'avg_response': self.simulation.scheduler.get_average_response_time(),
            'cpu_utilization': self.simulation.get_cpu_utilization() * 100,  # Percentage
            'throughput': self.simulation.get_throughput()
        }
        
        # Package the data
        results_data = {
            'processes': self.simulation.scheduler.processes,
            'scheduler_name': scheduler_name,
            'stats': stats
        }
        
        # Switch to results scene
        self.switch_scene.emit("results")
        
        # Get the scene manager and pass the data to results scene
        scene_manager = self.window().scene_manager
        if scene_manager:
            scene_manager.set_scene_data("simulation", results_data)
            scene_manager.show_scene("results", results_data)
            
    def _update_process_table(self):
        """Update the process table with current processes."""        
        if self.process_table and self.processes:
            self.process_table.update_table(self.processes, 0)
            
        # Set up removal callback
        self.process_table.set_remove_callback(self.on_remove_process)
        
    def on_remove_process(self, pid):
        """Remove a process by its ID."""        
        if self.simulation:
            self.simulation.remove_process(pid)
        
        self.processes = [p for p in self.processes if p.pid != pid]