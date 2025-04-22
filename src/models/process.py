from src.models.execution import Execution
from typing import Optional


class Process:
    """
    Represents a process in the CPU scheduler simulation.
    """

    def __init__(
        self, pid: int, name: str, arrival_time: int, burst_time: int, priority=None
    ):
        """
        Initialize a new Process instance.

        Args:
            pid (int): Process ID
            name (str): Process name
            arrival_time (int): The time when the process arrives
            burst_time (int): The total CPU time needed by the process
            priority (int, optional): Priority of the process (smaller value means higher priority)
        """
        self.__pid: int = pid
        self.__name: str = name
        self.__arrival_time: int = arrival_time
        self.__burst_time: int = burst_time
        self.__priority: Optional[int] = priority
        self.__remaining_time: int = burst_time
        self.__start_time: int = None
        self.__completion_time: int = None
        self.__waiting_time: int = 0
        self.__turnaround_time: int = 0
        self.__response_time: int = None
        self.__execution_history: list[Execution] = list()

    def reset(self):
        """Reset the process state for a new simulation."""
        # Explicitly reset each runtime state attribute
        self.__remaining_time = self.__burst_time
        self.__start_time = None
        self.__completion_time = None
        self.__waiting_time = 0
        self.__turnaround_time = 0
        self.__response_time = None
        self.__execution_history = list()

    def is_completed(self):
        """Check if the process has completed execution."""
        return self.__remaining_time <= 0

    def calculate_turnaround_time(self):
        """Calculate and set the turnaround time."""
        if self.__completion_time is not None:
            self.__turnaround_time = self.__completion_time - self.__arrival_time

    def calculate_waiting_time(self):
        """Calculate and set the waiting time."""
        if self.__turnaround_time:
            self.__waiting_time = self.__turnaround_time - self.__burst_time

    def execute(self, current_time: int, time_quantum: int = 1) -> int:
        """
        Execute the process for the given time quantum.

        Args:
            current_time (int): Current simulation time
            time_quantum (int): Amount of time to execute

        Returns:
            int: The amount of time actually used (may be less than time_quantum if process completes)
        """
        if self.__start_time is None:
            self.__start_time = current_time

        # Track the first time this process runs (for response time)
        if not self.__response_time:
            self.__response_time = current_time - self.__arrival_time

        execution_time = min(self.__remaining_time, time_quantum)
        self.__remaining_time -= execution_time

        # Record this execution period
        self.__execution_history.append(
            Execution(start_time=current_time, end_time=current_time + execution_time)
        )

        if self.is_completed():
            self.__completion_time = current_time + execution_time
            self.calculate_turnaround_time()
            self.calculate_waiting_time()

        return execution_time

    def clone(self):
        """Create a clone of this process."""
        return Process(
            pid=self.__pid,
            name=self.__name,
            arrival_time=self.__arrival_time,
            burst_time=self.__burst_time,
            priority=self.__priority,
        )

    def get_pid(self) -> int:
        return self.__pid

    def get_arrival_time(self) -> int:
        return self.__arrival_time

    def get_waiting_time(self) -> int:
        return self.__waiting_time

    def get_turnaround_time(self) -> int:
        return self.__turnaround_time

    def get_response_time(self) -> int:
        return self.__response_time

    def get_execution_history(self) -> list[Execution]:
        return self.__execution_history

    def __str__(self):
        """String representation of the process."""
        status = (
            "COMPLETED"
            if self.is_completed()
            else f"RUNNING ({self.__remaining_time}/{self.__burst_time})"
        )

        # Format the output on multiple lines
        output = [
            f"Process {self.__pid} ({self.__name}):",
            f"  Status: {status}",
            f"  Arrival time: {self.__arrival_time}",
            f"  Burst time: {self.__burst_time}",
            f"  Priority: {self.__priority}",
        ]

        # Add metrics when available
        if self.__waiting_time > 0:
            output.append(f"  Waiting time: {self.__waiting_time}")
        if self.__turnaround_time > 0:
            output.append(f"  Turnaround time: {self.__turnaround_time}")
        if self.__response_time is not None:
            output.append(f"  Response time: {self.__response_time}")

        return "\n".join(output)
