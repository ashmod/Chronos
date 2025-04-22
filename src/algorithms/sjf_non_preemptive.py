from src.core.scheduler import Scheduler
from src.models.process import Process
from typing import Optional, List


class SJFNonPreemptiveScheduler(Scheduler):
    """
    Shortest Job First (SJF) Non-Preemptive scheduling algorithm.
    Processes are executed based on the shortest burst time.
    Once a process starts executing, it runs to completion.
    """

    def __init__(self):
        super().__init__("Shortest Job First (Non-Preemptive)")
        self.current_running_process = None

    def get_next_process(self, current_time) -> Optional[Process]:
        """
        Get the next process to execute based on SJF Non-Preemptive scheduling.

        Args:
            current_time (int): Current simulation time

        Returns:
            Optional[Process]: The next process to execute, or None if no process is ready
        """
        # If a process is currently running, continue with it
        if (
            self.current_running_process
            and not self.current_running_process.is_completed()
        ):
            return self.current_running_process

        # Get all processes that have arrived and haven't completed
        ready_processes = self.get_arrived_processes(current_time)

        if not ready_processes:
            self.current_running_process = None
            return None

        # In SJF, we sort by burst time (shortest first)
        # If there are processes with the same burst time, we sort by arrival time
        # If arrival times are also the same, we sort by PID
        self.current_running_process = sorted(
            ready_processes, key=lambda p: (p.burst_time, p.arrival_time, p.pid)
        )[0]

        return self.current_running_process
