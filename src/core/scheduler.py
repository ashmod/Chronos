from abc import ABC, abstractmethod
from typing import List, Optional
from ..models.process import Process

class Scheduler(ABC):
    """
    Abstract base class for all CPU scheduling algorithms.
    """
    
    def __init__(self, name):
        """
        Initialize a new Scheduler instance.
        
        Args:
            name (str): Name of the scheduler
        """
        self.name = name
        self.processes = []
        self.current_process = None
        self.current_time = 0
        self.time_slice = 1  # Default time slice of 1 time unit
        self.completed_processes = []
        
    def add_process(self, process: Process):
        """
        Add a process to the scheduler.
        
        Args:
            process (Process): The process to add
        """
        self.processes.append(process)
        
    def reset(self):
        """Reset the scheduler state for a new simulation."""
        self.current_time = 0
        self.current_process = None
        self.completed_processes = []
        for process in self.processes:
            process.reset()
            
    def reset_state(self):
        """Reset only the scheduler state without resetting processes."""
        self.current_time = 0
        self.current_process = None
        self.completed_processes = []

    def all_processes_completed(self) -> bool:
        """Check if all processes have completed execution."""
        return all(process.is_completed() for process in self.processes)
        
    def get_arrived_processes(self, current_time) -> List[Process]:
        """
        Get all processes that have arrived by the current time.
        
        Args:
            current_time (int): Current simulation time
            
        Returns:
            List[Process]: List of arrived processes that haven't completed
        """
        return [p for p in self.processes 
                if (p.arrival_time <= current_time) and ( not p.is_completed() )]
                
    def calculate_metrics(self):
        """Calculate and return the average waiting time and turnaround time."""
        if not self.completed_processes:
            return 0, 0
            
        total_waiting_time = sum(p.waiting_time for p in self.completed_processes)
        total_turnaround_time = sum(p.turnaround_time for p in self.completed_processes)
        
        avg_waiting_time = total_waiting_time / len(self.completed_processes)
        avg_turnaround_time = total_turnaround_time / len(self.completed_processes)
        
        return avg_waiting_time, avg_turnaround_time
    
    def get_average_waiting_time(self):
        """Calculate and return the average waiting time."""
        completed = [p for p in self.processes if p.completion_time is not None]
        if not completed:
            return 0.0
        return sum(p.waiting_time for p in completed) / len(completed)
    
    def get_average_turnaround_time(self):
        """Calculate and return the average turnaround time."""
        completed = [p for p in self.processes if p.completion_time is not None]
        if not completed:
            return 0.0
        return sum(p.turnaround_time for p in completed) / len(completed)
    
    def get_average_response_time(self):
        """Calculate and return the average response time."""
        responded = [p for p in self.processes if p.response_time is not None]
        if not responded:
            return 0.0
        return sum(p.response_time for p in responded) / len(responded)
    
    @abstractmethod
    def get_next_process(self, current_time) -> Optional[Process]:
        """
        Get the next process to execute based on the scheduling algorithm.
        
        Args:
            current_time (int): Current simulation time
            
        Returns:
            Optional[Process]: The next process to execute, or None if no process is ready
        """
        pass
        
    def run_tick(self) -> Optional[Process]:
        """
        Run a single tick of the scheduler.
        
        Returns:
            Optional[Process]: The process that was executed in this tick, or None if idle
        """
        # Get the next process to execute
        next_process = self.get_next_process(self.current_time)
        
        # Define default value of time
        time_used = self.time_slice
        
        if next_process:
            # Execute the process for one time unit
            time_used = next_process.execute(self.current_time, self.time_slice)
            self.current_process = next_process
            
            # If the process has completed, add it to completed processes
            if next_process.is_completed() and next_process not in self.completed_processes:
                self.completed_processes.append(next_process)
        else:
            # CPU is idle
            self.current_process = None
            
        # Advance the time
        self.current_time += time_used
        
        return self.current_process