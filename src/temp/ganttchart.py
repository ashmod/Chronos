import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import numpy as np
import matplotlib.pyplot as plt

class GanttCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)
        
    def plot_gantt(self, processes_timeline):
        """
        Plot the Gantt chart with process execution timeline
        Args:
            processes_timeline: List of tuples (time, process_id, process_name)
        """
        self.axes.clear()
        
        if not processes_timeline:
            return
            
        # Extract unique process IDs and create a color map
        unique_processes = list(set(p[1] for p in processes_timeline))
        colors = plt.cm.get_cmap('tab20')(np.linspace(0, 1, len(unique_processes)))
        color_map = dict(zip(unique_processes, colors))
        
        # Create bars for each process execution
        for i in range(len(processes_timeline) - 1):
            process_id = processes_timeline[i][1]
            start_time = processes_timeline[i][0]
            end_time = processes_timeline[i + 1][0]
            
            if process_id != -1:  # -1 indicates idle time
                self.axes.barh(y=0, width=end_time - start_time, 
                             left=start_time, color=color_map[process_id],
                             label=f'P{process_id}')
                
                # Add process ID text in the middle of each bar
                self.axes.text(start_time + (end_time - start_time)/2, 0,
                             f'P{process_id}', ha='center', va='center')
        
        # Customize the chart
        self.axes.set_yticks([])
        self.axes.set_xlabel('Time')
        self.axes.set_title('Process Execution Timeline')
        
        # Add legend with unique processes
        handles = [plt.Rectangle((0,0),1,1, color=color_map[pid]) 
                  for pid in unique_processes]
        labels = [f'Process {pid}' for pid in unique_processes]
        self.axes.legend(handles, labels, loc='upper center', 
                        bbox_to_anchor=(0.5, -0.1), ncol=3)
        
        # Adjust layout to prevent label cutoff
        self.figure.tight_layout()
        
        # Refresh the canvas
        self.draw()