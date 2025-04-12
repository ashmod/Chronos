"""
Dummy CPU Scheduler with GUI and Live Simulation Enhancements

This file is a template for the CPU Scheduler project. It contains placeholders for:
- Live scheduler running every 1 unit (1 second) and updating the simulation.
- Dynamic process addition.
- Two modes: Live simulation and non-live (batch run) simulation.
- Live-updating Gantt Chart (graphical timeline of process execution).
- Live-updated table for remaining burst times.
- Calculation and display of average waiting time and turnaround time.
- Placeholders for six scheduling algorithms:
    1. FCFS Scheduler
    2. SJF Preemptive Scheduler
    3. SJF Non-Preemptive Scheduler
    4. Priority Preemptive Scheduler
    5. Priority Non-Preemptive Scheduler
    6. Round Robin Scheduler
"""

import tkinter as tk
from tkinter import ttk
import time

#####################################
# Process Data Model
#####################################

class Process:
    def __init__(self, pid, arrival_time, burst_time, priority=None):
        self.pid = pid
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.remaining_time = burst_time  # For preemptive scheduling
        self.priority = priority
        # These will be computed during simulation:
        self.start_time = None
        self.completion_time = None
        self.waiting_time = None
        self.turnaround_time = None

    def update(self, time_unit=1):
        """Update the process's remaining time."""
        if self.remaining_time > 0:
            self.remaining_time -= time_unit
            if self.remaining_time < 0:
                self.remaining_time = 0

    def is_completed(self):
        """Return True if the process has finished executing."""
        return self.remaining_time == 0

    def __str__(self):
        return (f"PID: {self.pid}, Arrival: {self.arrival_time}, "
                f"Burst: {self.burst_time}, Remaining: {self.remaining_time}, "
                f"Priority: {self.priority}")

#####################################
# Scheduler Algorithm Placeholders
#####################################

def fcfs_scheduler(processes, current_time):
    """
    First-Come, First-Served Scheduler.
    Placeholder: Implement actual FCFS logic here.
    
    Returns:
        schedule (list): List of tuples (pid, start_time, end_time).
    """
    print("Executing FCFS Scheduler (Placeholder)...")
    # TODO: Replace with actual FCFS scheduling logic
    schedule = [(p.pid, p.arrival_time, p.arrival_time + p.burst_time) for p in sorted(processes, key=lambda x: x.arrival_time)]
    return schedule

def sjf_preemptive_scheduler(processes, current_time):
    """
    Shortest Job First Preemptive Scheduler.
    Placeholder: Implement actual SJF preemptive logic here.
    """
    print("Executing SJF Preemptive Scheduler (Placeholder)...")
    # TODO: Implement SJF preemptive scheduling logic
    schedule = []
    return schedule

def sjf_non_preemptive_scheduler(processes, current_time):
    """
    Shortest Job First Non-Preemptive Scheduler.
    Placeholder: Implement actual SJF non-preemptive logic here.
    """
    print("Executing SJF Non-Preemptive Scheduler (Placeholder)...")
    # TODO: Implement SJF non-preemptive scheduling logic
    schedule = []
    return schedule

def priority_preemptive_scheduler(processes, current_time):
    """
    Priority Preemptive Scheduler.
    Placeholder: Implement actual priority preemptive logic here.
    (Lower value means higher priority)
    """
    print("Executing Priority Preemptive Scheduler (Placeholder)...")
    # TODO: Implement Priority preemptive scheduling logic
    schedule = []
    return schedule

def priority_non_preemptive_scheduler(processes, current_time):
    """
    Priority Non-Preemptive Scheduler.
    Placeholder: Implement actual priority non-preemptive logic here.
    """
    print("Executing Priority Non-Preemptive Scheduler (Placeholder)...")
    # TODO: Implement Priority non-preemptive scheduling logic
    schedule = []
    return schedule

def round_robin_scheduler(processes, quantum, current_time):
    """
    Round Robin Scheduler.
    Placeholder: Implement actual round robin logic here.
    
    Args:
        quantum (int): Time quantum.
    """
    print("Executing Round Robin Scheduler (Placeholder)...")
    # TODO: Implement Round Robin scheduling logic
    schedule = []
    return schedule

