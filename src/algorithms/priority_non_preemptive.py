from ..core.scheduler import Scheduler
from ..models.process import Process
from typing import Optional, List

class PriorityNonPreemptiveScheduler(Scheduler):
    """
    Priority Non-Preemptive scheduling algorithm.
    Processes are executed based on priority (lower value = higher priority).
    Once a process starts executing, it runs to completion.
    """
    
    def __init__(self):
        super().__init__("Priority (Non-Preemptive)")
        self.current_running_process = None
    
    def get_next_process(self, current_time) -> Optional[Process]:
        """
        Get the next process to execute based on Priority Non-Preemptive scheduling.
        
        Args:
            current_time (int): Current simulation time
            
        Returns:
            Optional[Process]: The next process to execute, or None if no process is ready
        """
        # If a process is currently running, continue with it
        if self.current_running_process and not self.current_running_process.is_completed():
            return self.current_running_process
            
        # Get all processes that have arrived and haven't completed
        ready_processes = self.get_arrived_processes(current_time)
        
        if not ready_processes:
            self.current_running_process = None
            return None
            
        # In Priority scheduling, we sort by priority (lower value = higher priority)
        # If there are processes with the same priority, we sort by arrival time
        # If arrival times are also the same, we sort by PID
        self.current_running_process = sorted(
            ready_processes, 
            key=lambda p: (p.priority, p.arrival_time, p.pid)
        )[0]
        
        return self.current_running_process