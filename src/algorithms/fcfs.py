from src.core.scheduler import Scheduler
from src.models.process import Process
from typing import Optional, List


class FCFSScheduler(Scheduler):
    """
    First-Come, First-Served (FCFS) scheduling algorithm.
    Processes are executed in the order they arrive.
    """

    def __init__(self):
        super().__init__("First-Come, First-Served (FCFS)")

    def get_next_process(self, current_time) -> Optional[Process]:
        """
        Get the next process to execute based on FCFS scheduling.

        Args:
            current_time (int): Current simulation time

        Returns:
            Optional[Process]: The next process to execute, or None if no process is ready
        """
        # Get all processes that have arrived and haven't completed
        ready_processes = self.get_arrived_processes(current_time)

        if not ready_processes:
            return None

        # In FCFS, we sort by arrival time (earliest first)
        # If there are processes with the same arrival time, we sort by PID
        return sorted(
            ready_processes, key=lambda p: (p.get_arrival_time(), p.get_pid())
        )[0]
