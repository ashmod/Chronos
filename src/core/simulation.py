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
            arrival_time=self.scheduler.current_time,
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

    def start(self):
        self.running = True
        self.paused = False
        simulation_thread = threading.Thread(target=self._run_simulation)
        simulation_thread.daemon = True
        simulation_thread.start()

    def stop(self):
        """Stop the simulation."""
        self.running = False
        self.paused = False

    def pause(self):
        self.running = False
        self.paused = True

    def resume(self):
        self.paused = False

    def set_speed(self, speed_factor: int):
        if speed_factor <= 0:
            self.delay = 0.001  # Minimum delay to prevent division by zero
        else:
            self.delay = 1.0 / speed_factor

    def run_all_at_once(self):
        """
        Run all processes without delay and display the final result.
        """
        # Reset the simulation state
        self.reset()

        # Run until all processes are completed
        while not self.scheduler.all_processes_completed():
            self.scheduler.run_tick()

    def _run_simulation(self):
        """
        Run the simulation with a delay between each tick.
        """
        while (self.running) and (not self.scheduler.all_processes_completed()):
            if not self.paused:
                # Run a single tick
                self.scheduler.run_tick()

                # Wait for the specified delay
                time.sleep(self.delay)
        self.running = False

    def get_cpu_utilization(self) -> float:
        raise NotImplementedError("CPU utilization calculation is not implemented.")

    def get_throughput(self) -> float:
        raise NotImplementedError("Throughput calculation is not implemented.")

    def has_results(self) -> bool:
        return self.scheduler.all_processes_completed()

    def get_timeline_entries(self):
        entries = []

        if (not self.scheduler) or (not self.scheduler.processes):
            return entries

        for process in self.scheduler.processes:
            for execution in process.get_execution_history():
                start, end = execution.get_start_time(), execution.get_end_time()
                entries.append((process, start, end))

        # Sort by start time
        entries.sort(key=lambda x: x[1])

        return entries
