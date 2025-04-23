from PyQt6.QtWidgets import QWidget
from PyQt6 import uic
import os
from src.core.simulation import Simulation
import threading
class RunLiveScene(QWidget):
    # This class represents the live simulation scene in the GUI.
    
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
        self.gantt_process = None
        # Load the UI
        uic.loadUi(ui_file, self)
        
        # Initialize UI elements
        self.setup_ui()
    
    def setup_ui(self):
        # Connect signals
        self.addLiveProcessButton.clicked.connect(self.add_live_process)
        self.runLiveButton.clicked.connect(self.run_live)
        self.runAllButton.clicked.connect(self.run_all)
        self.pauseButton.clicked.connect(self.pause_simulation)  # Pause button
        self.returnToInputSceneButton.clicked.connect(self.return_to_input)    
        
    def add_live_process(self):
        """Add a live process to the simulation."""
        threading.Thread(target=add_process_thread, daemon=True).start()
            
        def add_process_thread():
            
            # Get the input values from the UI
            name = self.processNameInput.text()
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
            
            # Increment the next PID for the next process
            self.next_pid += 1
            
            # Clear the input fieldsets = 
            self.processNameInput.clear()
            self.burstTimeSpinBox.setValue(1)
            self.prioritySpinBox.setValue(0)
            
            # Turn off creating process flag
            self.creating_process = False
        

    def run_live(self):
        threading.Thread(target=run_live_thread, daemon=True).start()
        
        def run_live_thread():
            live_simulation = None
            
            while self.simulation.is_running() and self.simulation.is_paused():
                # Lock the simulation to prevent concurrent access
                with self.lock:
                    if not live_simulation:
                        live_simulation = self.simulation._run_simulation(True)  
                    try:   
                        current_process = next(live_simulation)
                    except StopIteration as e:
                        current_process = e.value
                
                # Update the Gantt chart with the current process
                with self.gantt_lock:
                    self.gantt_process = current_process
                    
                if self.simulation.scheduler.all_processes_completed():
                    # All processes are completed, stop the simulation
                    break

    def pause_simulation(self):
        """Pause the simulation."""
        if self.simulation.is_running():
            self.simulation.set_paused(not self.simulation.is_paused())
        
    
    def return_to_input(self):
        from src.GUI.process_input_scene import ProcessInputScene
        self.return_to_input_scene = ProcessInputScene()
        self.return_to_input_scene.show()
        self.close()  