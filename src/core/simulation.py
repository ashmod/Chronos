import time
from src.models.process import Process
from src.core.scheduler import Scheduler
import threading


class Simulation:
    def __init__(self, scheduler: Scheduler, delay: float = 1.0):
        self.scheduler = scheduler
        self.delay = delay
        self.running = False
        self.paused = False

    def add_process(self, process: Process):
        self.scheduler.add_process(process)

    def add_live_process(
        self, name: str, burst_time: int, priority: int, pid: int
    ) -> Process:

        # Get the current simulation time
        current_time = self.scheduler.get_current_time()

        # Create a new process with arrival time set to current simulation time
        process = Process(
            pid=pid,
            name=name,
            arrival_time=current_time,
            burst_time=burst_time,
            priority=priority,
        )
        self.add_process(process)

        return process

    def remove_process(self, pid: int):
        # Find the process with the given pid
        self.scheduler.remove_process(pid)

    def reset(self):
        """Reset the simulation."""
        self.scheduler.hard_reset()

    def is_running(self) -> bool:
        """Check if the simulation is running."""
        return self.running

    def start(self):
        self.running = True
        self.paused = False

    def is_paused(self) -> bool:
        """Check if the simulation is paused."""
        return self.paused

    def set_paused(self, paused: bool):
        """Set the simulation to paused or unpaused."""
        self.paused = paused

    def set_speed(self, speed_factor: int):
        if speed_factor <= 0:
            self.delay = 0.001  # Minimum delay to prevent division by zero
        else:
            self.delay = 1.0 / speed_factor


    def _run_simulation(self, useDelay: bool = True):
        """
        Run the simulation with a delay between each tick.
        """
        while (self.running) and (not self.scheduler.all_processes_completed()):

            current_process = self.scheduler.run_tick()

            # Wait for the specified delay
            if useDelay:
                time.sleep(self.delay)
            
            yield current_process
                
        self.running = False
        return self.running

    def get_cpu_utilization(self) -> float:
        raise NotImplementedError("CPU utilization calculation is not implemented.")

    def get_throughput(self) -> float:
        raise NotImplementedError("Throughput calculation is not implemented.")

    def has_results(self) -> bool:
        return self.scheduler.all_processes_completed()