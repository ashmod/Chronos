import time
import threading
from typing import List, Optional, Callable, Literal
from ..models.process import Process
from .scheduler import Scheduler

class Simulation:
    def __init__(self, scheduler: Scheduler, delay: float = 1.0):
        self.scheduler = scheduler
        self.delay = delay
        self.running = False
        self.paused = False

        # # Callback hooks
        # self.process_update_callback: Optional[Callable[[List[Process], int], None]] = None
        # self.gantt_update_callback: Optional[Callable[[Optional[Process], int], None]] = None
        # self.stats_update_callback: Optional[Callable[[float, float], None]] = None

        # # Optional event log (tick-based)
        # self.event_log: List[str] = []

    # def set_process_update_callback(self, callback: Callable[[List[Process], int], None]):
    #     self.process_update_callback = callback

    # def set_gantt_update_callback(self, callback: Callable[[Optional[Process], int], None]):
    #     self.gantt_update_callback = callback

    # def set_stats_update_callback(self, callback: Callable[[float, float], None]):
    #     self.stats_update_callback = callback

    # def _trigger_ui_updates(self, current_process: Optional[Process] = None):
    #     if self.process_update_callback:
    #         self.process_update_callback(self.scheduler.processes, self.scheduler.current_time)
    #     if self.gantt_update_callback:
    #         self.gantt_update_callback(current_process, self.scheduler.current_time)
    #     if self.stats_update_callback:
    #         avg_waiting, avg_turnaround = self.scheduler.calculate_metrics()
    #         self.stats_update_callback(avg_waiting, avg_turnaround)

    def _tick_once(self):
        current_process = self.scheduler.run_tick()
        # self._trigger_ui_updates(current_process)
        # self.event_log.append(f"[Time {self.scheduler.current_time}] Ran: {current_process.name if current_process else 'IDLE'}")

    def add_process(self, process: Process):
        self.scheduler.add_process(process)
        # self._trigger_ui_updates()

    def add_live_process(self, name: str, burst_time: int, priority: int, pid: int) -> Process:
        process = Process(
            pid=pid,
            name=name,
            arrival_time=self.scheduler.current_time,
            burst_time=burst_time,
            priority=priority
        )
        self.scheduler.add_process(process)
        # self._trigger_ui_updates()
        return process

    def remove_process(self, pid: int):
        self.scheduler.remove_process(pid)
        # self._trigger_ui_updates()

    def remove_all_processes(self):
        self.scheduler.processes.clear()
        self.scheduler.reset_state()
        # self._trigger_ui_updates()

    def reset(self, mode: Literal["full", "soft", "progress_only"] = "full"):
        """
        Reset the simulation based on the selected mode:
        - "full": Remove all processes and reset everything
        - "soft": Keep processes, reset simulation state
        - "progress_only": Only reset process progress
        """
        if mode == "full":
            self.scheduler.processes.clear()
            self.scheduler.reset_state()
        elif mode == "soft":
            self.scheduler.reset_state()
        elif mode == "progress_only":
            for process in self.scheduler.processes:
                process.reset()
            self.scheduler.completed_processes.clear()

        # self._trigger_ui_updates()

    def start(self):
        self.running = True
        self.paused = False
        threading.Thread(target=self._run_simulation, daemon=True).start()

    # def stop(self):
    #     self.running = False
    #     self.paused = False

    def pause(self):
        self.running = False
        self.paused = True

    def resume(self):
        self.paused = False
        self.running = True

    def _run_simulation(self):
        while self.running and not self.scheduler.all_processes_completed():
            if not self.paused:
                self._tick_once()
                time.sleep(self.delay)
            else:
                time.sleep(0.05)
        self.running = False

    def run_all_at_once(self):
        self.reset(mode="soft")
        while not self.scheduler.all_processes_completed():
            self._tick_once()

    # def set_speed(self, speed_factor: int):
    #     self.delay = 1.0 / max(speed_factor, 1)

    # def get_cpu_utilization(self) -> float:
    #     last_completion = max((p.completion_time or 0 for p in self.scheduler.processes), default=0)
    #     if last_completion == 0:
    #         return 0.0
    #     total_busy = sum((end - start) for p in self.scheduler.processes for start, end in p.execution_history)
    #     return min(total_busy / last_completion, 1.0)

    # def get_throughput(self) -> float:
    #     completed = [p for p in self.scheduler.processes if p.completion_time is not None]
    #     if not completed:
    #         return 0.0
    #     last_time = max(p.completion_time for p in completed)
    #     return len(completed) / last_time if last_time else 0.0

    def get_timeline_entries(self):
        entries = [(p, start, end) for p in self.scheduler.processes for start, end in p.execution_history]
        return sorted(entries, key=lambda x: x[1])

    # def has_results(self) -> bool:
    #     return (
    #         self.scheduler.current_time > 0 or
    #         len(self.scheduler.completed_processes) > 0 or
    #         any(p.start_time is not None for p in self.scheduler.processes)
    #     )
