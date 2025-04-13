from ..core.scheduler import Scheduler
from ..models.process import Process
from typing import Optional, List
from collections import deque

class RoundRobinScheduler(Scheduler):
    """
    Round Robin scheduling algorithm.
    Each process is given a fixed time slice (quantum) to execute.
    Processes are executed in a circular queue.
    """
    
    def __init__(self, time_quantum=2):
        """
        Initialize a new RoundRobinScheduler instance.
        
        Args:
            time_quantum (int): The time quantum for each process (default: 2)
        """
        super().__init__("Round Robin")
        self.time_quantum = time_quantum
        self.time_slice = time_quantum  # Override the default time slice
        self.ready_queue = deque()
        self.current_process = None
        self.current_process_time = 0
    
    def add_process(self, process: Process):
        """
        Add a process to the scheduler.
        
        Args:
            process (Process): The process to add
        """
        super().add_process(process)
        
    def reset(self):
        """Reset the scheduler state for a new simulation."""
        super().reset()
        self.ready_queue = deque()
        self.current_process = None
        self.current_process_time = 0
        
    def get_next_process(self, current_time) -> Optional[Process]:
        """
        Get the next process to execute based on Round Robin scheduling.
        
        Args:
            current_time (int): Current simulation time
            
        Returns:
            Optional[Process]: The next process to execute, or None if no process is ready
        """
        # Get all processes that have arrived by the current time and haven't completed
        arrived_processes = self.get_arrived_processes(current_time)
        
        # Check if any new processes have arrived that are not in the ready queue
        for process in arrived_processes:
            if process not in self.ready_queue and process != self.current_process:
                self.ready_queue.append(process)
        
        # If current process has used its time quantum or completed, move to the next process
        if (self.current_process and (
                self.current_process_time >= self.time_quantum or 
                self.current_process.is_completed())):
            
            # If current process has not completed, add it back to the ready queue
            if self.current_process and not self.current_process.is_completed():
                self.ready_queue.append(self.current_process)
                
            # Reset current process
            self.current_process = None
            self.current_process_time = 0
        
        # If there is no current process, get the next one from the queue
        if not self.current_process and self.ready_queue:
            self.current_process = self.ready_queue.popleft()
            self.current_process_time = 0
            
        # Increment the time the current process has been running
        if self.current_process:
            self.current_process_time += 1
            
        return self.current_process