from abc import ABC, abstractmethod
from typing import List, Optional
from src.models.process import Process


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
        self.time_slice = 1  # Default time slice of 1 time unit
        self.processes: list[Process] = list()
        self.current_time = 0
        self.current_process: Optional[Process] = None
        self.completed_processes: list[Process] = list()

    def add_process(self, process: Process) -> None:
        """Add a process to the scheduler"""
        self.processes.append(process)

    def add_processes(self, processes: list[Process]) -> None:
        """Add multiple processes to the scheduler"""
        self.processes.extend(processes)

    def reset(self):
        """Reset only the scheduler state without resetting processes."""
        self.current_time = 0
        self.current_process = None
        self.completed_processes = list()

    def hard_reset(self):
        """
        Performs a complete reset of the scheduler and all processes.
        This method resets the scheduler to its initial state by calling the
        parent reset method, and additionally resets all processes managed
        by the scheduler to their initial states.
        """
        self.reset()
        for process in self.processes:
            process.reset()

    def get_current_time(self) -> int:
        """Get the current simulation time."""
        return self.current_time

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
        return [
            p
            for p in self.processes
            if (p.get_arrival_time() <= current_time) and (not p.is_completed())
        ]

    def get_average_waiting_time(self):
        """Calculate and return the average waiting time."""
        no_of_completed_processes = len(self.completed_processes)
        if no_of_completed_processes == 0:
            return 0.0

        total_waiting_time = sum(p.get_waiting_time() for p in self.completed_processes)
        return total_waiting_time / no_of_completed_processes

    def get_average_turnaround_time(self):
        """Calculate and return the average turnaround time."""
        no_of_completed_processes = len(self.completed_processes)
        if no_of_completed_processes == 0:
            return 0.0

        total_turnaround_time = sum(
            p.get_turnaround_time() for p in self.completed_processes
        )
        return total_turnaround_time / no_of_completed_processes

    def calculate_metrics(self):
        """Calculate and return the average waiting time and turnaround time."""
        return (self.get_average_waiting_time(), self.get_average_turnaround_time())

    def get_average_response_time(self):
        """Calculate and return the average response time."""
        responded = [p for p in self.processes if p.get_response_time() is not None]
        if not responded:
            return 0.0
        return sum(responded) / len(responded)

    def find_proccess_by_pid(self, pid: int) -> Optional[Process]:
        """
        Find a process by its PID.

        Args:
            pid (int): Process ID

        Returns:
            Optional[Process]: The process with the given PID, or None if not found
        """
        for process in self.processes:
            if process.get_pid() == pid:
                return process
        return None

    def remove_process(self, pid: int) -> None:
        """
        Remove a process by its PID.

        Args:
            pid (int): Process ID
        """
        process = self.find_proccess_by_pid(pid)
        if process in self.processes:
            self.processes.remove(process)
            if process in self.completed_processes:
                self.completed_processes.remove(process)

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

    def run_tick(self) -> Process:
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
            self.current_process = next_process
            time_used = self.current_process.execute(self.current_time, self.time_slice)

            # If the process has completed, add it to completed processes
            if (self.current_process.is_completed()):
                self.completed_processes.append(self.current_process)
        else:
            # CPU is idle
            self.current_process = None

        # Advance the time
        self.current_time += time_used
        
        return self.current_process
