from src.core.scheduler import Scheduler
from src.models.process import Process
from typing import Optional


class SJFPreemptiveScheduler(Scheduler):
    """
    Shortest Job First (SJF) Preemptive scheduling algorithm, also known as Shortest Remaining Time First (SRTF).
    At any point, the process with the shortest remaining time gets the CPU.
    """

    def __init__(self):
        super().__init__("Shortest Job First (Preemptive)")

    def get_next_process(self, current_time) -> Optional[Process]:
        """
        Get the next process to execute based on SJF Preemptive scheduling.

        Args:
            current_time (int): Current simulation time

        Returns:
            Optional[Process]: The next process to execute, or None if no process is ready
        """
        # Get all processes that have arrived and haven't completed
        ready_processes = self.get_arrived_processes(current_time)

        if not ready_processes:
            return None

        # In SJF Preemptive (SRTF), we sort by remaining time (shortest first)
        # If there are processes with the same remaining time, we sort by arrival time
        # If arrival times are also the same, we sort by PID
        return sorted(
            ready_processes, key=lambda p: (p.get_remaining_time(), p.get_arrival_time(), p.get_pid())
        )[0]
