from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                          QGroupBox, QLabel, QLineEdit, QSpinBox, 
                          QPushButton, QFormLayout, QFrame, QCheckBox)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt

class ProcessControlWidget(QWidget):
    """Widget for process control."""
    
    def __init__(self, parent=None, is_runtime=False):
        super().__init__(parent)
        self.process_count = 0
        self.is_runtime = is_runtime  # Flag to determine if this is for runtime process addition
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
        
        # Arrival time - Only show in pre-simulation mode
        self.arrival_time_spinbox = None
        if not self.is_runtime:
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
        
        # Auto arrival time notice - Only show in runtime mode (MOVED TO END OF FORM)
        if self.is_runtime:
            # Create a container with a border and background to make the notice more visible
            arrival_note_container = QFrame()
            arrival_note_container.setFrameShape(QFrame.StyledPanel)
            arrival_note_container.setFrameShadow(QFrame.Raised)
            arrival_note_container.setStyleSheet("""
                background-color: #FFF3CD; /* Light yellow background */
                border: 1px solid #FFEEBA; /* Light yellow border */
                border-radius: 6px;
                padding: 4px;
            """)
            
            arrival_note_layout = QVBoxLayout(arrival_note_container)
            arrival_note_layout.setContentsMargins(8, 6, 8, 6)
            arrival_note_layout.setSpacing(2)
            
            # Add a bold label with note icon
            note_label = QLabel("Current Simulation Time")
            note_label.setStyleSheet("font-weight: bold; color: #856404;") # Dark yellow text
            
            # Add explanation text
            explanation = QLabel("Process will be added with arrival time\nequal to the current simulation time")
            explanation.setStyleSheet("color: #856404;") # Dark yellow text
            
            arrival_note_layout.addWidget(note_label)
            arrival_note_layout.addWidget(explanation)
            
            process_form.addRow("Arrival:", arrival_note_container)
        
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
        
        # Clear All button (full width)
        self.remove_all_button = QPushButton("Clear All")
        self.remove_all_button.setIcon(QIcon.fromTheme("edit-clear"))
        self.remove_all_button.setFixedHeight(40) # Adjusted height
        self.remove_all_button.setObjectName("remove_all_button")
        buttons_layout.addWidget(self.remove_all_button)
        
        # Add Reset Gantt Chart button in runtime mode (Note: Only for runtime process addition)
        if self.is_runtime:
            self.reset_gantt_button = QPushButton("Reset Gantt Chart")
            self.reset_gantt_button.setIcon(QIcon.fromTheme("view-refresh"))
            self.reset_gantt_button.setFixedHeight(40) # Adjusted height
            self.reset_gantt_button.setObjectName("reset_gantt_button")
            # Add tooltip to explain what it does
            self.reset_gantt_button.setToolTip("Reset the Gantt chart visualization without affecting the simulation")
            buttons_layout.addWidget(self.reset_gantt_button)
        
        # File buttons only available in pre-simulation mode
        if not self.is_runtime:
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
            f"background-color: {process_colors[color_index]}; border-radius: 8px;"
        )
        
    def reset_count(self):
        """Reset the process counter."""
        self.process_count = 0
        self.process_name_input.setText("Process 1")
        self.color_preview.setStyleSheet("background-color: #FF6347; border-radius: 8px;") # Slightly less rounded
        
    def is_auto_arrival_enabled(self):
        """Check if auto arrival time is enabled."""
        # Always return True for runtime mode
        if self.is_runtime:
            return True
        # Not applicable for pre-simulation mode
        return False
        
    def get_arrival_time(self):
        """Get the arrival time value."""
        # For pre-simulation, use the spinbox value
        if not self.is_runtime and self.arrival_time_spinbox:
            return self.arrival_time_spinbox.value()
        # For runtime, this should be determined by the simulation
        return None