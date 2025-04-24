from src.core.scheduler import Scheduler
from src.models.process import Process
from typing import Optional, List
from collections import deque


class RoundRobinScheduler(Scheduler):
    """
    Round Robin scheduling algorithm.
    Each process is given a fixed time slice (quantum) to execute.
    Processes are executed in a circular queue.
    """

    def __init__(self, time_quantum: int = 2):
        """
        Initialize a new RoundRobinScheduler instance.

        Args:
            time_quantum (int): The time quantum for each process (default: 2)
        """
        super().__init__("Round Robin")
        self.TIME_QUANTUM = time_quantum  # constant for time quantum
        self.ready_queue = deque()
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
        # Call the parent's reset method instead of hard_reset to avoid recursion
        super().reset()
        for process in self.processes:
            process.reset()
        self.ready_queue = deque()
        self.current_quantum_used = 0

    def get_next_process(self, current_time) -> Optional[Process]:
        """
        Get the next process to execute based on Round Robin scheduling.

        Args:
            current_time (int): Current simulation time

        Returns:
            Optional[Process]: The next process to execute, or None if no process is ready
        """
        for process in self.get_arrived_processes(current_time):
            if (process not in self.ready_queue) and (process != self.current_process):
                self.ready_queue.append(process)

        if self.current_process:
            if self.current_process.is_completed():
                # Add to completed processes before setting to None
                self.completed_processes.append(self.current_process)
                self.current_process = None
                self.current_quantum_used = 0
            elif self.current_quantum_used == self.TIME_QUANTUM:
                self.ready_queue.append(self.current_process)
                self.current_process = None
                self.current_quantum_used = 0

        if (not self.current_process) and (len(self.ready_queue) > 0):
            self.current_process = self.ready_queue.popleft()
            self.current_quantum_used = 0
        return self.current_process

    def run_tick(self) -> Process:
        """
        Override the run_tick method to properly handle quantum time tracking.

        Returns:
            Optional[Process]: The process that was executed in this tick, or None if idle
        """
        self.get_next_process(self.current_time)

        time_used = self.time_slice
        if self.current_process:
            time_used = self.current_process.execute(self.current_time, self.time_slice)
            self.current_quantum_used += time_used

        self.current_time += time_used

        return self.current_process
