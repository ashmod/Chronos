from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                          QGroupBox, QLabel, QSpinBox, QPushButton, 
                          QRadioButton, QButtonGroup, QSlider)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class SchedulerControlWidget(QWidget):
    """Widget for scheduler control."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the scheduler control UI."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Scheduler selection
        scheduler_group = QGroupBox("CPU Scheduling Algorithm")
        scheduler_group.setFont(QFont("", 10, QFont.Bold))
        scheduler_layout = QVBoxLayout(scheduler_group)
        scheduler_layout.setSpacing(10)
        
        # Using radio buttons instead of a problematic dropdown
        self.algorithm_group = QButtonGroup(self)
        
        # Create radio buttons for each algorithm
        self.fcfs_radio = QRadioButton("First Come First Served (FCFS)")
        self.sjf_np_radio = QRadioButton("Shortest Job First (Non-Preemptive)")
        self.sjf_p_radio = QRadioButton("Shortest Job First (Preemptive)")
        self.priority_np_radio = QRadioButton("Priority (Non-Preemptive)")
        self.priority_p_radio = QRadioButton("Priority (Preemptive)")
        self.rr_radio = QRadioButton("Round Robin (RR)")
        
        # Set font for all radio buttons
        font = QFont()
        font.setPointSize(10)
        for radio in [self.fcfs_radio, self.sjf_np_radio, self.sjf_p_radio, 
                      self.priority_np_radio, self.priority_p_radio, self.rr_radio]:
            radio.setFont(font)
            self.algorithm_group.addButton(radio)
            scheduler_layout.addWidget(radio)
        
        # Select FCFS by default
        self.fcfs_radio.setChecked(True)
        
        # Algorithm description label
        self.algorithm_info_label = QLabel()
        self.algorithm_info_label.setWordWrap(True)
        self.algorithm_info_label.setFont(QFont("", 9))
        self.algorithm_info_label.setStyleSheet("color: #555555; margin-left: 20px;")
        self.algorithm_info_label.setMinimumHeight(40)
        scheduler_layout.addWidget(self.algorithm_info_label)
        
        # Time quantum for Round Robin - in its own container 
        self.quantum_widget = QWidget()
        quantum_layout = QHBoxLayout(self.quantum_widget)
        quantum_layout.setContentsMargins(20, 5, 0, 5)  # Additional left margin for indentation
        
        quantum_label = QLabel("Time Quantum:")
        quantum_label.setFont(QFont("", 10))
        
        self.time_quantum_spinbox = QSpinBox()
        self.time_quantum_spinbox.setRange(1, 100)
        self.time_quantum_spinbox.setValue(2)
        self.time_quantum_spinbox.setMinimumHeight(28)
        self.time_quantum_spinbox.setMinimumWidth(80)
        self.time_quantum_spinbox.setFont(QFont("", 10))
        
        units_label = QLabel("time units")
        units_label.setFont(QFont("", 10))
        
        quantum_layout.addWidget(quantum_label)
        quantum_layout.addWidget(self.time_quantum_spinbox)
        quantum_layout.addWidget(units_label)
        quantum_layout.addStretch()
        
        self.quantum_widget.setVisible(False)  # Hidden by default
        scheduler_layout.addWidget(self.quantum_widget)
        
        layout.addWidget(scheduler_group)
        
        # Simulation control group
        control_group = QGroupBox("Simulation Control")
        control_group.setFont(QFont("", 10, QFont.Bold))
        control_layout = QVBoxLayout(control_group)
        control_layout.setSpacing(15)
        
        # Speed control
        speed_layout = QHBoxLayout()
        speed_layout.setSpacing(10)
        
        speed_label = QLabel("Speed:")
        speed_label.setFont(QFont("", 10))
        
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 10)
        self.speed_slider.setValue(1)
        self.speed_slider.setTickPosition(QSlider.TicksBelow)
        self.speed_slider.setTickInterval(1)
        
        self.speed_label = QLabel("1×")
        self.speed_label.setFont(QFont("", 10, QFont.Bold))
        self.speed_label.setMinimumWidth(30)
        
        speed_layout.addWidget(speed_label)
        speed_layout.addWidget(self.speed_slider, 1)
        speed_layout.addWidget(self.speed_label)
        
        control_layout.addLayout(speed_layout)
        
        # Control buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        # Start button
        self.start_button = QPushButton("Start")
        self.start_button.setFont(QFont("", 10, QFont.Bold))
        self.start_button.setMinimumHeight(36)
        buttons_layout.addWidget(self.start_button)
        
        # Pause/Resume button
        self.pause_resume_button = QPushButton("Pause")
        self.pause_resume_button.setFont(QFont("", 10, QFont.Bold))
        self.pause_resume_button.setEnabled(False)
        self.pause_resume_button.setMinimumHeight(36)
        buttons_layout.addWidget(self.pause_resume_button)
        
        control_layout.addLayout(buttons_layout)
        
        # Run all at once button
        self.run_all_button = QPushButton("Run Entire Simulation")
        self.run_all_button.setFont(QFont("", 10, QFont.Bold))
        self.run_all_button.setMinimumHeight(36)
        control_layout.addWidget(self.run_all_button)
        
        layout.addWidget(control_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        # Connect signals
        self.algorithm_group.buttonClicked.connect(self._on_algorithm_changed)
        self.speed_slider.valueChanged.connect(self.update_speed_label)
        
        # Initialize algorithm info
        self._on_algorithm_changed(self.fcfs_radio)
    
    def _on_algorithm_changed(self, button):
        """Update UI based on selected algorithm radio button"""
        # Get the index based on which radio button was clicked
        radios = [self.fcfs_radio, self.sjf_np_radio, self.sjf_p_radio, 
                  self.priority_np_radio, self.priority_p_radio, self.rr_radio]
        
        index = radios.index(button) if button in radios else 0
        
        # Update algorithm info text with descriptions
        algorithm_descriptions = [
            "First Come First Served: Processes are executed in the order they arrive. Simple but may cause long waiting times for short processes.",
            "Shortest Job First (Non-Preemptive): Selects the process with shortest burst time. Minimizes average waiting time but may cause starvation.",
            "Shortest Job First (Preemptive): Running process is interrupted when a new process with shorter remaining time arrives. Also known as SRTF.",
            "Priority Scheduling (Non-Preemptive): Selects process with highest priority. May cause starvation of low-priority processes.",
            "Priority Scheduling (Preemptive): Running process is interrupted when a higher priority process arrives.",
            "Round Robin: Each process gets a fixed time slice in a cyclic manner. Good for time-sharing systems."
        ]
        
        if 0 <= index < len(algorithm_descriptions):
            self.algorithm_info_label.setText(algorithm_descriptions[index])
        
        # Show/hide quantum input for Round Robin
        is_round_robin = (index == 5)
        self.quantum_widget.setVisible(is_round_robin)
    
    def get_selected_algorithm_index(self):
        """Get the index of the currently selected algorithm"""
        radios = [self.fcfs_radio, self.sjf_np_radio, self.sjf_p_radio, 
                  self.priority_np_radio, self.priority_p_radio, self.rr_radio]
        
        for i, radio in enumerate(radios):
            if radio.isChecked():
                return i
        return 0  # Default to FCFS
        
    def update_speed_label(self, value):
        """Update the speed indicator label"""
        self.speed_label.setText(f"{value}×")