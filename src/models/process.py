from dataclasses import dataclass

class Process:
    """
    Represents a process in the CPU scheduling simulation.
    """
    
    def __init__(self, pid: int, name: str, arrival_time: int, burst_time: int, priority: int = None):
        """
        Initialize a new Process instance.
        
        Args:
            pid (int): Process ID
            name (str): Process name
            arrival_time (int): Arrival time of the process
            burst_time (int): Burst time required by the process
            priority (int, optional): Priority of the process (lower value means higher priority)
        """
        self.pid = pid
        self.name = name
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.priority = priority
        
        # Runtime state
        self.remaining_time = burst_time
        self.completion_time = None
        self.waiting_time = 0
        self.turnaround_time = 0
        self.response_time = None
        self.start_time = None
        self.execution_history = []  # List of (start_time, end_time) tuples
        
    def reset(self):
        """Reset the process state for a new simulation."""
        self.remaining_time = self.burst_time
        self.completion_time = None
        self.waiting_time = 0
        self.turnaround_time = 0
        self.response_time = None
        self.start_time = None
        self.execution_history = []
        
    def execute(self, current_time: int, time_slice: int = 1) -> int:
        """
        Execute the process for the given time slice.
        
        Args:
            current_time (int): Current simulation time
            time_slice (int): Maximum time to execute
            
        Returns:
            int: Actual time executed
        """
        # If first execution, record response time
        if self.response_time is None:
            self.response_time = current_time - self.arrival_time
            
        # If first time, record start time
        if self.start_time is None:
            self.start_time = current_time
            
        # Calculate how much time to actually execute
        time_to_execute = min(time_slice, self.remaining_time)
        
        # Update remaining time
        self.remaining_time -= time_to_execute
        
        # Record execution interval
        self.execution_history.append((current_time, current_time + time_to_execute))
        
        # If process completes, calculate metrics
        if self.remaining_time == 0:
            self.completion_time = current_time + time_to_execute
            self.turnaround_time = self.completion_time - self.arrival_time
            self.waiting_time = self.turnaround_time - self.burst_time
            
        return time_to_execute
        
    def is_completed(self) -> bool:
        """Check if the process has completed execution."""
        return self.remaining_time <= 0
        
    def __str__(self) -> str:
        """Return string representation of the process."""
        return f"P{self.pid} ({self.name})"
        
    def __repr__(self) -> str:
        """Return string representation of the process."""
        return f"Process(pid={self.pid}, name='{self.name}', arrival_time={self.arrival_time}, burst_time={self.burst_time}, priority={self.priority})"