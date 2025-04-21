import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import csv
import os
from typing import List, Dict, Callable, Any
from ..models.process import Process
from ..algorithms.fcfs import FCFSScheduler
from ..algorithms.sjf_preemptive import SJFPreemptiveScheduler
from ..algorithms.sjf_non_preemptive import SJFNonPreemptiveScheduler
from ..algorithms.priority_preemptive import PriorityPreemptiveScheduler
from ..algorithms.priority_non_preemptive import PriorityNonPreemptiveScheduler
from ..algorithms.round_robin import RoundRobinScheduler

class SchedulerConfigFrame(ctk.CTkFrame):
    """
    Configuration screen for setting up the CPU scheduler.
    """
    
    def __init__(self, master, switch_to_simulation):
        """
        Initialize the configuration screen.
        
        Args:
            master: The parent widget
            switch_to_simulation: Callback function to switch to simulation screen
        """
        super().__init__(master)
        self.master = master
        self.switch_to_simulation = switch_to_simulation
        
        # Initialize variables
        self.processes = []
        self.next_pid = 1
        
        # Configure grid with two main columns
        self.grid_columnconfigure(0, weight=1)  # Left column
        self.grid_columnconfigure(1, weight=1)  # Right column
        
        # Create left and right frames
        left_frame = ctk.CTkFrame(self)
        left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        right_frame = ctk.CTkFrame(self)
        right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        # Configure left frame (Scheduler selection)
        left_frame.grid_columnconfigure(0, weight=1)
        
        # Scheduler selection section
        ctk.CTkLabel(left_frame, text="Select Scheduling Algorithm", font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        
        # Scheduler options
        self.scheduler_var = tk.StringVar(value="FCFS")
        
        # Dictionary of scheduler types and their UI labels
        self.scheduler_types = {
            "FCFS": "First-Come, First-Served (FCFS)",
            "SJF-NP": "Shortest Job First (Non-Preemptive)",
            "SJF-P": "Shortest Job First (Preemptive)",
            "Priority-NP": "Priority (Non-Preemptive)",
            "Priority-P": "Priority (Preemptive)",
            "RR": "Round Robin"
        }
        
        # Create scheduler selection radio buttons
        for i, (key, value) in enumerate(self.scheduler_types.items()):
            ctk.CTkRadioButton(left_frame, text=value, variable=self.scheduler_var, value=key,
                             command=self.update_process_form).grid(row=i+1, column=0, padx=20, pady=5, sticky="w")
        
        # Time Quantum for Round Robin
        self.quantum_frame = ctk.CTkFrame(left_frame)
        self.quantum_frame.grid(row=7, column=0, padx=10, pady=10, sticky="ew")
        self.quantum_frame.grid_columnconfigure(0, weight=1)
        self.quantum_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(self.quantum_frame, text="Time Quantum:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.quantum_var = tk.StringVar(value="2")
        self.quantum_entry = ctk.CTkEntry(self.quantum_frame, width=60, textvariable=self.quantum_var)
        self.quantum_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Hide quantum frame initially (will show only for Round Robin)
        self.quantum_frame.grid_remove()
        
        # Add separator
        separator = ctk.CTkFrame(left_frame, height=2, fg_color="gray")
        separator.grid(row=8, column=0, padx=10, pady=10, sticky="ew")
        
        # Import/Export buttons
        btn_frame = ctk.CTkFrame(left_frame)
        btn_frame.grid(row=9, column=0, padx=10, pady=10, sticky="ew")
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkButton(btn_frame, text="Import Processes", command=self.import_processes).grid(
            row=0, column=0, padx=5, pady=5)
        ctk.CTkButton(btn_frame, text="Export Processes", command=self.export_processes).grid(
            row=0, column=1, padx=5, pady=5)
        
        # Start button
        ctk.CTkButton(left_frame, text="Start Simulation", font=ctk.CTkFont(size=16),
                     command=self.start_simulation, height=40).grid(
            row=10, column=0, padx=10, pady=(20, 10), sticky="ew")
        
        # Configure right frame (Process management)
        right_frame.grid_columnconfigure(0, weight=1)
        
        # Process management section
        ctk.CTkLabel(right_frame, text="Process Management", font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        
        # Process input form
        self.process_form_frame = ctk.CTkFrame(right_frame)
        self.process_form_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.setup_process_form()
        
        # Process list
        ctk.CTkLabel(right_frame, text="Current Processes", font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=2, column=0, padx=10, pady=(10, 5), sticky="w")
            
        # Process list display (using Treeview)
        self.tree_frame = ctk.CTkFrame(right_frame)
        self.tree_frame.grid(row=3, column=0, padx=10, pady=5, sticky="nsew")
        right_frame.grid_rowconfigure(3, weight=1)  # Make tree expand
        
        # Create Treeview inside a canvas for scrolling
        # Fix: Get the proper background color for the canvas
        # Get appearance mode first to avoid reference before assignment
        appearance_mode = ctk.get_appearance_mode().lower()
        
        # Use a specific string color value for the canvas background
        if appearance_mode == "dark":
            canvas_bg = "#2b2b2b"  # Dark background
        else:
            canvas_bg = "#ebebeb"  # Light background
            
        tree_canvas = ctk.CTkCanvas(self.tree_frame, highlightthickness=0, bg=canvas_bg)
        tree_canvas.pack(side="left", fill="both", expand=True)
        
        # Add a scrollbar
        scrollbar = ctk.CTkScrollbar(self.tree_frame, command=tree_canvas.yview)
        scrollbar.pack(side="right", fill="y")
        tree_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Create a frame inside the canvas for the treeview
        self.tree_view_frame = ctk.CTkFrame(tree_canvas)
        tree_canvas.create_window((0, 0), window=self.tree_view_frame, anchor="nw")
        
        # Configure the tree_view_frame
        self.tree_view_frame.bind("<Configure>", lambda e: tree_canvas.configure(scrollregion=tree_canvas.bbox("all")))
        self.tree_view_frame.grid_columnconfigure(0, weight=1)
        
        # Initialize empty process list
        self.update_process_list()
        
        # Button frame for process list actions
        btn_frame2 = ctk.CTkFrame(right_frame)
        btn_frame2.grid(row=4, column=0, padx=10, pady=10, sticky="ew")
        btn_frame2.grid_columnconfigure(0, weight=1)
        btn_frame2.grid_columnconfigure(1, weight=1)
        btn_frame2.grid_columnconfigure(2, weight=1)
        
        ctk.CTkButton(btn_frame2, text="Edit Selected", command=self.edit_process).grid(
            row=0, column=0, padx=5, pady=5)
        ctk.CTkButton(btn_frame2, text="Remove Selected", command=self.remove_selected_process).grid(
            row=0, column=1, padx=5, pady=5)
        ctk.CTkButton(btn_frame2, text="Clear All", command=self.clear_all_processes).grid(
            row=0, column=2, padx=5, pady=5)
    
    def setup_process_form(self):
        """Set up the process input form."""
        self.process_form_frame.grid_columnconfigure(0, weight=0)  # Label column
        self.process_form_frame.grid_columnconfigure(1, weight=1)  # Entry column
        
        # Process name
        ctk.CTkLabel(self.process_form_frame, text="Process Name:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.name_var = tk.StringVar()
        self.name_entry = ctk.CTkEntry(self.process_form_frame, textvariable=self.name_var)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Arrival time
        ctk.CTkLabel(self.process_form_frame, text="Arrival Time:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.arrival_var = tk.StringVar(value="0")
        self.arrival_entry = ctk.CTkEntry(self.process_form_frame, textvariable=self.arrival_var)
        self.arrival_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        # Burst time
        ctk.CTkLabel(self.process_form_frame, text="Burst Time:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.burst_var = tk.StringVar()
        self.burst_entry = ctk.CTkEntry(self.process_form_frame, textvariable=self.burst_var)
        self.burst_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        
        # Priority (only visible for priority schedulers)
        self.priority_label = ctk.CTkLabel(self.process_form_frame, text="Priority:")
        self.priority_label.grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.priority_var = tk.StringVar(value="0")
        self.priority_entry = ctk.CTkEntry(self.process_form_frame, textvariable=self.priority_var)
        self.priority_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        
        # Add process button
        ctk.CTkButton(self.process_form_frame, text="Add Process", command=self.add_process).grid(
            row=4, column=0, columnspan=2, padx=5, pady=10, sticky="ew")
        
        # Initialize form based on selected scheduler
        self.update_process_form()
    
    def update_process_form(self):
        """Update the process form fields based on selected scheduler."""
        scheduler_type = self.scheduler_var.get()
        
        # Show/hide priority field based on scheduler type
        if scheduler_type.startswith("Priority"):
            # Make priority field visible
            self.priority_label.grid()
            self.priority_entry.grid()
        else:
            # Hide priority field
            self.priority_label.grid_remove()
            self.priority_entry.grid_remove()
        
        # Show/hide quantum field based on scheduler type
        if scheduler_type == "RR":
            self.quantum_frame.grid()
        else:
            self.quantum_frame.grid_remove()
    
    def add_process(self):
        """Add a new process from form inputs."""
        try:
            # Validate inputs
            name = self.name_var.get().strip()
            if not name:
                name = f"P{self.next_pid}"
                
            arrival_time = int(self.arrival_var.get())
            burst_time = int(self.burst_var.get())
            
            # Validate burst time
            if burst_time <= 0:
                messagebox.showerror("Invalid Input", "Burst time must be greater than 0")
                return
                
            # Get priority if applicable
            priority = None
            if self.scheduler_var.get().startswith("Priority"):
                priority = int(self.priority_var.get())
            
            # Create and add process
            process = Process(
                pid=self.next_pid,
                name=name,
                arrival_time=arrival_time,
                burst_time=burst_time,
                priority=priority
            )
            
            self.processes.append(process)
            self.next_pid += 1
            
            # Clear form
            self.name_var.set("")
            self.arrival_var.set("0")
            self.burst_var.set("")
            self.priority_var.set("0")
            
            # Update process list
            self.update_process_list()
            
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numeric values for arrival time, burst time, and priority")
    
    def edit_process(self):
        """Edit the selected process."""
        # Find selected process
        selected_idx = self.get_selected_process_index()
        if selected_idx is None:
            messagebox.showinfo("No Selection", "Please select a process to edit")
            return
            
        process = self.processes[selected_idx]
        
        # Store the original PID to preserve it
        original_pid = process.pid
        
        # Fill form with process data
        self.name_var.set(process.name)
        self.arrival_var.set(str(process.arrival_time))
        self.burst_var.set(str(process.burst_time))
        if process.priority is not None:
            self.priority_var.set(str(process.priority))
        else:
            self.priority_var.set("0")
            
        # Create a custom button to save the edited process
        save_btn = self.process_form_frame.grid_slaves(row=4, column=0)[0]
        original_text = save_btn.cget("text")
        original_command = save_btn.cget("command")
        
        # Change the button to "Save Changes"
        save_btn.configure(
            text="Save Changes", 
            command=lambda: self.save_edited_process(selected_idx, original_pid, save_btn, original_text, original_command)
        )
    
    def save_edited_process(self, idx, original_pid, btn, original_text, original_command):
        """Save the edited process with the original PID."""
        try:
            # Validate inputs
            name = self.name_var.get().strip()
            if not name:
                name = f"P{original_pid}"
                
            arrival_time = int(self.arrival_var.get())
            burst_time = int(self.burst_var.get())
            
            # Validate burst time
            if burst_time <= 0:
                messagebox.showerror("Invalid Input", "Burst time must be greater than 0")
                return
                
            # Get priority if applicable
            priority = None
            if self.scheduler_var.get().startswith("Priority"):
                priority = int(self.priority_var.get())
            
            # Create process with the ORIGINAL PID
            process = Process(
                pid=original_pid,  # Keep the original PID
                name=name,
                arrival_time=arrival_time,
                burst_time=burst_time,
                priority=priority
            )
            
            # Insert at the same position or at the end if index is out of range
            if 0 <= idx < len(self.processes):
                self.processes[idx] = process
            else:
                self.processes.append(process)
            
            # Clear form
            self.name_var.set("")
            self.arrival_var.set("0")
            self.burst_var.set("")
            self.priority_var.set("0")
            
            # Reset button
            btn.configure(text=original_text, command=original_command)
            
            # Update process list
            self.update_process_list()
            
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numeric values for arrival time, burst time, and priority")
    
    def remove_selected_process(self):
        """Remove the selected process from the list."""
        selected_idx = self.get_selected_process_index()
        if selected_idx is None:
            messagebox.showinfo("No Selection", "Please select a process to remove")
            return
            
        self.processes.pop(selected_idx)
        self.update_process_list()
    
    def clear_all_processes(self):
        """Clear all processes from the list."""
        if not self.processes:
            return
            
        if messagebox.askyesno("Confirm", "Are you sure you want to remove all processes?"):
            self.processes.clear()
            self.next_pid = 1
            self.update_process_list()
    
    def get_selected_process_index(self):
        """Get the index of the selected process in the list."""
        # Get all children of the tree view frame
        children = self.tree_view_frame.winfo_children()
        if not children:
            return None
        
        # First child might be header, so skip it when looking for selected processes
        process_frames = []
        for child in children:
            # Skip any non-SelectableProcessFrame widgets (like headers or empty labels)
            if isinstance(child, SelectableProcessFrame):
                process_frames.append(child)
                
        # Now check which process frame is selected
        for i, frame in enumerate(process_frames):
            if frame.is_selected:
                return i
                
        return None
    
    def update_process_list(self):
        """Update the process list display."""
        # Remove all existing process frames
        for widget in self.tree_view_frame.winfo_children():
            widget.destroy()
        
        if not self.processes:
            # Show empty message
            empty_label = ctk.CTkLabel(self.tree_view_frame, text="No processes added yet")
            empty_label.grid(row=0, column=0, padx=10, pady=10)
            return
            
        # Create column headers
        header_frame = ctk.CTkFrame(self.tree_view_frame)
        header_frame.grid(row=0, column=0, padx=5, pady=(5, 0), sticky="ew")
        
        columns = ["PID", "Name", "Arrival", "Burst"]
        if any(p.priority is not None for p in self.processes):
            columns.append("Priority")
        
        # Configure header columns
        for i, col in enumerate(columns):
            header_frame.grid_columnconfigure(i, weight=1)
            ctk.CTkLabel(header_frame, text=col, font=ctk.CTkFont(weight="bold")).grid(
                row=0, column=i, padx=5, pady=2)
        
        # Add each process as a row
        for i, process in enumerate(self.processes):
            process_frame = SelectableProcessFrame(
                self.tree_view_frame, 
                process, 
                show_priority=any(p.priority is not None for p in self.processes),
                select_callback=self.process_selected
            )
            process_frame.grid(row=i+1, column=0, padx=5, pady=(0, 5), sticky="ew")
    
    def process_selected(self, selected_frame):
        """Handle process selection."""
        # Deselect all other processes
        for frame in self.tree_view_frame.winfo_children():
            if hasattr(frame, 'deselect') and frame != selected_frame:
                frame.deselect()
    
    def import_processes(self):
        """Import processes from a CSV file."""
        filepath = filedialog.askopenfilename(
            title="Import Processes",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        
        if not filepath:
            return
            
        try:
            with open(filepath, 'r', newline='') as file:
                reader = csv.reader(file)
                header = next(reader)
                
                # Check if header has required columns
                required_cols = ["Name", "Arrival Time", "Burst Time"]
                if not all(col in header for col in required_cols):
                    messagebox.showerror("Invalid File Format", 
                                         "CSV file must have columns: Name, Arrival Time, Burst Time")
                    return
                    
                # Get column indices
                name_idx = header.index("Name")
                arrival_idx = header.index("Arrival Time")
                burst_idx = header.index("Burst Time")
                
                # Check if Priority column exists
                priority_idx = None
                if "Priority" in header:
                    priority_idx = header.index("Priority")
                
                # Clear existing processes if any
                if self.processes and messagebox.askyesno(
                    "Existing Processes", "Replace existing processes with imported ones?"):
                    self.processes.clear()
                    self.next_pid = 1
                
                # Import processes
                for row in reader:
                    if len(row) >= 3:  # Make sure row has enough data
                        try:
                            name = row[name_idx].strip()
                            arrival_time = int(row[arrival_idx])
                            burst_time = int(row[burst_idx])
                            
                            priority = None
                            if priority_idx is not None and len(row) > priority_idx:
                                priority_val = row[priority_idx].strip()
                                if priority_val:
                                    priority = int(priority_val)
                            
                            process = Process(
                                pid=self.next_pid,
                                name=name if name else f"P{self.next_pid}",
                                arrival_time=arrival_time,
                                burst_time=burst_time,
                                priority=priority
                            )
                            
                            self.processes.append(process)
                            self.next_pid += 1
                        except ValueError:
                            # Skip invalid rows
                            continue
                
                # Update process list
                self.update_process_list()
                messagebox.showinfo("Import Complete", f"Successfully imported {len(self.processes)} processes.")
                
        except Exception as e:
            messagebox.showerror("Import Error", f"Error importing processes: {str(e)}")
    
    def export_processes(self):
        """Export processes to a CSV file."""
        if not self.processes:
            messagebox.showinfo("No Processes", "There are no processes to export.")
            return
            
        filepath = filedialog.asksaveasfilename(
            title="Export Processes",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        
        if not filepath:
            return
            
        try:
            with open(filepath, 'w', newline='') as file:
                writer = csv.writer(file)
                
                # Write header
                has_priority = any(p.priority is not None for p in self.processes)
                header = ["PID", "Name", "Arrival Time", "Burst Time"]
                if has_priority:
                    header.append("Priority")
                writer.writerow(header)
                
                # Write processes
                for process in self.processes:
                    row = [
                        process.pid, 
                        process.name, 
                        process.arrival_time, 
                        process.burst_time
                    ]
                    if has_priority:
                        row.append(process.priority if process.priority is not None else "")
                    writer.writerow(row)
                    
            messagebox.showinfo("Export Complete", f"Successfully exported {len(self.processes)} processes to {filepath}")
                
        except Exception as e:
            messagebox.showerror("Export Error", f"Error exporting processes: {str(e)}")
    
    def create_scheduler(self):
        """Create a scheduler instance based on the selected algorithm."""
        scheduler_type = self.scheduler_var.get()
        
        if scheduler_type == "FCFS":
            return FCFSScheduler()
        elif scheduler_type == "SJF-NP":
            return SJFNonPreemptiveScheduler()
        elif scheduler_type == "SJF-P":
            return SJFPreemptiveScheduler()
        elif scheduler_type == "Priority-NP":
            return PriorityNonPreemptiveScheduler()
        elif scheduler_type == "Priority-P":
            return PriorityPreemptiveScheduler()
        elif scheduler_type == "RR":
            # Get time quantum
            try:
                quantum = int(self.quantum_var.get())
                if quantum <= 0:
                    messagebox.showerror("Invalid Input", "Time quantum must be greater than 0")
                    return None
                return RoundRobinScheduler(quantum)
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter a valid time quantum")
                return None
        else:
            messagebox.showerror("Error", "Unknown scheduler type")
            return None
    
    def start_simulation(self):
        """Start the CPU scheduler simulation."""
        # Validate processes
        if not self.processes:
            messagebox.showinfo("No Processes", "Please add at least one process to simulate.")
            return
            
        # Create scheduler
        scheduler = self.create_scheduler()
        if not scheduler:
            return  # Error already displayed
            
        # Add processes to scheduler
        for process in self.processes:
            # Make a copy of the process to avoid modifying the original
            process_copy = Process(
                pid=process.pid,
                name=process.name,
                arrival_time=process.arrival_time,
                burst_time=process.burst_time,
                priority=process.priority
            )
            scheduler.add_process(process_copy)
            
        # Switch to simulation screen
        self.switch_to_simulation(scheduler)


class SelectableProcessFrame(ctk.CTkFrame):
    """A frame representing a selectable process in the process list."""
    
    def __init__(self, master, process, show_priority=False, select_callback=None):
        """
        Initialize the process frame.
        
        Args:
            master: The parent widget
            process: The Process object
            show_priority: Whether to display the priority column
            select_callback: Callback function when process is selected
        """
        super().__init__(master)
        self.process = process
        self.is_selected = False
        self.select_callback = select_callback
        
        # Configure grid
        columns = 4
        if show_priority:
            columns = 5
            
        for i in range(columns):
            self.grid_columnconfigure(i, weight=1)
        
        # Process details
        ctk.CTkLabel(self, text=str(process.pid)).grid(row=0, column=0, padx=5, pady=2)
        ctk.CTkLabel(self, text=process.name).grid(row=0, column=1, padx=5, pady=2)
        ctk.CTkLabel(self, text=str(process.arrival_time)).grid(row=0, column=2, padx=5, pady=2)
        ctk.CTkLabel(self, text=str(process.burst_time)).grid(row=0, column=3, padx=5, pady=2)
        
        if show_priority:
            priority_text = str(process.priority) if process.priority is not None else "-"
            ctk.CTkLabel(self, text=priority_text).grid(row=0, column=4, padx=5, pady=2)
        
        # Bind click event
        self.bind("<Button-1>", self.on_click)
        for child in self.winfo_children():
            child.bind("<Button-1>", self.on_click)
            
    def on_click(self, event):
        """Handle click event on the frame."""
        self.select()
        
    def select(self):
        """Select this process frame."""
        self.is_selected = True
        self.configure(fg_color=("gray75", "gray25"))
        if self.select_callback:
            self.select_callback(self)
            
    def deselect(self):
        """Deselect this process frame."""
        self.is_selected = False
        self.configure(fg_color=("gray90", "gray10"))