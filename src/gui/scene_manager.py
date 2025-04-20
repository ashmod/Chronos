from PyQt5.QtWidgets import QStackedWidget

from .scenes.welcome_scene import WelcomeScene
from .scenes.process_input_scene import ProcessInputScene
from .scenes.simulation_scene import SimulationScene
from .scenes.results_scene import ResultsScene

class SceneManager(QStackedWidget):
    """
    Manager for scene-based navigation in the application.
    
    Handles the transitions between different scenes and passes data
    between them as needed.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize scenes
        self.scenes = {}
        self.current_scene_id = None
        self.scene_data = {}  # Data to pass between scenes
        
        # Create all scenes
        self._create_scenes()
        
        # Show the welcome scene by default
        self.show_scene("welcome")
        
    def _create_scenes(self):
        """Create and register all scenes."""
        # Create scenes
        self.scenes["welcome"] = WelcomeScene()
        self.scenes["process_input"] = ProcessInputScene()
        self.scenes["simulation"] = SimulationScene()
        self.scenes["results"] = ResultsScene()
        
        # Connect scene signals
        for scene_id, scene in self.scenes.items():
            scene.switch_scene.connect(lambda target, source=scene_id: 
                                      self.handle_scene_switch(source, target))
        
        # Connect special signals
        self.scenes["process_input"].proceed_with_processes.connect(
            self.scenes["simulation"].enter_scene
        )
        
        # Add scenes to the stacked widget
        for scene in self.scenes.values():
            self.addWidget(scene)
    
    def show_scene(self, scene_id, data=None):
        """
        Switch to the specified scene and pass data if provided.
        
        Args:
            scene_id (str): ID of the scene to show
            data (any): Data to pass to the scene
        """
        if scene_id not in self.scenes:
            return
            
        # Exit current scene if applicable
        if self.current_scene_id and self.current_scene_id in self.scenes:
            self.scenes[self.current_scene_id].exit_scene()
            
        # Update current scene ID
        self.current_scene_id = scene_id
        
        # Show the new scene
        scene = self.scenes[scene_id]
        self.setCurrentWidget(scene)
        
        # Pass data to the scene
        scene.enter_scene(data)
        
    def handle_scene_switch(self, source_id, target_id_with_data):
        """
        Handle a scene switch request.
        
        Args:
            source_id (str): ID of the source scene
            target_id_with_data (str): ID of the target scene with optional data
                                      format: "scene_id:data"
        """
        parts = target_id_with_data.split(":", 1)
        target_id = parts[0]
        
        # Extract data if provided
        data = parts[1] if len(parts) > 1 else None
        
        # Store data from source scene
        if source_id in self.scene_data:
            data_to_pass = self.scene_data[source_id]
            if data and target_id == "process_input":
                # For process_input, the data is a flag like "load" or "example"
                data_to_pass = data
        else:
            data_to_pass = data
            
        # Show the target scene
        self.show_scene(target_id, data_to_pass)
        
    def set_scene_data(self, scene_id, data):
        """
        Store data for a specific scene.
        
        Args:
            scene_id (str): ID of the scene
            data (any): Data to store
        """
        self.scene_data[scene_id] = data
        
    def set_dark_mode(self, enabled):
        """
        Set dark mode for all scenes.
        
        Args:
            enabled (bool): Whether dark mode should be enabled
        """
        for scene in self.scenes.values():
            scene.set_dark_mode(enabled)