class Process:
    """
    Represents a process in the CPU scheduler simulation.
    """
    
    def __init__(self, pid, name, arrival_time, burst_time, priority=0):
        """
        Initialize a new Process instance.
        
        Args:
            pid (int): Process ID
            name (str): Process name
            arrival_time (int): The time when the process arrives
            burst_time (int): The total CPU time needed by the process
            priority (int, optional): Priority of the process (smaller value means higher priority)
        """
        self.pid = pid
        self.name = name
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.remaining_time = burst_time
        self.priority = priority
        self.start_time = None
        self.completion_time = None
        self.waiting_time = 0
        self.turnaround_time = 0
        self.response_time = None
        self.execution_history = []  # List of (start_time, end_time) tuples
        
    def reset(self):
        """Reset the process state for a new simulation."""
        self.remaining_time = self.burst_time
        self.start_time = None
        self.completion_time = None
        self.waiting_time = 0
        self.turnaround_time = 0
        self.response_time = None
        self.execution_history = []
        
    def reset_progress(self):
        """Reset the progress of the process (alias for reset)."""
        self.reset()
        
    def is_completed(self):
        """Check if the process has completed execution."""
        return self.remaining_time <= 0
        
    def calculate_turnaround_time(self):
        """Calculate and set the turnaround time."""
        if self.completion_time is not None:
            self.turnaround_time = self.completion_time - self.arrival_time
            
    def calculate_waiting_time(self):
        """Calculate and set the waiting time."""
        if self.turnaround_time:
            self.waiting_time = self.turnaround_time - self.burst_time
            
    def execute(self, current_time, time_quantum=1):
        """
        Execute the process for the given time quantum.
        
        Args:
            current_time (int): Current simulation time
            time_quantum (int): Amount of time to execute
            
        Returns:
            int: The amount of time actually used (may be less than time_quantum if process completes)
        """
        if self.start_time is None:
            self.start_time = current_time
            self.response_time = current_time - self.arrival_time
            
        execution_time = min(self.remaining_time, time_quantum)
        self.remaining_time -= execution_time
        
        # Record this execution period
        self.execution_history.append((current_time, current_time + execution_time))
        
        if self.is_completed():
            self.completion_time = current_time + execution_time
            self.calculate_turnaround_time()
            self.calculate_waiting_time()
            
        return execution_time
    
    def __str__(self):
        """String representation of the process."""
        return f"Process {self.pid} ({self.name}): arrival={self.arrival_time}, burst={self.burst_time}, priority={self.priority}"