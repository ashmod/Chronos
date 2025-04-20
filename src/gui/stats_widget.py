from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, 
                          QLabel, QFormLayout)
from PyQt5.QtCore import Qt

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
        
    def update_stats(self, avg_waiting: float, avg_turnaround: float, avg_response: float = 0.0, cpu_utilization: float = 0, throughput: float = 0.0):
        """
        Update statistics display.
        
        Args:
            avg_waiting (float): Average waiting time
            avg_turnaround (float): Average turnaround time
            avg_response (float, optional): Average response time
            cpu_utilization (float, optional): CPU utilization percentage
            throughput (float, optional): System throughput
        """
        self.avg_waiting_label.setText(f"{avg_waiting:.2f}")
        self.avg_turnaround_label.setText(f"{avg_turnaround:.2f}")
        self.avg_response_label.setText(f"{avg_response:.2f}")
        self.cpu_label.setText(f"{cpu_utilization:.0f}%")
        self.throughput_label.setText(f"{throughput:.2f} processes/unit time")