from PyQt6.QtWidgets import QWidget, QTableWidgetItem, QHBoxLayout
from PyQt6 import uic
import os
from src.core.simulation import Simulation
from src.models.process import Process
import threading
from src.gui.ganttchart import GanttCanvas

class RunLiveScene(QWidget):
    """This class represents the live simulation scene in the gui."""
    
    def __init__(self,simulation: Simulation, next_pid: int):
        super().__init__()
        # Get the directory containing the UI file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ui_file = os.path.join(current_dir, "PyQtUI", "runLiveSceneUI.ui")
        # Initialize the attributes
        self.simulation: Simulation = simulation
        self.next_pid: int = next_pid
        self.lock = threading.Lock()
        self.gantt_lock = threading.Lock()
        # Load the UI
        uic.loadUi(ui_file, self)

        self.showMaximized()
        
        # Initialize UI elements
        self.setup_ui()
        
    
    def setup_ui(self):
        # Connect signals
        self.addLiveProcessButton.clicked.connect(self.add_live_process)
        self.runLiveButton.clicked.connect(self.run_live)
        self.pauseButton.clicked.connect(self.pause_simulation)  # Pause button
        self.returnToInputSceneButton.clicked.connect(self.return_to_input)
        
        # Create the canvas for the Gantt chart
        self.gantt_canvas = GanttCanvas(self)
        
        
        # Create a layout for the placeholder frame and add the canvas
        layout = QHBoxLayout(self.ganttPlaceHolder)
        layout.addWidget(self.gantt_canvas)
        self.ganttPlaceHolder.setLayout(layout)

        # Create table and populate it
        processes = self.simulation.scheduler.get_processes()
        self.processStatsTable.setRowCount(len(processes))
        for row, process in enumerate(processes):
            # Add a row for each process
            waiting_time = "N/A" 
            turnaround_time = "N/A" 
            response_time = "N/A" 
            completion_time = "N/A"

            
            # Add data to the table
            self.processStatsTable.setItem(row, 0, QTableWidgetItem(str(process.get_pid())))
            self.processStatsTable.setItem(row, 1, QTableWidgetItem(process.get_name()))
            self.processStatsTable.setItem(row, 2, QTableWidgetItem(str(process.get_arrival_time())))
            self.processStatsTable.setItem(row, 3, QTableWidgetItem(str(process.get_burst_time())))
            self.processStatsTable.setItem(row, 4, QTableWidgetItem(str(completion_time)))
            self.processStatsTable.setItem(row, 5, QTableWidgetItem(str(waiting_time)))
            self.processStatsTable.setItem(row, 6, QTableWidgetItem(str(turnaround_time)))
            self.processStatsTable.setItem(row, 7, QTableWidgetItem(str(response_time)))
        
    def add_live_process(self):
        """Add a live process to the simulation."""
            
        def add_process_thread():
            
            # Get the input values from the UI
            name = self.processNameTextBox.text()
            burst_time = int(self.burstTimeSpinBox.value())
            priority = int(self.prioritySpinBox.value())
            pid = self.next_pid
            
            with self.lock:
                # Create process and add it to the scheduler
                self.simulation.add_live_process(
                    pid=pid,
                    name=name,
                    burst_time=burst_time,
                    priority=priority,
                )
                
                # Add process to table
                row = self.processStatsTable.rowCount()
                self.processStatsTable.insertRow(row)
                self.processStatsTable.setItem(row, 0, QTableWidgetItem(str(pid)))
                self.processStatsTable.setItem(row, 1, QTableWidgetItem(name))
                self.processStatsTable.setItem(row, 2, QTableWidgetItem(str(self.simulation.scheduler.get_current_time())))  # Arrival time is always 0 for live processes
                self.processStatsTable.setItem(row, 3, QTableWidgetItem(str(burst_time)))
                self.processStatsTable.setItem(row, 4, QTableWidgetItem(str("N/A")))  # completion time is not available yet
                self.processStatsTable.setItem(row, 5, QTableWidgetItem("N/A"))  # Waiting time is not available yet
                self.processStatsTable.setItem(row, 6, QTableWidgetItem("N/A"))  # Turnaround time is not available yet
                self.processStatsTable.setItem(row, 7, QTableWidgetItem("N/A"))  # Response time is not available yet
            
            # Increment the next PID for the next process
            self.next_pid += 1
            
            # Clear the input fieldsets = 
            self.processNameTextBox.clear()
            self.burstTimeSpinBox.setValue(1)
            self.prioritySpinBox.setValue(0)
            
            # Turn off creating process flag
            self.creating_process = False
        
        threading.Thread(target=add_process_thread, daemon=True).start()

    def run_live(self):
        
        def run_live_thread():
            live_simulation = None
            self.simulation.start()
            
            while self.simulation.is_running() and not self.simulation.is_paused():
                print("Simulation is running.")
                # Lock the simulation to prevent concurrent access
                with self.lock:
                    print("Inside lock")
                    if not live_simulation:
                        live_simulation = self.simulation._run_simulation(True)  
                    try:   
                        current_process = next(live_simulation)
                        print("Try success")
                    except StopIteration as e:
                        current_process = e.value
                
                # Updates current process in the table
                print("Updating row")
                self.update_row_per_tick(current_process)
                # Update the Gantt chart with the current process
                with self.gantt_lock:
                    print("Updating Gantt chart")
                    self.simulation.processes_timeline.append(current_process)
                    self.update_gantt_chart()
                    
                if self.simulation.scheduler.all_processes_completed():
                    # All processes are completed, stop the simulation
                    print(*self.simulation.scheduler.get_processes())
                    break
                
        print("Starting live thread")        
        threading.Thread(target=run_live_thread, daemon=True).start()
        

    def pause_simulation(self):
        """Pause the simulation."""
        if self.simulation.is_running():
            self.simulation.set_paused(not self.simulation.is_paused())
        
    
    def return_to_input(self):
        from src.gui.process_input_scene import ProcessInputScene
        self.return_to_input_scene = ProcessInputScene()
        self.return_to_input_scene.show()
        self.close()  
        
        
    def update_row_per_tick(self, process:Process) -> None:
        """
        Update the process table with the current process information.
        """
        if process is None:
            return # No process to update
        
        pid:int = process.get_pid()
        # find row in table with the given pid
        for row in range(self.processStatsTable.rowCount()):
            if int(self.processStatsTable.item(row, 0).text()) == pid:
                # Update waiting time, turnaround time, and response time
                burst_time:int = process.get_remaining_time()
                self.processStatsTable.setItem(row, 3, QTableWidgetItem(str(burst_time)))
                
                if burst_time == 0:
                    waiting_time = process.get_waiting_time()
                    turnaround_time = process.get_turnaround_time()
                    response_time = process.get_response_time()
                    
                    self.processStatsTable.setItem(row, 4, QTableWidgetItem(str(process.get_completion_time())))
                    self.processStatsTable.setItem(row, 5, QTableWidgetItem(str(waiting_time)))
                    self.processStatsTable.setItem(row, 6, QTableWidgetItem(str(turnaround_time)))
                    self.processStatsTable.setItem(row, 7, QTableWidgetItem(str(response_time)))
                break

    def update_gantt_chart(self):
        """
        Update the Gantt chart with process execution timeline
        """
        if not self.simulation.processes_timeline:
            return
            
        # Use the plot_gantt_chart method from our GanttCanvas class
        self.gantt_canvas.plot_gantt_chart(self.simulation.processes_timeline)