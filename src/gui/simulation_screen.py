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

# Define dark theme colors for matplotlib and ttk
DARK_BG = "#2b2b2b"
DARK_FG = "#DCE4EE"
DARK_GRID = "#444444"
DARK_AXES = "#333333"
DARK_TOOLTIP_BG = "#3f3f3f"
DARK_TOOLTIP_FG = "#ffffff"

class SimulationScreen(ctk.CTkFrame):
    """
    Screen for visualizing the CPU scheduling simulation with live updates.
    Redesigned for better layout and usability.
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
        """Set up the user interface elements with a redesigned layout."""
        self.columnconfigure(0, weight=3)  # Main content area (Gantt + Table)
        self.columnconfigure(1, weight=1)  # Sidebar (Controls, Stats, Add Process)
        self.rowconfigure(0, weight=0)  # Header
        self.rowconfigure(1, weight=1)  # Main content row

        # Header
        self._setup_header()

        # Main content frame (Left Side: Gantt + Table)
        main_content_frame = ctk.CTkFrame(self)
        main_content_frame.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=(0, 10))
        main_content_frame.columnconfigure(0, weight=1)
        main_content_frame.rowconfigure(0, weight=2)  # Gantt chart
        main_content_frame.rowconfigure(1, weight=1)  # Process table

        # Set up the Gantt chart
        self._setup_gantt_chart(main_content_frame)

        # Set up the process table
        self._setup_process_table(main_content_frame)

        # Sidebar frame (Right Side: Tabs for Controls, Stats, Add Process)
        sidebar_frame = ctk.CTkFrame(self)
        sidebar_frame.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=(0, 10))
        sidebar_frame.columnconfigure(0, weight=1)
        sidebar_frame.rowconfigure(0, weight=1) # Tab view will take full height

        # Create Tab View for Controls, Add Process, Stats
        self.tab_view = ctk.CTkTabview(sidebar_frame)
        self.tab_view.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Add tabs
        self.tab_view.add("Controls")
        self.tab_view.add("Add Process")
        self.tab_view.add("Statistics")
        self.tab_view.add("Export") # Added Export Tab

        # Set up the controls in the "Controls" tab
        self._setup_controls(self.tab_view.tab("Controls"))

        # Set up the add live process UI in the "Add Process" tab
        self._setup_add_live_process(self.tab_view.tab("Add Process"))

        # Set up the statistics panel in the "Statistics" tab
        self._setup_stats_panel(self.tab_view.tab("Statistics"))

        # Set up the export controls in the "Export" tab
        self._setup_export_controls(self.tab_view.tab("Export"))

    def _setup_header(self):
        """Set up the header with title and back button."""
        header_frame = ctk.CTkFrame(self, fg_color="transparent") # Make header transparent
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        header_frame.columnconfigure(0, weight=1)  # Title
        header_frame.columnconfigure(1, weight=0)  # Back button

        # Title
        self.title_var = tk.StringVar(value="CPU Scheduling Simulation")
        title_label = ctk.CTkLabel(header_frame, textvariable=self.title_var, font=("Segoe UI", 18, "bold"))
        title_label.grid(row=0, column=0, sticky="w", padx=5)

        # Back button
        back_button = ctk.CTkButton(header_frame, text="< Back to Config", command=self._on_back, width=120)
        back_button.grid(row=0, column=1, sticky="e", padx=5)

    def _setup_gantt_chart(self, parent):
        """Set up the Gantt chart visualization with dark theme."""
        gantt_frame = ctk.CTkFrame(parent)
        gantt_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=(0, 5))
        gantt_frame.columnconfigure(0, weight=1)
        gantt_frame.rowconfigure(0, weight=1)

        # Create a matplotlib figure for the Gantt chart with dark background
        self.figure = Figure(figsize=(5, 4), dpi=100, facecolor=DARK_BG)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor(DARK_AXES) # Dark background for the plot area

        # Configure colors for axes and ticks
        self.ax.spines['bottom'].set_color(DARK_FG)
        self.ax.spines['top'].set_color(DARK_FG)
        self.ax.spines['left'].set_color(DARK_FG)
        self.ax.spines['right'].set_color(DARK_FG)
        self.ax.xaxis.label.set_color(DARK_FG)
        self.ax.yaxis.label.set_color(DARK_FG)
        self.ax.tick_params(axis='x', colors=DARK_FG)
        self.ax.tick_params(axis='y', colors=DARK_FG)
        self.ax.title.set_color(DARK_FG)

        self.canvas = FigureCanvasTkAgg(self.figure, gantt_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        # Set the canvas background to match the frame
        self.canvas_widget.configure(bg=gantt_frame.cget("fg_color")[1]) # Use the dark mode color
        self.canvas_widget.grid(row=0, column=0, sticky="nsew")

        # Set up initial Gantt chart
        self._init_gantt_chart()

        # Add tooltip for hover information (using a CTkLabel for better theme integration)
        self.tooltip = ctk.CTkLabel(self, text="", corner_radius=5, fg_color=DARK_TOOLTIP_BG, text_color=DARK_TOOLTIP_FG)

        # Bind mouse motion for tooltips
        self.canvas.mpl_connect("motion_notify_event", self._on_hover)
        self.canvas.mpl_connect("axes_leave_event", lambda event: self.tooltip.place_forget())

    def _init_gantt_chart(self):
        """Initialize the Gantt chart with dark theme styling."""
        self.ax.clear()
        self.ax.set_title("CPU Scheduling Gantt Chart", color=DARK_FG)
        self.ax.set_xlabel("Time", color=DARK_FG)
        self.ax.set_ylabel("Processes", color=DARK_FG)
        self.ax.set_xlim(0, 10)  # Initial time window

        # Set grid color
        self.ax.grid(True, which='both', axis='x', linestyle='--', linewidth=0.5, color=DARK_GRID)

        # Re-apply axis/tick colors after clear
        self.ax.set_facecolor(DARK_AXES)
        self.ax.spines['bottom'].set_color(DARK_FG)
        self.ax.spines['top'].set_color(DARK_FG)
        self.ax.spines['left'].set_color(DARK_FG)
        self.ax.spines['right'].set_color(DARK_FG)
        self.ax.tick_params(axis='x', colors=DARK_FG)
        self.ax.tick_params(axis='y', colors=DARK_FG)

        self.figure.tight_layout()
        self.canvas.draw()

        # Store gantt data for tooltips
        self.gantt_bars = []

    def _setup_process_table(self, parent):
        """Set up the process table with dark theme styling."""
        table_frame = ctk.CTkFrame(parent)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=(5, 0))
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=0)  # Label
        table_frame.rowconfigure(1, weight=1)  # Table

        # Label
        table_label = ctk.CTkLabel(table_frame, text="Process Table", font=("Segoe UI", 14, "bold"))
        table_label.grid(row=0, column=0, sticky="w", padx=5, pady=(5, 2))

        # --- Style the ttk.Treeview for dark theme --- 
        style = ttk.Style()
        style.theme_use("clam") # 'clam' theme is often easier to customize

        # Configure Treeview colors
        style.configure("Treeview",
                        background=DARK_BG,
                        foreground=DARK_FG,
                        fieldbackground=DARK_BG,
                        borderwidth=0)
        # Configure Header colors
        style.configure("Treeview.Heading",
                        background=DARK_AXES, # Slightly different background for header
                        foreground=DARK_FG,
                        relief="flat")
        # Configure selected item colors
        style.map('Treeview',
                  background=[('selected', '#0078D7')], # Use a highlight color
                  foreground=[('selected', 'white')])
        # Remove borders from headings
        style.layout("Treeview.Heading", [('Treeview.heading', {'sticky': 'nswe'})])
        # --- End of Styling --- 

        # Create the treeview for the process table
        columns = ("PID", "Name", "Arrival", "Burst", "Priority", "Remaining", "Waiting", "Turnaround", "Completion")
        self.process_table = ttk.Treeview(table_frame, columns=columns, show="headings", style="Treeview")

        # Define headings
        for col in columns:
            self.process_table.heading(col, text=col, anchor='w')
            width = 70 if col != "Name" else 100
            min_width = 50 if col != "Name" else 80
            self.process_table.column(col, width=width, minwidth=min_width, stretch=tk.YES, anchor='w')

        # Add scrollbars (using ttk scrollbars, styling them is harder)
        # Consider CTkScrollbar if deeper theme integration is needed
        x_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=self.process_table.xview)
        y_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.process_table.yview)
        self.process_table.configure(xscrollcommand=x_scrollbar.set, yscrollcommand=y_scrollbar.set)

        # Place the table and scrollbars
        self.process_table.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0,5))
        x_scrollbar.grid(row=2, column=0, sticky="ew", padx=5)
        y_scrollbar.grid(row=1, column=1, sticky="ns", pady=(0,5))

    def _setup_controls(self, parent_tab):
        """Set up the simulation controls within the 'Controls' tab."""
        parent_tab.columnconfigure(0, weight=1)
        parent_tab.columnconfigure(1, weight=1)

        # Simulation control buttons frame
        button_frame = ctk.CTkFrame(parent_tab, fg_color="transparent")
        button_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)

        self.start_button = ctk.CTkButton(button_frame, text="Start", command=self._on_start)
        self.start_button.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        self.pause_button = ctk.CTkButton(button_frame, text="Pause", command=self._on_pause, state="disabled")
        self.pause_button.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        self.stop_button = ctk.CTkButton(button_frame, text="Stop", command=self._on_stop, state="disabled")
        self.stop_button.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        self.reset_button = ctk.CTkButton(button_frame, text="Reset", command=self._on_reset)
        self.reset_button.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        # Speed control frame
        speed_frame = ctk.CTkFrame(parent_tab, fg_color="transparent")
        speed_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=10)
        speed_frame.columnconfigure(1, weight=1) # Allow slider to expand

        ctk.CTkLabel(speed_frame, text="Speed:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5)

        self.speed_var = tk.IntVar(value=1)
        speed_slider = ctk.CTkSlider(speed_frame, from_=1, to=10, number_of_steps=9,
                                   variable=self.speed_var, command=self._on_speed_change)
        speed_slider.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        self.speed_label = ctk.CTkLabel(speed_frame, text="1x", width=25) # Fixed width for label
        self.speed_label.grid(row=0, column=2, sticky="e", padx=5, pady=5)

    def _setup_add_live_process(self, parent_tab):
        """Set up the UI for adding live processes within the 'Add Process' tab."""
        parent_tab.columnconfigure(0, weight=0) # Label column
        parent_tab.columnconfigure(1, weight=1) # Entry column

        # Process Name
        ctk.CTkLabel(parent_tab, text="Name:").grid(
            row=0, column=0, sticky="w", padx=10, pady=5)
        self.live_name_var = tk.StringVar(value=f"P{self.next_pid}")
        live_name_entry = ctk.CTkEntry(parent_tab, textvariable=self.live_name_var)
        live_name_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        # Burst Time
        ctk.CTkLabel(parent_tab, text="Burst Time:").grid(
            row=1, column=0, sticky="w", padx=10, pady=5)
        self.live_burst_var = tk.StringVar(value="5")
        live_burst_entry = ctk.CTkEntry(parent_tab, textvariable=self.live_burst_var)
        live_burst_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        # Priority
        ctk.CTkLabel(parent_tab, text="Priority:").grid(
            row=2, column=0, sticky="w", padx=10, pady=5)
        self.live_priority_var = tk.StringVar(value="1")
        live_priority_entry = ctk.CTkEntry(parent_tab, textvariable=self.live_priority_var)
        live_priority_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=5)

        # Add button
        self.add_live_button = ctk.CTkButton(parent_tab, text="Add Process", command=self._on_add_live_process, state="disabled")
        self.add_live_button.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=10)

    def _setup_stats_panel(self, parent_tab):
        """Set up the statistics panel within the 'Statistics' tab."""
        parent_tab.columnconfigure(0, weight=1) # Label column
        parent_tab.columnconfigure(1, weight=1) # Value column

        row_index = 0

        # Helper function to add stat rows
        def add_stat_row(label_text, var):
            nonlocal row_index
            ctk.CTkLabel(parent_tab, text=label_text).grid(
                row=row_index, column=0, sticky="w", padx=10, pady=3)
            ctk.CTkLabel(parent_tab, textvariable=var).grid(
                row=row_index, column=1, sticky="w", padx=5, pady=3)
            row_index += 1

        # Current time
        self.current_time_var = tk.StringVar(value="0")
        add_stat_row("Current Time:", self.current_time_var)

        # Current process
        self.current_process_var = tk.StringVar(value="None")
        add_stat_row("Current Process:", self.current_process_var)

        # Completed processes
        self.completed_var = tk.StringVar(value="0/0")
        add_stat_row("Completed:", self.completed_var)

        # Separator
        ttk.Separator(parent_tab, orient="horizontal").grid(
            row=row_index, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        row_index += 1

        # Average waiting time
        self.avg_waiting_var = tk.StringVar(value="0.00")
        add_stat_row("Avg. Waiting:", self.avg_waiting_var)

        # Average turnaround time
        self.avg_turnaround_var = tk.StringVar(value="0.00")
        add_stat_row("Avg. Turnaround:", self.avg_turnaround_var)

        # Average response time
        self.avg_response_var = tk.StringVar(value="0.00")
        add_stat_row("Avg. Response:", self.avg_response_var)

        # CPU utilization
        self.cpu_util_var = tk.StringVar(value="0.00%")
        add_stat_row("CPU Utilization:", self.cpu_util_var)

        # Throughput
        self.throughput_var = tk.StringVar(value="0.00 proc/unit")
        add_stat_row("Throughput:", self.throughput_var)

    def _setup_export_controls(self, parent_tab):
        """Set up the export controls within the 'Export' tab."""
        parent_tab.columnconfigure(0, weight=1)
        parent_tab.rowconfigure(0, weight=0) # Button row
        parent_tab.rowconfigure(1, weight=1) # Spacer row

        # Export results button
        self.export_button = ctk.CTkButton(parent_tab, text="Export Results", command=self._on_export_results, state="disabled")
        self.export_button.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

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
        """Update the Gantt chart with dark theme styling."""
        if not self.simulation:
            return

        # Clear existing chart
        self.ax.clear()
        self.gantt_bars = []

        # Get all processes
        processes = self.scheduler.processes
        if not processes:
            # If no processes, still draw the base chart correctly themed
            self._init_gantt_chart()
            return

        # Prepare data for Gantt chart
        process_names = [p.name for p in processes]
        y_pos = np.arange(len(process_names))

        # Set up chart elements with dark theme colors
        self.ax.set_title("CPU Scheduling Gantt Chart", color=DARK_FG)
        self.ax.set_xlabel("Time", color=DARK_FG)
        self.ax.set_ylabel("Processes", color=DARK_FG)
        self.ax.set_yticks(y_pos)
        self.ax.set_yticklabels(process_names, color=DARK_FG) # Set tick label color
        self.ax.set_facecolor(DARK_AXES)

        # Configure colors for axes and ticks
        self.ax.spines['bottom'].set_color(DARK_FG)
        self.ax.spines['top'].set_color(DARK_FG)
        self.ax.spines['left'].set_color(DARK_FG)
        self.ax.spines['right'].set_color(DARK_FG)
        self.ax.tick_params(axis='x', colors=DARK_FG)
        self.ax.tick_params(axis='y', colors=DARK_FG)

        # Dynamically adjust time window based on current time
        max_time = current_time
        if self.simulation.get_timeline_entries():
             max_time = max(current_time, max(entry[2] for entry in self.simulation.get_timeline_entries()))

        window_size = 20  # Show 20 time units at a time
        # Adjust window logic slightly to handle max_time
        if max_time <= window_size:
            start_time = 0
            end_time = window_size
        else:
            start_time = max(0, current_time - window_size * 0.75) # Show more past than future
            end_time = start_time + window_size
            if end_time < max_time:
                 end_time = max_time + 2 # Add a little buffer
                 start_time = end_time - window_size

        self.ax.set_xlim(start_time, end_time)

        # Add grid
        self.ax.grid(True, which='both', axis='x', linestyle='--', linewidth=0.5, color=DARK_GRID)

        # Draw execution blocks for each process
        timeline_entries = self.simulation.get_timeline_entries()

        # Draw each timeline entry
        for entry in timeline_entries:
            process, start_t, end_t = entry
            try:
                process_idx = processes.index(process)
            except ValueError:
                continue # Skip if process not found (e.g., added and removed quickly?)

            color = self.process_colors.get(process.pid, (0.5, 0.5, 0.5)) # Default color if not found

            # Create a rectangle for this execution block
            rect = patches.Rectangle(
                (start_t, process_idx - 0.4),  # (x, y)
                end_t - start_t,              # width
                0.8,                               # height
                linewidth=0.5, # Thinner border
                edgecolor=DARK_FG, # Light border for visibility
                facecolor=color,
                alpha=0.9, # Slightly more opaque
                label=process.name
            )
            self.ax.add_patch(rect)

            # Store rectangle for tooltip
            self.gantt_bars.append((rect, process, start_t, end_t))

        # Draw current time marker
        self.ax.axvline(x=current_time, color='red', linestyle='-', linewidth=1.5)

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
        if not self.gantt_bars or event.xdata is None or event.ydata is None:
            self.tooltip.place_forget()
            return

        # Check if mouse is over any gantt bar
        for rect, process, start, end in self.gantt_bars:
            # Use contains which checks data coordinates
            contains, _ = rect.contains(event)
            if contains:
                # Convert canvas coordinates to window coordinates
                x, y = self.canvas_widget.winfo_pointerxy() # Get mouse position relative to screen
                root_x = self.winfo_toplevel().winfo_rootx() # Get window top-left x
                root_y = self.winfo_toplevel().winfo_rooty() # Get window top-left y

                # Calculate tooltip position relative to the window
                tooltip_x = x - root_x + 10
                tooltip_y = y - root_y + 10

                # Create tooltip text
                text = (f"Process: {process.name} (PID: {process.pid})\n"
                        f"Time: {start:.2f} to {end:.2f}\n"
                        f"Duration: {end - start:.2f}")

                # Update and show tooltip
                self.tooltip.configure(text=text)
                # Place relative to the main SimulationScreen frame
                self.tooltip.place(x=tooltip_x, y=tooltip_y)
                return

        # If not over any bar, hide tooltip
        self.tooltip.place_forget()

    def _update_controls(self):
        """Update the enabled/disabled state of controls based on simulation state."""
        simulation_exists = self.simulation is not None
        simulation_running = simulation_exists and self.simulation.running
        simulation_paused = simulation_exists and self.simulation.paused
        has_processes = simulation_exists and self.scheduler and len(self.scheduler.processes) > 0
        has_results = simulation_exists and self.simulation.has_results()

        # Update button states in Controls Tab
        self.start_button.configure(state="normal" if (simulation_exists and has_processes and not simulation_running) else "disabled")
        self.pause_button.configure(state="normal" if simulation_running and not simulation_paused else "disabled")
        self.stop_button.configure(state="normal" if simulation_running or simulation_paused else "disabled")
        self.reset_button.configure(state="normal" if simulation_exists else "disabled")

        # Update Add Process Tab button state
        self.add_live_button.configure(state="normal" if simulation_running else "disabled")

        # Update Export Tab button state
        self.export_button.configure(state="normal" if has_results else "disabled")

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