import time
import threading
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
            
    def add_live_process(self, name: str, burst_time: int, priority: int, pid: int) -> Process:
        """
        Add a process during simulation execution with arrival time set to current time.
        
        Args:
            name (str): Name of the process
            burst_time (int): Burst time of the process
            priority (int): Priority of the process
            pid (int): Process ID
        
        Returns:
            Process: The newly created and added process
        """
        # Get the current simulation time
        current_time = self.scheduler.current_time
        
        # Create a new process with arrival time set to current simulation time
        process = Process(
            pid=pid,
            name=name,
            arrival_time=current_time,
            burst_time=burst_time,
            priority=priority
        )
        
        # Add the process to the scheduler
        self.scheduler.add_process(process)
        
        # Update the UI if callback is provided
        if self.process_update_callback:
            self.process_update_callback(self.scheduler.processes, current_time)
            
        return process
            
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
        self.scheduler.reset_state()
        
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
        # Run the simulation in a new thread to avoid blocking the UI
        simulation_thread = threading.Thread(target=self._run_simulation)
        simulation_thread.daemon = True
        simulation_thread.start()
        
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
            #else:
                # If paused, just sleep to avoid consuming CPU
                #time.sleep(0.1)
                
        self.running = False
        
    def set_speed(self, speed_factor: int):
        """
        Set the simulation speed based on a multiplier.
        
        Args:
            speed_factor (int): Speed multiplier, higher values mean faster simulation
        """
        if speed_factor <= 0:
            self.delay = 0.001  # Minimum delay to prevent division by zero
        else:
            self.delay = 1.0 / speed_factor
            
    def get_cpu_utilization(self) -> float:
        """
        Calculate CPU utilization as the percentage of time the CPU was busy (not idle).
        
        Returns:
            float: CPU utilization as a decimal (0.0 to 1.0)
        """
        if not self.scheduler or not self.scheduler.processes:
            return 0.0
            
        # Find the last completion time
        last_completion = 0
        for process in self.scheduler.processes:
            if process.completion_time is not None and process.completion_time > last_completion:
                last_completion = process.completion_time
                
        if last_completion == 0:
            return 0.0
            
        # Calculate total busy time from all process execution periods
        total_busy_time = 0
        for process in self.scheduler.processes:
            for start, end in process.execution_history:
                total_busy_time += (end - start)
                
        # CPU utilization = busy time / total simulation time
        return min(total_busy_time / last_completion, 1.0)  # Cap at 100%
        
    def get_throughput(self) -> float:
        """
        Calculate throughput as the number of processes completed per unit of time.
        
        Returns:
            float: Throughput (processes per unit time)
        """
        if not self.scheduler or not self.scheduler.processes:
            return 0.0
            
        # Count completed processes
        completed_count = 0
        last_completion = 0
        
        for process in self.scheduler.processes:
            if process.completion_time is not None:
                completed_count += 1
                if process.completion_time > last_completion:
                    last_completion = process.completion_time
                    
        if last_completion == 0 or completed_count == 0:
            return 0.0
            
        # Throughput = number of processes completed / total time
        return completed_count / last_completion
        
    def get_timeline_entries(self):
        """
        Get a list of timeline entries for the Gantt chart.
        
        Returns:
            list: List of tuples (process, start_time, end_time)
        """
        entries = []
        
        if not self.scheduler or not self.scheduler.processes:
            return entries
            
        for process in self.scheduler.processes:
            for start, end in process.execution_history:
                entries.append((process, start, end))
                
        # Sort by start time
        entries.sort(key=lambda x: x[1])
        
        return entries