#####################################
# Simulation Calculation Functions
#####################################

def calculate_statistics(processes):
    """
    Calculate average waiting time and turnaround time.
    Placeholder: Compute these values after simulation is complete.
    
    Returns:
        avg_waiting (float), avg_turnaround (float)
    """
    # TODO: Implement actual statistics calculations
    total_waiting = sum(p.waiting_time for p in processes if p.waiting_time is not None)
    total_turnaround = sum(p.turnaround_time for p in processes if p.turnaround_time is not None)
    n = len(processes)
    avg_waiting = total_waiting / n if n > 0 else 0
    avg_turnaround = total_turnaround / n if n > 0 else 0
    return avg_waiting, avg_turnaround

#####################################
# GUI Application with Live Simulation
#####################################

class SchedulerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CPU Scheduler GUI")
        self.geometry("900x700")
        
        # Global simulation variables
        self.processes = []         # List of Process objects
        self.simulation_time = 0    # Current time unit in the simulation
        self.live_running = False   # Flag to indicate if live simulation is on
        
        self.selected_scheduler = tk.StringVar(value="FCFS")
        self.simulation_mode = tk.StringVar(value="live")  # Options: "live" or "non-live"
        
        self.create_widgets()

    def create_widgets(self):
        # --- Process Addition Frame ---
        add_frame = ttk.Frame(self)
        add_frame.pack(pady=10, padx=10, fill=tk.X)
        
        ttk.Label(add_frame, text="Process ID:").pack(side=tk.LEFT, padx=5)
        self.entry_pid = ttk.Entry(add_frame, width=8)
        self.entry_pid.pack(side=tk.LEFT)
        
        ttk.Label(add_frame, text="Arrival Time:").pack(side=tk.LEFT, padx=5)
        self.entry_arrival = ttk.Entry(add_frame, width=8)
        self.entry_arrival.pack(side=tk.LEFT)
        
        ttk.Label(add_frame, text="Burst Time:").pack(side=tk.LEFT, padx=5)
        self.entry_burst = ttk.Entry(add_frame, width=8)
        self.entry_burst.pack(side=tk.LEFT)
        
        ttk.Label(add_frame, text="Priority (Optional):").pack(side=tk.LEFT, padx=5)
        self.entry_priority = ttk.Entry(add_frame, width=8)
        self.entry_priority.pack(side=tk.LEFT)
        
        add_button = ttk.Button(add_frame, text="Add Process", command=self.add_process)
        add_button.pack(side=tk.LEFT, padx=10)
        
        # --- Scheduler & Mode Selection Frame ---
        options_frame = ttk.Frame(self)
        options_frame.pack(pady=10, padx=10, fill=tk.X)
        
        ttk.Label(options_frame, text="Scheduler:").pack(side=tk.LEFT, padx=5)
        scheduler_options = [
            "FCFS", 
            "SJF Preemptive", 
            "SJF Non-Preemptive", 
            "Priority Preemptive", 
            "Priority Non-Preemptive", 
            "Round Robin"
        ]
        self.scheduler_menu = ttk.OptionMenu(options_frame, self.selected_scheduler, scheduler_options[0], *scheduler_options)
        self.scheduler_menu.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(options_frame, text="Quantum (for RR):").pack(side=tk.LEFT, padx=5)
        self.entry_quantum = ttk.Entry(options_frame, width=5)
        self.entry_quantum.pack(side=tk.LEFT, padx=5)
        self.entry_quantum.insert(0, "2")
        
        # Radio buttons for simulation mode
        ttk.Label(options_frame, text="Mode:").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(options_frame, text="Live", variable=self.simulation_mode, value="live").pack(side=tk.LEFT)
        ttk.Radiobutton(options_frame, text="Non-Live", variable=self.simulation_mode, value="non-live").pack(side=tk.LEFT)
        
        # --- Action Buttons ---
        action_frame = ttk.Frame(self)
        action_frame.pack(pady=10, padx=10)
        
        self.start_button = ttk.Button(action_frame, text="Start Simulation", command=self.start_simulation)
        self.start_button.pack(side=tk.LEFT, padx=10)
        
        self.stop_button = ttk.Button(action_frame, text="Stop Simulation", command=self.stop_simulation, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=10)
        
        # --- Gantt Chart Display (Placeholder using Text widget) ---
        gantt_frame = ttk.LabelFrame(self, text="Gantt Chart (Timeline)")
        gantt_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        self.gantt_text = tk.Text(gantt_frame, height=10)
        self.gantt_text.pack(fill=tk.BOTH, expand=True)
        
        # --- Remaining Burst Time Table (Using Treeview) ---
        table_frame = ttk.LabelFrame(self, text="Remaining Burst Time Table")
        table_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        self.tree = ttk.Treeview(table_frame, columns=("PID", "Arrival", "Burst", "Remaining", "Priority"), show="headings")
        self.tree.heading("PID", text="PID")
        self.tree.heading("Arrival", text="Arrival")
        self.tree.heading("Burst", text="Burst")
        self.tree.heading("Remaining", text="Remaining")
        self.tree.heading("Priority", text="Priority")
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # --- Statistics Display ---
        stats_frame = ttk.LabelFrame(self, text="Statistics")
        stats_frame.pack(pady=10, padx=10, fill=tk.X)
        self.stats_label = ttk.Label(stats_frame, text="Avg Waiting Time: N/A | Avg Turnaround Time: N/A")
        self.stats_label.pack(padx=10, pady=5)

    def add_process(self):
        """Read input fields and add a process to the simulation list."""
        try:
            pid = self.entry_pid.get().strip()
            arrival = int(self.entry_arrival.get().strip())
            burst = int(self.entry_burst.get().strip())
            priority_val = self.entry_priority.get().strip()
            priority = int(priority_val) if priority_val else None
            
            new_proc = Process(pid, arrival, burst, priority)
            self.processes.append(new_proc)
            self.update_process_table()
            self.gantt_text.insert(tk.END, f"Added {new_proc}\n")
        except ValueError:
            self.gantt_text.insert(tk.END, "Error: Please enter valid numeric values for Arrival, Burst, and Priority.\n")

    def update_process_table(self):
        """Refresh the live-updating table showing each process's remaining burst time."""
        # Clear the existing table
        for row in self.tree.get_children():
            self.tree.delete(row)
        # Insert updated process info
        for proc in self.processes:
            self.tree.insert("", tk.END, values=(proc.pid, proc.arrival_time, proc.burst_time, proc.remaining_time, proc.priority))

    def start_simulation(self):
        """Start the simulation in either live or non-live mode based on selection."""
        mode = self.simulation_mode.get()
        self.gantt_text.insert(tk.END, f"Starting {mode} simulation...\n")
        if mode == "live":
            self.live_running = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.simulation_time = 0  # reset simulation time
            self.live_simulation_step()  # begin live simulation loop
        else:
            # Run simulation in non-live mode (batch run without waiting for each second)
            self.run_non_live_simulation()

    def stop_simulation(self):
        """Stop the live simulation."""
        self.live_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.gantt_text.insert(tk.END, "Live simulation stopped.\n")

    def live_simulation_step(self):
        """
        A simulation step called every 1 second.
        This function should:
         - Update simulation time.
         - Execute the selected scheduler's logic for this time unit.
         - Update the Gantt chart and process table.
         - Compute and display statistics if simulation is complete.
        """
        if not self.live_running:
            return

        self.simulation_time += 1
        self.gantt_text.insert(tk.END, f"--- Time Unit: {self.simulation_time} ---\n")
        
        # TODO: Call the appropriate scheduler algorithm based on self.selected_scheduler
        scheduler_name = self.selected_scheduler.get()
        current_schedule = []
        if scheduler_name == "FCFS":
            current_schedule = fcfs_scheduler(self.processes, self.simulation_time)
        elif scheduler_name == "SJF Preemptive":
            current_schedule = sjf_preemptive_scheduler(self.processes, self.simulation_time)
        elif scheduler_name == "SJF Non-Preemptive":
            current_schedule = sjf_non_preemptive_scheduler(self.processes, self.simulation_time)
        elif scheduler_name == "Priority Preemptive":
            current_schedule = priority_preemptive_scheduler(self.processes, self.simulation_time)
        elif scheduler_name == "Priority Non-Preemptive":
            current_schedule = priority_non_preemptive_scheduler(self.processes, self.simulation_time)
        elif scheduler_name == "Round Robin":
            try:
                quantum = int(self.entry_quantum.get().strip())
            except ValueError:
                quantum = 2
            current_schedule = round_robin_scheduler(self.processes, quantum, self.simulation_time)
        
        # Placeholder: Update process states based on the scheduler's output.
        self.gantt_text.insert(tk.END, f"Schedule at time {self.simulation_time}: {current_schedule}\n")
        
        # For each process, update remaining burst time as placeholder (simulate execution)
        for proc in self.processes:
            if not proc.is_completed() and proc.arrival_time <= self.simulation_time:
                proc.update()  # simulate execution for 1 time unit
        
        # Update the live process table
        self.update_process_table()
        
        # TODO: Calculate and update statistics (average waiting and turnaround times)
        # (This is a placeholder; complete calculation should be implemented)
        avg_wait, avg_turnaround = calculate_statistics(self.processes)
        self.stats_label.config(text=f"Avg Waiting Time: {avg_wait:.2f} | Avg Turnaround Time: {avg_turnaround:.2f}")
        
        # TODO: Update the Gantt Chart graphics (this placeholder uses text output)
        # For a more advanced implementation, consider using a Canvas widget to draw the timeline.
        
        # Continue simulation if any process still has remaining burst time
        if any(not proc.is_completed() for proc in self.processes):
            self.after(1000, self.live_simulation_step)  # schedule next time unit after 1 second
        else:
            self.gantt_text.insert(tk.END, "Simulation Complete.\n")
            self.live_running = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)

    def run_non_live_simulation(self):
        """
        Run simulation in non-live mode:
        Process all simulation steps in a loop without waiting in real time.
        Update displays at the end of the simulation.
        """
        self.simulation_time = 0
        self.gantt_text.insert(tk.END, "Running non-live simulation...\n")
        # Placeholder loop: iterate until all processes are complete.
        while any(not proc.is_completed() for proc in self.processes):
            self.simulation_time += 1
            # TODO: Execute scheduler algorithm at each simulation time unit and update processes
            scheduler_name = self.selected_scheduler.get()
            current_schedule = []
            if scheduler_name == "FCFS":
                current_schedule = fcfs_scheduler(self.processes, self.simulation_time)
            elif scheduler_name == "SJF Preemptive":
                current_schedule = sjf_preemptive_scheduler(self.processes, self.simulation_time)
            elif scheduler_name == "SJF Non-Preemptive":
                current_schedule = sjf_non_preemptive_scheduler(self.processes, self.simulation_time)
            elif scheduler_name == "Priority Preemptive":
                current_schedule = priority_preemptive_scheduler(self.processes, self.simulation_time)
            elif scheduler_name == "Priority Non-Preemptive":
                current_schedule = priority_non_preemptive_scheduler(self.processes, self.simulation_time)
            elif scheduler_name == "Round Robin":
                try:
                    quantum = int(self.entry_quantum.get().strip())
                except ValueError:
                    quantum = 2
                current_schedule = round_robin_scheduler(self.processes, quantum, self.simulation_time)
            
            # Simulate execution for processes that have arrived
            for proc in self.processes:
                if not proc.is_completed() and proc.arrival_time <= self.simulation_time:
                    proc.update()

        self.gantt_text.insert(tk.END, f"Non-live simulation complete at time unit {self.simulation_time}.\n")
        self.update_process_table()
        avg_wait, avg_turnaround = calculate_statistics(self.processes)
        self.stats_label.config(text=f"Avg Waiting Time: {avg_wait:.2f} | Avg Turnaround Time: {avg_turnaround:.2f}")

#####################################
# Main Function
#####################################

def main():
    app = SchedulerGUI()
    app.mainloop()

if __name__ == "__main__":
    main()
