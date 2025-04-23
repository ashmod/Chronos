from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from typing import List, Optional
from src.models.process import Process
import matplotlib.patches as patches
import numpy as np
from matplotlib.ticker import MaxNLocator


class GanttCanvas(FigureCanvasQTAgg):
    """
    A custom matplotlib canvas for displaying a Gantt chart of process execution.
    This component can be embedded in Qt applications.
    """
    
    def __init__(self, parent=None, width=8, height=4, dpi=100):
        """
        Initialize the GanttCanvas for the Gantt chart visualization.
        
        Args:
            parent: Parent widget
            width: Figure width in inches
            height: Figure height in inches
            dpi: Dots per inch (resolution)
        """
        # Create the figure and axis with a modern style
        plt.style.use('ggplot')  # Use a cleaner, more modern style
        
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor='#f8f9fa')
        self.axes = self.fig.add_subplot(111)
        
        # Set up the figure with tight layout for better appearance
        self.fig.tight_layout(pad=3.0)
        
        # Color palette for different processes - use a modern, vibrant palette
        self.colors = [
            '#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6',
            '#1abc9c', '#d35400', '#c0392b', '#16a085', '#8e44ad',
            '#27ae60', '#e67e22', '#2980b9', '#f1c40f', '#7f8c8d'
        ]
        
        # Process ID to color mapping
        self.process_colors = {}
        
        super().__init__(self.fig)
        self.setParent(parent)

    def plot_gantt_chart(self, process_timeline: List[Optional[Process]]):
        """
        Plot a Gantt chart showing the execution timeline of processes.
        
        Args:
            process_timeline: List of processes executed at each time step,
                             None indicates idle CPU time
        """
        # Clear any previous plots
        self.axes.clear()
        
        if not process_timeline:
            self.axes.set_title("No processes to display")
            self.draw()
            return
        
        # Create data structures for plotting
        timeline_length = len(process_timeline)
        
        # Group consecutive time slots with the same process
        segments = []
        current_process = None
        start_time = 0
        
        for t, process in enumerate(process_timeline):
            if process != current_process:
                if current_process is not None:
                    segments.append((current_process, start_time, t))
                current_process = process
                start_time = t
                
        # Add the last segment
        if current_process is not None:
            segments.append((current_process, start_time, timeline_length))
        
        # Assign colors to process IDs
        for process in process_timeline:
            if process and process.get_pid() not in self.process_colors:
                color_idx = len(self.process_colors) % len(self.colors)
                self.process_colors[process.get_pid()] = self.colors[color_idx]
        
        # Plot the segments as colored rectangles
        y_pos = 0
        y_height = 0.8  # Make bars thicker for better visibility
        
        # Store time markers for deduplication
        time_markers = set()
        
        for process, start, end in segments:
            if process is None:
                # Idle time - use light gray with a subtle pattern
                self.axes.barh(y_pos, end - start, height=y_height, left=start, 
                              color='#f5f5f5', edgecolor='#d9d9d9', 
                              alpha=0.7, hatch='////', zorder=1)
                
                # Label in the center of idle segment
                if end - start > 1:
                    self.axes.text((start + end) / 2, y_pos, "Idle", 
                                  ha='center', va='center', color='#555',
                                  fontsize=10, fontweight='normal', zorder=3)
            else:
                # Process execution - use the assigned color
                pid = process.get_pid()
                base_color = self.process_colors.get(pid, '#3498db')
                
                # Create a rectangle with rounded corners
                # Using Rectangle with rounded corners instead of FancyBboxPatch for better compatibility
                rect = self.axes.barh(y_pos, end - start, height=y_height, left=start,
                                     color=base_color, edgecolor='black', 
                                     linewidth=1, alpha=0.85, zorder=2)
                
                # Add process info as text in the middle of the segment
                if end - start > 1:
                    pname = process.get_name()
                    display_name = f"{pname} (P{pid})" if end - start > 4 else f"P{pid}"
                    self.axes.text((start + end) / 2, y_pos, display_name,
                                 ha='center', va='center', color='white',
                                 fontweight='bold', fontsize=10, zorder=5)
                
                # Add initial and final time markers
                time_markers.add(start)
                time_markers.add(end)
                
                # Draw vertical lines at segment boundaries with time labels
                for t in [start, end]:
                    self.axes.axvline(x=t, color='#34495e', linestyle='-', 
                                     alpha=0.5, linewidth=0.8, zorder=1)
                    
                # Add small tick marks at the bottom for each segment boundary
                for t in [start, end]:
                    self.axes.plot([t, t], [-0.5, -0.3], color='#34495e', 
                                  linewidth=1.5, zorder=4)
        
        # Add a legend with modern styling
        legend_patches = []
        process_ids = set()
        for process in process_timeline:
            if process is not None:
                process_ids.add(process.get_pid())
                
        for pid in sorted(process_ids):
            color = self.process_colors.get(pid, '#3498db')
            name = next((p.get_name() for p in process_timeline if p and p.get_pid() == pid), f"P{pid}")
            legend_patch = patches.Patch(
                facecolor=color, edgecolor='black', 
                label=f"{name} (ID: {pid})", alpha=0.85
            )
            legend_patches.append(legend_patch)
            
        # Add idle time to legend if present
        if any(p is None for p in process_timeline):
            idle_patch = patches.Patch(
                facecolor='#f5f5f5', edgecolor='#d9d9d9',
                label='Idle', hatch='////', alpha=0.7
            )
            legend_patches.append(idle_patch)
        
        # Place legend below the chart
        if legend_patches:
            self.axes.legend(
                handles=legend_patches, loc='upper center',
                bbox_to_anchor=(0.5, -0.12), ncol=min(4, len(legend_patches)),
                frameon=True, fancybox=True, shadow=True
            )
        
        # Set chart title with custom styling
        self.axes.set_title(
            "CPU Process Scheduling Gantt Chart", 
            fontsize=14, fontweight='bold', pad=15,
            color='#2c3e50'
        )
        
        # Set x-axis labels with custom styling
        self.axes.set_xlabel(
            "Time Units", fontsize=10, fontweight='bold',
            color='#2c3e50', labelpad=10
        )
        
        # Hide y-axis ticks and labels for cleaner appearance
        self.axes.set_yticks([])
        self.axes.set_ylabel("")
        
        # Set x-axis limits with some padding
        self.axes.set_xlim(-0.5, timeline_length + 0.5)
        self.axes.set_ylim(-0.5, 0.5)
        
        # Add grid lines for better readability
        self.axes.grid(axis='x', linestyle='--', alpha=0.3, color='#7f8c8d')
        
        # Add all time markers to x-axis ticks, plus start and end points
        time_markers.add(0)
        time_markers.add(timeline_length)
        
        # Make sure we don't have too many ticks if timeline is long
        if timeline_length > 20:
            # For long timelines, use MaxNLocator to limit the number of ticks
            self.axes.xaxis.set_major_locator(MaxNLocator(nbins=20, integer=True))
        else:
            # For shorter timelines, show all time markers
            self.axes.set_xticks(sorted(list(time_markers)))
        
        # Style the x-axis ticks and labels
        for tick in self.axes.get_xticklabels():
            tick.set_fontsize(9)
        
        # Add a subtle background grid
        self.axes.set_facecolor('#f8f9fa')
        
        # Add average metrics as text on the chart if available
        processes = [p for p in process_timeline if p is not None]
        if processes:
            unique_processes = {p.get_pid(): p for p in processes if p.is_completed()}
            if unique_processes:
                metrics_text = []
                
                # Calculate average metrics from completed processes
                completed = list(unique_processes.values())
                if completed:
                    avg_wait = sum(p.get_waiting_time() for p in completed) / len(completed)
                    avg_turnaround = sum(p.get_turnaround_time() for p in completed) / len(completed)
                    
                    metrics_text.append(f"Avg. Waiting Time: {avg_wait:.1f}")
                    metrics_text.append(f"Avg. Turnaround Time: {avg_turnaround:.1f}")
                    
                    # Add metrics text box
                    if metrics_text:
                        self.axes.text(
                            timeline_length + 0.5, 0, '\n'.join(metrics_text),
                            ha='right', va='top', fontsize=8,
                            bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.7),
                            transform=self.axes.transData
                        )
        
        # Adjust layout
        self.fig.tight_layout()
        
        # Ensure legend fits within figure bounds
        if legend_patches:
            self.fig.subplots_adjust(bottom=0.2)
            
        self.draw()

    def save_chart(self, filename):
        """
        Save the Gantt chart to a file.
        
        Args:
            filename: Path to save the file
        """
        self.fig.savefig(filename, bbox_inches='tight', dpi=300)