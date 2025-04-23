from src.core.scheduler import Scheduler
from src.models.process import Process
from typing import Optional, List


class PriorityPreemptiveScheduler(Scheduler):
    """
    Priority Preemptive scheduling algorithm.
    At any point, the process with the highest priority (lowest priority number) gets the CPU.
    """

    def __init__(self):
        super().__init__("Priority (Preemptive)")

    def get_next_process(self, current_time) -> Optional[Process]:
        """
        Get the next process to execute based on Priority Preemptive scheduling.

        Args:
            current_time (int): Current simulation time

        Returns:
            Optional[Process]: The next process to execute, or None if no process is ready
        """
        # Get all processes that have arrived and haven't completed
        ready_processes = self.get_arrived_processes(current_time)

        if not ready_processes:
            return None

        # In Priority Preemptive scheduling, we sort by priority (lower value = higher priority)
        # If there are processes with the same priority, we sort by arrival time
        # If arrival times are also the same, we sort by PID
        return sorted(
            ready_processes, key=lambda p: (p.get_priority(), p.get_arrival_time(), p.get_pid())
        )[0]
