import time
from typing import List, Dict, Tuple, Optional, Callable
from ..models.process import Process
from .scheduler import Scheduler

class Simulation:
    """
    Controls the CPU scheduling simulation.
    """
    
    def __init__(self, scheduler: Scheduler, delay: float = 1.0):
        """
        Initialize a new Simulation instance.
        
        Args:
            scheduler (Scheduler): The scheduler to use
            delay (float): Delay between ticks in seconds (default: 1.0)
        """
        self.scheduler = scheduler
        self.delay = delay
        self.running = False
        self.paused = False
        self.process_update_callback = None
        self.gantt_update_callback = None
        self.stats_update_callback = None
        self.current_time = 0
    
    def has_results(self):
        """
        Check if the simulation has any results that can be exported.
        
        Returns:
            bool: True if any processes have been completed, False otherwise
        """
        if not self.scheduler or not self.scheduler.processes:
            return False
            
        # Check if simulation has started processing any processes
        return self.scheduler.current_time > 0 or len(self.scheduler.completed_processes) > 0 or any(
            process.start_time is not None for process in self.scheduler.processes
        )
        
    def set_process_update_callback(self, callback: Callable[[List[Process], int], None]):
        """Set the callback function for updating process information."""
        self.process_update_callback = callback
        
    def set_gantt_update_callback(self, callback: Callable[[Optional[Process], int], None]):
        """Set the callback function for updating the Gantt chart."""
        self.gantt_update_callback = callback
        
    def set_stats_update_callback(self, callback: Callable[[float, float], None]):
        """Set the callback function for updating statistics."""
        self.stats_update_callback = callback
        
    def add_process(self, process: Process):
        """
        Add a process to the simulation.
        
        Args:
            process (Process): The process to add
        """
        self.scheduler.add_process(process)
        if self.process_update_callback:
            self.process_update_callback(self.scheduler.processes, self.scheduler.current_time)
            
    def remove_process(self, pid: int):
        """
        Remove a process from the simulation by its process ID.
        
        Args:
            pid (int): The process ID to remove
        """
        # Find the process with the given pid
        process_to_remove = None
        for process in self.scheduler.processes:
            if process.pid == pid:
                process_to_remove = process
                break
                
        if process_to_remove:
            # Remove from scheduler's processes list
            self.scheduler.processes.remove(process_to_remove)
            
            # Also remove from completed_processes if it's there
            if process_to_remove in self.scheduler.completed_processes:
                self.scheduler.completed_processes.remove(process_to_remove)
                
            # Update UI
            if self.process_update_callback:
                self.process_update_callback(self.scheduler.processes, self.scheduler.current_time)
                
            # Update statistics
            if self.stats_update_callback:
                avg_waiting, avg_turnaround = self.scheduler.calculate_metrics()
                self.stats_update_callback(avg_waiting, avg_turnaround)
                
    def remove_all_processes(self):
        """Remove all processes from the simulation."""
        self.scheduler.processes.clear()
        self.scheduler.completed_processes.clear()
        
        # Update UI
        if self.process_update_callback:
            self.process_update_callback([], self.scheduler.current_time)
            
        # Update statistics
        if self.stats_update_callback:
            self.stats_update_callback(0.0, 0.0)
            
    def reset(self):
        """Reset the simulation."""
        self.scheduler.reset()
        self.current_time = 0
        if self.process_update_callback:
            self.process_update_callback(self.scheduler.processes, self.scheduler.current_time)
        if self.gantt_update_callback:
            self.gantt_update_callback(None, self.scheduler.current_time)
        if self.stats_update_callback:
            avg_waiting, avg_turnaround = self.scheduler.calculate_metrics()
            self.stats_update_callback(avg_waiting, avg_turnaround)
            
    def reset_processes_progress(self):
        """Reset progress for all processes without removing them."""
        # Keep all processes but reset their progress
        for process in self.scheduler.processes:
            process.reset_progress()
            
        # Clear completed processes list but keep them in main processes list
        self.scheduler.completed_processes.clear()
        
    def reset_without_removing_processes(self):
        """Reset the simulation state without removing processes."""
        # Reset simulation time
        self.scheduler.current_time = 0
        self.current_time = 0
        
        # Reset scheduler state but keep processes
        self.scheduler.reset_state()
        
        # Update UI
        if self.process_update_callback:
            self.process_update_callback(self.scheduler.processes, self.scheduler.current_time)
        if self.gantt_update_callback:
            self.gantt_update_callback(None, self.scheduler.current_time)
        if self.stats_update_callback:
            # Reset statistics to zero since we're starting over
            self.stats_update_callback(0.0, 0.0)
            
    def start(self):
        """Start the simulation."""
        self.running = True
        self.paused = False
        self._run_simulation()
        
    def stop(self):
        """Stop the simulation."""
        self.running = False
        self.paused = False
        
    def pause(self):
        """Pause the simulation."""
        self.paused = True
        
    def resume(self):
        """Resume the simulation."""
        self.paused = False
        
    def run_all_at_once(self):
        """
        Run all processes without delay and display the final result.
        """
        # Reset the simulation state
        self.reset()
        
        # Run until all processes are completed
        while not self.scheduler.all_processes_completed():
            current_process = self.scheduler.run_tick()
            
            # Update Gantt chart with process execution
            if self.gantt_update_callback and current_process:
                self.gantt_update_callback(current_process, self.scheduler.current_time)
        
        # Update process table with final state
        if self.process_update_callback:
            self.process_update_callback(self.scheduler.processes, self.scheduler.current_time)
            
        # Update statistics
        if self.stats_update_callback:
            avg_waiting, avg_turnaround = self.scheduler.calculate_metrics()
            self.stats_update_callback(avg_waiting, avg_turnaround)
    
    def _run_simulation(self):
        """
        Run the simulation with a delay between each tick.
        """
        while self.running and not self.scheduler.all_processes_completed():
            if not self.paused:
                # Run a single tick
                current_process = self.scheduler.run_tick()
                
                # Update UI
                if self.process_update_callback:
                    self.process_update_callback(self.scheduler.processes, self.scheduler.current_time)
                    
                if self.gantt_update_callback:
                    self.gantt_update_callback(current_process, self.scheduler.current_time)
                    
                if self.stats_update_callback:
                    avg_waiting, avg_turnaround = self.scheduler.calculate_metrics()
                    self.stats_update_callback(avg_waiting, avg_turnaround)
                
                # Wait for the specified delay
                time.sleep(self.delay)
            else:
                # If paused, just sleep to avoid consuming CPU
                time.sleep(0.1)
                
        self.running = False