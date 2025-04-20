from PyQt5.QtCore import QThread, pyqtSignal

class SimulationThread(QThread):
    """Thread for running the simulation without blocking the UI."""
    
    # Define signals for thread-safe UI updates
    process_updated = pyqtSignal(list, int)
    gantt_updated = pyqtSignal(object, int)
    stats_updated = pyqtSignal(float, float)
    
    def __init__(self, simulation):
        super().__init__()
        self.simulation = simulation
        
    def run(self):
        """Run the simulation."""
        # Connect simulation callbacks to our thread signals
        self.simulation.set_process_update_callback(self.process_updated.emit)
        self.simulation.set_gantt_update_callback(self.gantt_updated.emit)
        self.simulation.set_stats_update_callback(self.stats_updated.emit)
        
        # Start the simulation
        self.simulation.start()