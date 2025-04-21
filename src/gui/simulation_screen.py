import threading
import tkinter as tk
import customtkinter as ctk
from tkinter import ttk, messagebox
import time
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.patches as patches
import numpy as np
import csv
import random
from ..core.simulation import Simulation
from ..models.process import Process

class SimulationScreen(ctk.CTkFrame):
    """
    Screen for visualizing the CPU scheduling simulation with live updates.
    """
    
    def __init__(self, master, go_back_callback):
        """
        Initialize the SimulationScreen.
        
        Args:
            master: The parent widget
            go_back_callback: Callback function to return to the previous screen
        """
        super().__init__(master)
        
        # Store references
        self.master = master
        self.go_back_callback = go_back_callback
        self.simulation = None
        self.scheduler = None
        self.simulation_thread = None
        self.process_colors = {}
        self.next_pid = 1
        
        # Set up the UI
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the user interface elements."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)  # Header
        self.rowconfigure(1, weight=1)  # Content
        
        # Header
        self._setup_header()
        
        # Main content frame
        content_frame = ctk.CTkFrame(self)
        content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        content_frame.columnconfigure(0, weight=3)  # Gantt chart and process table
        content_frame.columnconfigure(1, weight=1)  # Controls and stats
        content_frame.rowconfigure(0, weight=1)
        
        # Left panel (Gantt chart and process table)
        left_panel = ctk.CTkFrame(content_frame)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=0)
        left_panel.columnconfigure(0, weight=1)
        left_panel.rowconfigure(0, weight=2)  # Gantt chart
        left_panel.rowconfigure(1, weight=1)  # Process table
        
        # Right panel (Controls and statistics)
        right_panel = ctk.CTkFrame(content_frame)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=0)
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(0, weight=0)  # Controls
        right_panel.rowconfigure(1, weight=1)  # Statistics
        
        # Set up the Gantt chart
        self._setup_gantt_chart(left_panel)
        
        # Set up the process table
        self._setup_process_table(left_panel)
        
        # Set up the controls
        self._setup_controls(right_panel)
        
        # Set up the statistics panel
        self._setup_stats_panel(right_panel)
    
    def _setup_header(self):
        """Set up the header with title and back button."""
        header_frame = ctk.CTkFrame(self)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        header_frame.columnconfigure(0, weight=1)  # Title
        header_frame.columnconfigure(1, weight=0)  # Back button
        
        # Title
        self.title_var = tk.StringVar(value="CPU Scheduling Simulation")
        title_label = ctk.CTkLabel(header_frame, textvariable=self.title_var, font=("Segoe UI", 18, "bold"))
        title_label.grid(row=0, column=0, sticky="w")
        
        # Back button
        back_button = ctk.CTkButton(header_frame, text="Back to Config", command=self._on_back)
        back_button.grid(row=0, column=1, sticky="e")
    
    def _setup_gantt_chart(self, parent):
        """Set up the Gantt chart visualization."""
        gantt_frame = ctk.CTkFrame(parent)
        gantt_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=(0, 5))
        
        # Create a matplotlib figure for the Gantt chart
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, gantt_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Set up initial Gantt chart
        self._init_gantt_chart()
        
        # Add tooltip for hover information
        self.tooltip = tk.Label(self, text="", bg="#ffffe0", relief="solid", borderwidth=1)
        
        # Bind mouse motion for tooltips
        self.canvas.mpl_connect("motion_notify_event", self._on_hover)
        self.canvas.mpl_connect("axes_leave_event", lambda event: self.tooltip.place_forget())
    
    def _init_gantt_chart(self):
        """Initialize the Gantt chart with empty data."""
        self.ax.clear()
        self.ax.set_title("CPU Scheduling Gantt Chart")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Processes")
        self.ax.set_xlim(0, 10)  # Initial time window
        self.ax.grid(True, which='both', axis='x', linestyle='--', linewidth=0.5)
        self.figure.tight_layout()
        self.canvas.draw()
        
        # Store gantt data for tooltips
        self.gantt_bars = []
    
    def _setup_process_table(self, parent):
        """Set up the process table."""
        table_frame = ctk.CTkFrame(parent)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=(5, 0))
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=0)  # Label
        table_frame.rowconfigure(1, weight=1)  # Table
        
        # Label
        table_label = ctk.CTkLabel(table_frame, text="Process Table", font=("Segoe UI", 14, "bold"))
        table_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        # Create the treeview for the process table
        columns = ("PID", "Name", "Arrival", "Burst", "Priority", "Remaining", "Waiting", "Turnaround", "Completion")
        
        # Use a Treeview from ttk
        self.process_table = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        # Define headings
        for col in columns:
            self.process_table.heading(col, text=col)
            width = 70 if col != "Name" else 100
            self.process_table.column(col, width=width)
        
        # Add scrollbars
        x_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=self.process_table.xview)
        y_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.process_table.yview)
        self.process_table.configure(xscrollcommand=x_scrollbar.set, yscrollcommand=y_scrollbar.set)
        
        # Place the table and scrollbars
        self.process_table.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        x_scrollbar.grid(row=2, column=0, sticky="ew", padx=5)
        y_scrollbar.grid(row=1, column=1, sticky="ns", pady=5)
    
    def _setup_controls(self, parent):
        """Set up the simulation controls."""
        controls_frame = ctk.CTkFrame(parent)
        controls_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=(0, 5))
        controls_frame.columnconfigure(0, weight=1)
        controls_frame.columnconfigure(1, weight=1)
        
        # Control buttons
        ctk.CTkLabel(controls_frame, text="Simulation Controls", font=("Segoe UI", 14, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        
        # Simulation control buttons
        self.start_button = ctk.CTkButton(controls_frame, text="Start", command=self._on_start)
        self.start_button.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        
        self.pause_button = ctk.CTkButton(controls_frame, text="Pause", command=self._on_pause, state="disabled")
        self.pause_button.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        self.stop_button = ctk.CTkButton(controls_frame, text="Stop", command=self._on_stop, state="disabled")
        self.stop_button.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        
        self.reset_button = ctk.CTkButton(controls_frame, text="Reset", command=self._on_reset)
        self.reset_button.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        
        # Speed control
        ctk.CTkLabel(controls_frame, text="Simulation Speed:").grid(
            row=3, column=0, sticky="w", padx=10, pady=5)
        
        self.speed_var = tk.IntVar(value=1)
        speed_slider = ctk.CTkSlider(controls_frame, from_=1, to=10, number_of_steps=9, 
                                   variable=self.speed_var, command=self._on_speed_change)
        speed_slider.grid(row=3, column=1, sticky="ew", padx=5, pady=5)
        
        self.speed_label = ctk.CTkLabel(controls_frame, text="1x")
        self.speed_label.grid(row=3, column=1, sticky="e", padx=10, pady=5)
        
        # Add live process frame
        self._setup_add_live_process(controls_frame, start_row=4)
        
        # Export results button
        self.export_button = ctk.CTkButton(controls_frame, text="Export Results", command=self._on_export_results)
        self.export_button.grid(row=9, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
    
    def _setup_add_live_process(self, parent, start_row):
        """Set up the UI for adding live processes during simulation."""
        # Separator
        separator = ttk.Separator(parent, orient="horizontal")
        separator.grid(row=start_row, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        
        # Add process label
        ctk.CTkLabel(parent, text="Add Live Process", font=("Segoe UI", 14, "bold")).grid(
            row=start_row+1, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        
        # Process Name
        ctk.CTkLabel(parent, text="Name:").grid(
            row=start_row+2, column=0, sticky="w", padx=10, pady=5)
        self.live_name_var = tk.StringVar(value=f"P{self.next_pid}")
        live_name_entry = ctk.CTkEntry(parent, textvariable=self.live_name_var)
        live_name_entry.grid(row=start_row+2, column=1, sticky="ew", padx=5, pady=5)
        
        # Burst Time
        ctk.CTkLabel(parent, text="Burst Time:").grid(
            row=start_row+3, column=0, sticky="w", padx=10, pady=5)
        self.live_burst_var = tk.StringVar(value="5")
        live_burst_entry = ctk.CTkEntry(parent, textvariable=self.live_burst_var)
        live_burst_entry.grid(row=start_row+3, column=1, sticky="ew", padx=5, pady=5)
        
        # Priority
        ctk.CTkLabel(parent, text="Priority:").grid(
            row=start_row+4, column=0, sticky="w", padx=10, pady=5)
        self.live_priority_var = tk.StringVar(value="1")
        live_priority_entry = ctk.CTkEntry(parent, textvariable=self.live_priority_var)
        live_priority_entry.grid(row=start_row+4, column=1, sticky="ew", padx=5, pady=5)
        
        # Add button
        self.add_live_button = ctk.CTkButton(parent, text="Add Process", command=self._on_add_live_process, state="disabled")
        self.add_live_button.grid(row=start_row+5, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
    
    def _setup_stats_panel(self, parent):
        """Set up the statistics panel."""
        stats_frame = ctk.CTkFrame(parent)
        stats_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=(5, 0))
        stats_frame.columnconfigure(0, weight=1)
        stats_frame.columnconfigure(1, weight=1)
        
        # Statistics Label
        ctk.CTkLabel(stats_frame, text="Simulation Statistics", font=("Segoe UI", 14, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        
        # Current time
        ctk.CTkLabel(stats_frame, text="Current Time:").grid(
            row=1, column=0, sticky="w", padx=10, pady=5)
        self.current_time_var = tk.StringVar(value="0")
        ctk.CTkLabel(stats_frame, textvariable=self.current_time_var).grid(
            row=1, column=1, sticky="w")
        
        # Current process
        ctk.CTkLabel(stats_frame, text="Current Process:").grid(
            row=2, column=0, sticky="w", padx=10, pady=5)
        self.current_process_var = tk.StringVar(value="None")
        ctk.CTkLabel(stats_frame, textvariable=self.current_process_var).grid(
            row=2, column=1, sticky="w")
        
        # Completed processes
        ctk.CTkLabel(stats_frame, text="Completed:").grid(
            row=3, column=0, sticky="w", padx=10, pady=5)
        self.completed_var = tk.StringVar(value="0/0")
        ctk.CTkLabel(stats_frame, textvariable=self.completed_var).grid(
            row=3, column=1, sticky="w")
        
        # Average waiting time
        ctk.CTkLabel(stats_frame, text="Avg. Waiting Time:").grid(
            row=4, column=0, sticky="w", padx=10, pady=5)
        self.avg_waiting_var = tk.StringVar(value="0.00")
        ctk.CTkLabel(stats_frame, textvariable=self.avg_waiting_var).grid(
            row=4, column=1, sticky="w")
        
        # Average turnaround time
        ctk.CTkLabel(stats_frame, text="Avg. Turnaround:").grid(
            row=5, column=0, sticky="w", padx=10, pady=5)
        self.avg_turnaround_var = tk.StringVar(value="0.00")
        ctk.CTkLabel(stats_frame, textvariable=self.avg_turnaround_var).grid(
            row=5, column=1, sticky="w")
        
        # Average response time
        ctk.CTkLabel(stats_frame, text="Avg. Response Time:").grid(
            row=6, column=0, sticky="w", padx=10, pady=5)
        self.avg_response_var = tk.StringVar(value="0.00")
        ctk.CTkLabel(stats_frame, textvariable=self.avg_response_var).grid(
            row=6, column=1, sticky="w")
        
        # CPU utilization
        ctk.CTkLabel(stats_frame, text="CPU Utilization:").grid(
            row=7, column=0, sticky="w", padx=10, pady=5)
        self.cpu_util_var = tk.StringVar(value="0.00%")
        ctk.CTkLabel(stats_frame, textvariable=self.cpu_util_var).grid(
            row=7, column=1, sticky="w")
        
        # Throughput
        ctk.CTkLabel(stats_frame, text="Throughput:").grid(
            row=8, column=0, sticky="w", padx=10, pady=5)
        self.throughput_var = tk.StringVar(value="0.00 proc/unit")
        ctk.CTkLabel(stats_frame, textvariable=self.throughput_var).grid(
            row=8, column=1, sticky="w")
    
    def set_scheduler(self, scheduler):
        """
        Set the scheduler to use for simulation.
        
        Args:
            scheduler: The configured scheduler object
        """
        self.scheduler = scheduler
        
        # Update the title with scheduler name
        self.title_var.set(f"CPU Scheduling Simulation: {scheduler.name}")
        
        # Initialize simulation with scheduler
        self.simulation = Simulation(scheduler)
        
        # Set up callbacks for updates
        self.simulation.set_process_update_callback(self._update_process_table)
        self.simulation.set_gantt_update_callback(self._update_gantt_chart)
        self.simulation.set_stats_update_callback(self._update_stats)
        
        # Update the process table initially
        self._update_process_table(scheduler.processes, 0)
        
        # Generate colors for processes
        self._generate_process_colors(scheduler.processes)

        # Enable/disable controls
        self._update_controls()
    
    def _generate_process_colors(self, processes):
        """Generate distinct colors for each process for the Gantt chart."""
        # Initialize colors for processes
        for process in processes:
            if process.pid not in self.process_colors:
                # Generate a random pastel color
                r = random.uniform(0.5, 0.9)
                g = random.uniform(0.5, 0.9)
                b = random.uniform(0.5, 0.9)
                self.process_colors[process.pid] = (r, g, b)
    
    def _update_process_table(self, processes, current_time):
        """Update the process table with current process information."""
        # Clear current table
        for item in self.process_table.get_children():
            self.process_table.delete(item)
        
        # Add colors for any new processes
        self._generate_process_colors(processes)
        
        # Update the table
        for process in processes:
            remaining = process.remaining_time
            waiting = process.waiting_time
            turnaround = process.turnaround_time
            completion = process.completion_time if process.completion_time is not None else "-"
            
            self.process_table.insert("", "end", values=(
                process.pid,
                process.name,
                process.arrival_time,
                process.burst_time,
                process.priority if process.priority is not None else "-",
                remaining,
                waiting,
                turnaround,
                completion
            ))
            
        # Update current time
        self.current_time_var.set(str(current_time))
        
        # Update completion count
        completed_count = len([p for p in processes if p.is_completed()])
        self.completed_var.set(f"{completed_count}/{len(processes)}")
        
        # Make sure to update the next PID for adding new processes
        if processes:
            max_pid = max(p.pid for p in processes)
            self.next_pid = max_pid + 1
            self.live_name_var.set(f"P{self.next_pid}")
    
    def _update_gantt_chart(self, current_process, current_time):
        """Update the Gantt chart with current execution information."""
        if not self.simulation:
            return
            
        # Clear existing chart
        self.ax.clear()
        self.gantt_bars = []
        
        # Get all processes
        processes = self.scheduler.processes
        if not processes:
            return
            
        # Prepare data for Gantt chart
        process_names = [p.name for p in processes]
        y_pos = np.arange(len(process_names))
        
        # Set up chart
        self.ax.set_title("CPU Scheduling Gantt Chart")
        self.ax.set_xlabel("Time")
        self.ax.set_yticks(y_pos)
        self.ax.set_yticklabels(process_names)
        
        # Dynamically adjust time window based on current time
        window_size = 20  # Show 20 time units at a time
        start_time = max(0, current_time - window_size // 2)
        end_time = start_time + window_size
        self.ax.set_xlim(start_time, end_time)
        
        # Add grid
        self.ax.grid(True, which='both', axis='x', linestyle='--', linewidth=0.5)
        
        # Draw execution blocks for each process
        timeline_entries = self.simulation.get_timeline_entries()
        
        # Draw each timeline entry
        for entry in timeline_entries:
            process, start_time, end_time = entry
            process_idx = processes.index(process)
            color = self.process_colors[process.pid]
            
            # Create a rectangle for this execution block
            rect = patches.Rectangle(
                (start_time, process_idx - 0.4),  # (x, y)
                end_time - start_time,              # width
                0.8,                               # height
                linewidth=1,
                edgecolor='black',
                facecolor=color,
                alpha=0.8,
                label=process.name
            )
            self.ax.add_patch(rect)
            
            # Store rectangle for tooltip
            self.gantt_bars.append((rect, process, start_time, end_time))
        
        # Draw current time marker
        self.ax.axvline(x=current_time, color='red', linestyle='-', linewidth=1)
        
        # Adjust layout and redraw
        self.figure.tight_layout()
        self.canvas.draw()
    
    def _update_stats(self, avg_waiting, avg_turnaround):
        """Update the statistics panel with current metrics."""
        if not self.simulation or not self.scheduler:
            return
            
        # Update average metrics
        self.avg_waiting_var.set(f"{avg_waiting:.2f}")
        self.avg_turnaround_var.set(f"{avg_turnaround:.2f}")
        
        # Get additional metrics
        avg_response = self.scheduler.get_average_response_time()
        cpu_util = self.simulation.get_cpu_utilization() * 100
        throughput = self.simulation.get_throughput()
        
        # Update UI
        self.avg_response_var.set(f"{avg_response:.2f}")
        self.cpu_util_var.set(f"{cpu_util:.2f}%")
        self.throughput_var.set(f"{throughput:.2f} proc/unit")
        
        # Update current process
        current_process = self.scheduler.current_process
        if current_process:
            self.current_process_var.set(f"{current_process.name} (PID: {current_process.pid})")
        else:
            self.current_process_var.set("None (Idle)")
    
    def _on_hover(self, event):
        """Handle hover events on the Gantt chart to show tooltips."""
        if not self.gantt_bars or not hasattr(event, 'xdata') or not hasattr(event, 'ydata') or event.xdata is None or event.ydata is None:
            self.tooltip.place_forget()
            return
            
        # Check if mouse is over any gantt bar
        for rect, process, start, end in self.gantt_bars:
            if rect.contains_point([event.xdata, event.ydata]):
                # Calculate tooltip position
                x, y = event.x, event.y
                
                # Create tooltip text
                text = (f"Process: {process.name} (PID: {process.pid})\n"
                        f"Time: {start} to {end}\n"
                        f"Duration: {end - start}")
                
                # Update and show tooltip
                self.tooltip.configure(text=text)
                self.tooltip.place(x=x+10, y=y+10)
                return
                
        # If not over any bar, hide tooltip
        self.tooltip.place_forget()
    
    def _update_controls(self):
        """Update the enabled/disabled state of controls based on simulation state."""
        simulation_exists = self.simulation is not None
        simulation_running = simulation_exists and self.simulation.running
        simulation_paused = simulation_exists and self.simulation.paused
        has_processes = simulation_exists and len(self.scheduler.processes) > 0
        
        # Update button states
        self.start_button.configure(state="normal" if (simulation_exists and has_processes and not simulation_running) else "disabled")
        self.pause_button.configure(state="normal" if simulation_running and not simulation_paused else "disabled")
        self.stop_button.configure(state="normal" if simulation_running or simulation_paused else "disabled")
        self.reset_button.configure(state="normal" if simulation_exists else "disabled")
        
        # Always enable the Add Process button when simulation is running
        # This ensures you can add processes during execution
        self.add_live_button.configure(state="normal" if simulation_running else "disabled")
        
        # Make the button more visible when enabled
        if simulation_running:
            self.add_live_button.configure(fg_color="#28a745")  # Green color when enabled
        else:
            self.add_live_button.configure(fg_color="transparent")  # Default color when disabled
        
        self.export_button.configure(state="normal" if simulation_exists and self.simulation.has_results() else "disabled")
    
    def _on_start(self):
        """Start the simulation."""
        if not self.simulation:
            return
            
        # Start the simulation in a new thread
        self.simulation.start()
        self.simulation_thread = threading.Thread(target=self._run_simulation)
        self.simulation_thread.daemon = True
        self.simulation_thread.start()
        
        # Update control states
        self._update_controls()
    
    def _on_pause(self):
        """Pause the simulation."""
        if not self.simulation:
            return
            
        if self.simulation.paused:
            self.simulation.resume()
            self.pause_button.configure(text="Pause")
        else:
            self.simulation.pause()
            self.pause_button.configure(text="Resume")
            
        self._update_controls()
    
    def _on_stop(self):
        """Stop the simulation."""
        if not self.simulation:
            return
            
        self.simulation.stop()
        if self.simulation_thread and self.simulation_thread.is_alive():
            self.simulation_thread.join(timeout=1.0)
            
        self.pause_button.configure(text="Pause")
        self._update_controls()
    
    def _on_reset(self):
        """Reset the simulation."""
        if not self.simulation:
            return
            
        # Stop if running
        if self.simulation.running:
            self._on_stop()
            
        # Reset simulation
        self.simulation.reset()
        
        # Reset UI elements
        self._init_gantt_chart()
        self._update_process_table(self.scheduler.processes, 0)
        self._update_stats(0, 0)
        
        self.pause_button.configure(text="Pause")
        self._update_controls()
    
    def _on_speed_change(self, value):
        """Handle simulation speed change."""
        speed = int(value)
        self.speed_label.configure(text=f"{speed}x")
        
        if self.simulation:
            self.simulation.set_speed(speed)
    
    def _on_add_live_process(self):
        """Add a new process during simulation execution with arrival time set to current time."""
        if not self.simulation or not self.simulation.running:
            messagebox.showerror("Error", "Simulation must be running to add live processes")
            return
            
        try:
            # Get values from entry fields
            name = self.live_name_var.get()
            burst_time = int(self.live_burst_var.get())
            priority_str = self.live_priority_var.get()
            priority = int(priority_str) if priority_str else None
            
            # Validate inputs
            if not name:
                messagebox.showerror("Input Error", "Process name cannot be empty")
                return
                
            if burst_time <= 0:
                messagebox.showerror("Input Error", "Burst time must be positive")
                return
                
            if priority is not None and priority < 0:
                messagebox.showerror("Input Error", "Priority cannot be negative")
                return
                
            # Get the current simulation time from the scheduler
            current_time = self.scheduler.current_time
                
            # Add process to simulation using the main thread's event loop 
            # to avoid threading issues
            def add_process_safely():
                try:
                    # Add the process with arrival time equal to current simulation time
                    process = self.simulation.add_live_process(
                        name=name,
                        burst_time=burst_time,
                        priority=priority,
                        pid=self.next_pid
                    )
                    
                    # Print information to console for debugging
                    print(f"Process added: {process.name} (PID: {process.pid})")
                    print(f"Arrival time: {process.arrival_time}, Current time: {current_time}")
                    
                    # Increment next PID and update entry field
                    self.next_pid += 1
                    self.live_name_var.set(f"P{self.next_pid}")
                    
                    # Reset entry fields
                    self.live_burst_var.set("5")
                    self.live_priority_var.set("1")
                    
                    # Force an immediate update to the process table and Gantt chart
                    self._update_process_table(self.scheduler.processes, current_time)
                    self._update_gantt_chart(self.scheduler.current_process, current_time)
                    
                    # Show success message
                    messagebox.showinfo("Process Added", 
                        f"Process {name} added successfully!\n" +
                        f"Arrival time: {current_time}\n" +
                        f"Burst time: {burst_time}\n" +
                        f"Priority: {priority if priority is not None else 'N/A'}"
                    )
                    
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to add process: {str(e)}")
            
            # Execute the add process operation in the main thread
            self.master.after(0, add_process_safely)
            
        except ValueError as e:
            messagebox.showerror("Input Error", f"Invalid input values: {str(e)}")
    
    def _on_export_results(self):
        """Export simulation results to a CSV or text file."""
        if not self.simulation or not self.scheduler.processes:
            messagebox.showinfo("Export", "No simulation results to export")
            return
            
        try:
            from tkinter import filedialog
            
            # Prompt user for file location and name
            filetypes = [
                ("CSV files", "*.csv"),
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=filetypes,
                title="Save Simulation Results",
                initialfile=f"{self.scheduler.name.replace(' ', '_')}_results"
            )
            
            if not filename:  # User canceled
                return
                
            # Determine the file format based on extension
            is_csv = filename.lower().endswith('.csv')
            
            with open(filename, "w", newline="") as file:
                if is_csv:
                    writer = csv.writer(file)
                    
                    # Write header
                    writer.writerow([
                        "PID", "Name", "Arrival Time", "Burst Time", "Priority",
                        "Completion Time", "Turnaround Time", "Waiting Time", "Response Time"
                    ])
                    
                    # Write data for each process
                    for process in self.scheduler.processes:
                        writer.writerow([
                            process.pid,
                            process.name,
                            process.arrival_time,
                            process.burst_time,
                            process.priority if process.priority is not None else "",
                            process.completion_time if process.completion_time is not None else "",
                            process.turnaround_time,
                            process.waiting_time,
                            process.response_time if process.response_time is not None else ""
                        ])
                else:
                    # Write as formatted text
                    file.write(f"CPU Scheduling Simulation Results: {self.scheduler.name}\n")
                    file.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    
                    # Write summary statistics
                    file.write("=== Summary Statistics ===\n")
                    file.write(f"Total Processes: {len(self.scheduler.processes)}\n")
                    file.write(f"Completed Processes: {len(self.scheduler.completed_processes)}\n")
                    file.write(f"Average Waiting Time: {self.scheduler.get_average_waiting_time():.2f}\n")
                    file.write(f"Average Turnaround Time: {self.scheduler.get_average_turnaround_time():.2f}\n")
                    file.write(f"Average Response Time: {self.scheduler.get_average_response_time():.2f}\n")
                    file.write(f"CPU Utilization: {self.simulation.get_cpu_utilization() * 100:.2f}%\n")
                    file.write(f"Throughput: {self.simulation.get_throughput():.2f} processes/time unit\n\n")
                    
                    # Write process details
                    file.write("=== Process Details ===\n")
                    file.write(f"{'PID':<5} {'Name':<10} {'Arrival':<8} {'Burst':<6} {'Priority':<8} {'Completion':<10} {'Turnaround':<10} {'Waiting':<8} {'Response':<8}\n")
                    file.write("-" * 80 + "\n")
                    
                    for process in self.scheduler.processes:
                        file.write(f"{process.pid:<5} {process.name:<10} {process.arrival_time:<8} {process.burst_time:<6} "
                                   f"{str(process.priority) if process.priority is not None else '-':<8} "
                                   f"{str(process.completion_time) if process.completion_time is not None else '-':<10} "
                                   f"{process.turnaround_time:<10.2f} {process.waiting_time:<8.2f} "
                                   f"{str(process.response_time) if process.response_time is not None else '-':<8}\n")
                    
                    # Write execution timeline
                    file.write("\n=== Execution Timeline ===\n")
                    timeline = self.simulation.get_timeline_entries()
                    for entry in timeline:
                        process, start, end = entry
                        file.write(f"Time {start:<4}-{end:<4}: Process {process.name} (PID: {process.pid})\n")
                    
            messagebox.showinfo("Export Successful", f"Results saved to {filename}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export results: {str(e)}")
    
    def _on_back(self):
        """Return to the configuration screen."""
        if self.simulation and self.simulation.running:
            # Confirm if user wants to stop the simulation
            if not messagebox.askyesno("Confirm", "Simulation is running. Do you want to stop and go back?"):
                return
                
            # Stop the simulation
            self._on_stop()
            
        # Call the go_back callback
        self.go_back_callback()
    
    def _run_simulation(self):
        """Monitor simulation state and update UI."""
        try:
            while self.simulation and self.simulation.running:
                # Update UI controls based on simulation state
                self.master.after(100, self._update_controls)
                time.sleep(0.1)
                
            # Final update when simulation ends
            self.master.after(0, self._update_controls)
            
        except Exception as e:
            print(f"Error in simulation thread: {str(e)}")
            messagebox.showerror("Simulation Error", f"An error occurred: {str(e)}")
            self.simulation.stop()