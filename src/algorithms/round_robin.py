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
        self.time_slice = 1  # Set time slice to 1 to control execution more precisely
        self.ready_queue = deque()
        self.current_process = None
        self.current_quantum_used = 0  # Track how much of the quantum has been used
    
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
        self.current_quantum_used = 0
        
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
        
        # Add newly arrived processes to the ready queue
        for process in arrived_processes:
            if process not in self.ready_queue and process != self.current_process:
                self.ready_queue.append(process)
                
        # If we have a current process, check if it should continue running
        if self.current_process:
            # Check if the process has completed
            if self.current_process.is_completed():
                self.current_process = None
                self.current_quantum_used = 0
            # Check if the quantum has expired
            elif self.current_quantum_used >= self.time_quantum:
                # Move the process to the back of the queue if not completed
                self.ready_queue.append(self.current_process)
                self.current_process = None
                self.current_quantum_used = 0
                
        # If there's no current process but we have processes in the queue, get the next one
        if not self.current_process and self.ready_queue:
            self.current_process = self.ready_queue.popleft()
            self.current_quantum_used = 0
            # Record the first execution if not already set
            if self.current_process.start_time is None:
                self.current_process.start_time = current_time
                
        # If we have a current process, increment the quantum counter
        if self.current_process:
            self.current_quantum_used += 1
            
        return self.current_process

    def run_tick(self) -> Optional[Process]:
        """
        Run a single tick of the simulation.
        
        Returns:
            Optional[Process]: The process that was executed in this tick, or None if CPU was idle
        """
        # Get the next process to execute
        process = self.get_next_process(self.current_time)
        
        # If there is a process to execute
        if process:
            # Execute the process for one time unit, passing the current time as required
            process.execute(self.current_time)
            
            # If the process has completed
            if process.is_completed():
                process.completion_time = self.current_time + 1
                process.turnaround_time = process.completion_time - process.arrival_time
                process.waiting_time = process.turnaround_time - process.burst_time
                self.completed_processes.append(process)
                
        # Increment current time
        self.current_time += 1
        
        return process