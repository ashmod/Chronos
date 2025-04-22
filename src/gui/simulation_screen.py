import threading
import tkinter as tk
import customtkinter as ctk
from tkinter import ttk, messagebox
import time
import colorsys
import csv
import random
from ..core.simulation import Simulation
from ..models.process import Process

# Define modern theme colors
DARK_BG = "#1E1E2E"           # Dark background
DARK_FG = "#CDD6F4"           # Light text color
DARK_GRID = "#313244"         # Grid lines color
DARK_AXES = "#45475A"         # Header/axes color
DARK_HIGHLIGHT = "#89B4FA"    # Selection highlight
DARK_TOOLTIP_BG = "#313244"   # Tooltip background
DARK_TOOLTIP_FG = "#CDD6F4"   # Tooltip text
ACCENT_COLOR = "#F5C2E7"      # Accent color for active items
PROCESS_BASE_COLOR = "#94E2D5" # Base color for processes

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
        self.timeline_entries = []
        self.current_time_marker = None
        self.gantt_cells = {}

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

        # Set up the redesigned Gantt chart
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
        """Set up a simplified timeline visualization to replace the traditional Gantt chart."""
        gantt_frame = ctk.CTkFrame(parent)
        gantt_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=(0, 5))
        gantt_frame.columnconfigure(0, weight=1)
        gantt_frame.rowconfigure(0, weight=0)  # Title
        gantt_frame.rowconfigure(1, weight=1)  # Timeline content

        # Timeline title with zoom and navigation controls
        title_frame = ctk.CTkFrame(gantt_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 2))
        title_frame.columnconfigure(0, weight=1)  # Title
        title_frame.columnconfigure(1, weight=0)  # Controls

        # Title
        title_label = ctk.CTkLabel(title_frame, text="CPU Execution Timeline", 
                                  font=("Segoe UI", 14, "bold"))
        title_label.grid(row=0, column=0, sticky="w")
        
        # Controls container frame 
        controls_frame = ctk.CTkFrame(title_frame, fg_color="transparent")
        controls_frame.grid(row=0, column=1, sticky="e")
        
        # Horizontal navigation frame (NEW)
        nav_frame = ctk.CTkFrame(controls_frame, fg_color=DARK_BG)
        nav_frame.grid(row=0, column=0, padx=(0, 10))
        
        # Jump to start button
        start_btn = ctk.CTkButton(nav_frame, text="⏮", width=30, height=30,
                                command=self._scroll_to_start, corner_radius=5)
        start_btn.grid(row=0, column=0, padx=2)
        
        # Scroll left button
        left_btn = ctk.CTkButton(nav_frame, text="◀", width=30, height=30, 
                               command=self._scroll_left, corner_radius=5)
        left_btn.grid(row=0, column=1, padx=2)
        
        # Scroll right button
        right_btn = ctk.CTkButton(nav_frame, text="▶", width=30, height=30,
                                command=self._scroll_right, corner_radius=5)
        right_btn.grid(row=0, column=2, padx=2)
        
        # Jump to end button
        end_btn = ctk.CTkButton(nav_frame, text="⏭", width=30, height=30,
                              command=self._scroll_to_end, corner_radius=5)
        end_btn.grid(row=0, column=3, padx=2)
        
        # Center view button (to current time)
        center_btn = ctk.CTkButton(nav_frame, text="⌖", width=30, height=30,
                                 command=self._center_time_marker, corner_radius=5)
        center_btn.grid(row=0, column=4, padx=2)
        
        # Zoom control frame
        zoom_frame = ctk.CTkFrame(controls_frame, fg_color=DARK_BG)
        zoom_frame.grid(row=0, column=1)
        
        # Zoom out button
        zoom_out_btn = ctk.CTkButton(zoom_frame, text="-", width=30, height=30, 
                                   command=self._zoom_out_gantt, corner_radius=5)
        zoom_out_btn.grid(row=0, column=0, padx=2)
        
        # Zoom in button
        zoom_in_btn = ctk.CTkButton(zoom_frame, text="+", width=30, height=30,
                                  command=self._zoom_in_gantt, corner_radius=5)
        zoom_in_btn.grid(row=0, column=1, padx=2)
        
        # Reset zoom button
        reset_zoom_btn = ctk.CTkButton(zoom_frame, text="↺", width=30, height=30,
                                     command=self._reset_zoom_gantt, corner_radius=5)
        reset_zoom_btn.grid(row=0, column=2, padx=2)

        # Create a frame for the timeline with scrollbars
        table_container = ctk.CTkFrame(gantt_frame)
        table_container.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        table_container.columnconfigure(0, weight=1)
        table_container.rowconfigure(0, weight=1)

        # Create a canvas for scrolling with improved configuration
        self.gantt_canvas = tk.Canvas(table_container, bg=DARK_BG, highlightthickness=0)
        
        # Scrollbars with enhanced interaction
        h_scrollbar = ctk.CTkScrollbar(table_container, orientation="horizontal", 
                                      command=self.gantt_canvas.xview)
        v_scrollbar = ctk.CTkScrollbar(table_container, orientation="vertical", 
                                      command=self.gantt_canvas.yview)
        
        self.gantt_canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        
        # Place elements
        self.gantt_canvas.grid(row=0, column=0, sticky="nsew")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")

        # Create a frame inside the canvas for the timeline content
        self.gantt_content = ctk.CTkFrame(self.gantt_canvas, fg_color=DARK_BG)
        self.gantt_canvas_window = self.gantt_canvas.create_window(
            (0, 0), window=self.gantt_content, anchor="nw"
        )

        # Bind canvas resize to update scroll region
        self.gantt_canvas.bind("<Configure>", self._on_canvas_configure)
        self.gantt_content.bind("<Configure>", self._on_content_configure)
        
        # Add enhanced mouse wheel scrolling capabilities
        self.gantt_canvas.bind("<MouseWheel>", self._on_mousewheel_y)  # Windows/MacOS vertical scroll
        self.gantt_canvas.bind("<Shift-MouseWheel>", self._on_mousewheel_x)  # Horizontal scroll with Shift
        self.gantt_canvas.bind("<Button-4>", self._on_mousewheel_y)  # Linux scroll up
        self.gantt_canvas.bind("<Button-5>", self._on_mousewheel_y)  # Linux scroll down
        self.gantt_canvas.bind("<Shift-Button-4>", self._on_mousewheel_x)  # Linux horizontal scroll
        self.gantt_canvas.bind("<Shift-Button-5>", self._on_mousewheel_x)  # Linux horizontal scroll
        
        # Add drag-to-scroll capability
        self.gantt_canvas.bind("<ButtonPress-1>", self._start_drag_scroll)
        self.gantt_canvas.bind("<B1-Motion>", self._do_drag_scroll)
        
        # Add keyboard navigation for the canvas
        self.gantt_canvas.bind("<Key-Left>", lambda e: self.gantt_canvas.xview_scroll(-1, "units"))
        self.gantt_canvas.bind("<Key-Right>", lambda e: self.gantt_canvas.xview_scroll(1, "units"))
        self.gantt_canvas.bind("<Key-Up>", lambda e: self.gantt_canvas.yview_scroll(-1, "units"))
        self.gantt_canvas.bind("<Key-Down>", lambda e: self.gantt_canvas.yview_scroll(1, "units"))
        self.gantt_canvas.bind("<Key-Page_Up>", lambda e: self.gantt_canvas.yview_scroll(-5, "units"))
        self.gantt_canvas.bind("<Key-Page_Down>", lambda e: self.gantt_canvas.yview_scroll(5, "units"))
        self.gantt_canvas.bind("<Key-Home>", lambda e: self.gantt_canvas.xview_moveto(0))
        self.gantt_canvas.bind("<Key-End>", lambda e: self.gantt_canvas.xview_moveto(1))
        
        # Make the canvas focusable to enable keyboard navigation
        self.gantt_canvas.config(takefocus=1)
        
        # Create tooltip for hovering over timeline segments
        self.tooltip = ctk.CTkLabel(
            self, text="", corner_radius=6, 
            fg_color=DARK_TOOLTIP_BG, text_color=DARK_TOOLTIP_FG
        )
        
        # Initialize zoom level
        self.gantt_zoom_level = 1.0
        self.gantt_cell_width = 40  # Base width
        self.gantt_row_height = 35   # Base height
        
        # Horizontal scroll state - for smoother continuous scrolling
        self.h_scroll_active = False
        self.h_scroll_direction = 0
        self.h_scroll_after_id = None
        
        # Drag scroll state
        self._drag_scroll_x = 0
        self._drag_scroll_y = 0
        
        # Initialize the timeline visualization
        self._init_gantt_chart(time_units=30)

    def _on_canvas_configure(self, event):
        """Handle canvas resizing to update the inner frame width."""
        # Update the width of the inner frame to match the canvas
        # This helps with horizontal scrolling when content is smaller than canvas
        canvas_width = event.width
        content_width = self.gantt_content.winfo_reqwidth()
        
        # Set the inner frame width to be at least the canvas width
        # This prevents the scrollbar from disappearing when content is narrow
        new_width = max(canvas_width, content_width)
        self.gantt_canvas.itemconfig(self.gantt_canvas_window, width=new_width)
        
        # Update scroll region after adjusting width
        self._on_content_configure(None) # Pass None as event is not needed here

    def _on_content_configure(self, event):
        """Update the scroll region when the content size changes."""
        if self.gantt_canvas:
            # Use bbox("all") to get the bounding box of all items in the canvas
            scroll_region = self.gantt_canvas.bbox("all")
            if scroll_region:
                self.gantt_canvas.configure(scrollregion=scroll_region)
            else:
                # Handle case where canvas is empty
                self.gantt_canvas.configure(scrollregion=(0, 0, 0, 0))

    def _init_gantt_chart(self, time_units=30, max_display_processes=8):
        """Initialize an empty timeline visualization with modern styling and continuous cells."""
        # Clear any existing content
        for widget in self.gantt_content.winfo_children():
            widget.destroy()
        
        self.gantt_cells = {}
        self.timeline_entries = []
        
        # Set a proper background for the gantt content area
        self.gantt_content.configure(fg_color=DARK_BG)
        
        # Calculate dynamic cell width based on zoom
        time_cell_width = int(self.gantt_cell_width * self.gantt_zoom_level)
        row_height = int(self.gantt_row_height) # Keep row height constant for now
        
        # Configure the grid with fixed size cells - ensure predictable layout
        process_col_width = 150 # Fixed width for process names
        self.gantt_content.columnconfigure(0, weight=0, minsize=process_col_width)
        
        # Set up time unit columns - start from 1 instead of 0
        for i in range(1, time_units + 1):
            # Fixed width columns with no weight to prevent stretching
            self.gantt_content.columnconfigure(i, weight=0, minsize=time_cell_width)
            
            # Add time labels with improved styling - show i instead of i-1 to start from 1
            time_label = ctk.CTkLabel(
                self.gantt_content, 
                text=str(i), 
                width=time_cell_width, 
                height=25, 
                fg_color=DARK_AXES, 
                text_color=DARK_FG,
                corner_radius=0,
                font=("Segoe UI", 10)
            )
            time_label.grid(row=0, column=i, sticky="nsew", padx=0, pady=0)
        
        # Process column header with improved styling
        header_label = ctk.CTkLabel(
            self.gantt_content, 
            text="Process", 
            width=process_col_width, 
            height=25, 
            fg_color=DARK_AXES,
            text_color=DARK_FG, 
            corner_radius=0,
            font=("Segoe UI", 10, "bold")
        )
        header_label.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        
        # Create empty row slots for processes with consistent styling
        for row in range(1, max_display_processes + 1):
            # Process name cell with improved styling - no padding
            process_label = ctk.CTkLabel(
                self.gantt_content, 
                text="", 
                width=process_col_width, 
                height=row_height, 
                fg_color=DARK_GRID,
                text_color=DARK_FG,
                corner_radius=0
            )
            process_label.grid(row=row, column=0, sticky="nsew", padx=0, pady=0)
            
            # Empty cells for time units - no padding for continuous display
            for col in range(1, time_units + 1):
                # Create a cell with fixed size and minimal borders
                cell = ctk.CTkFrame(
                    self.gantt_content,
                    width=time_cell_width, 
                    height=row_height,
                    fg_color=DARK_BG,
                    border_width=1,
                    border_color=DARK_GRID,
                    corner_radius=0
                )
                cell.grid(row=row, column=col, sticky="nsew", padx=0, pady=0)
                
                # Make sure the cell doesn't expand internally
                cell.grid_propagate(False)
                
                # Store cell reference in our tracking dictionary with adjusted time values
                if row not in self.gantt_cells:
                    self.gantt_cells[row] = {}
                self.gantt_cells[row][col] = {
                    'widget': cell,
                    'process': None,
                    'start': col,  # Time now starts at 1 (col instead of col-1)
                    'end': col + 1
                }
                
                # Improved tooltip behavior
                cell.bind("<Enter>", lambda e, r=row, c=col: self._show_cell_tooltip(r, c, e))
                cell.bind("<Leave>", lambda e: self.tooltip.place_forget())

        # Current time marker (placeholder, will be created when simulation runs)
        self.current_time_marker = None
        
        # Initialize visible row indices for scrolling
        self.visible_start_row = 1
        self.max_visible_rows = max_display_processes
        
        # Update scroll region after initialization
        self.gantt_content.update_idletasks() # Ensure widgets are drawn
        self.gantt_canvas.configure(scrollregion=self.gantt_canvas.bbox("all"))

    def _expand_gantt_chart(self, new_time_units):
        """Expand the timeline to accommodate more time units."""
        current_columns = len(self.gantt_content.grid_slaves(row=0)) - 1  # Subtract process column
        if new_time_units <= current_columns:
            return
            
        # Calculate dynamic cell width based on zoom
        time_cell_width = int(self.gantt_cell_width * self.gantt_zoom_level)
        row_height = int(self.gantt_row_height)
        
        # Add new time columns
        for i in range(current_columns + 1, new_time_units + 1):
            # Fixed width columns with no weight to prevent stretching
            self.gantt_content.columnconfigure(i, weight=0, minsize=time_cell_width)
            
            # Add time label with consistent styling - no padding
            time_label = ctk.CTkLabel(
                self.gantt_content, 
                text=str(i), 
                width=time_cell_width, 
                height=25, 
                fg_color=DARK_AXES,
                text_color=DARK_FG,
                corner_radius=0,
                font=("Segoe UI", 10)
            )
            time_label.grid(row=0, column=i, sticky="nsew", padx=0, pady=0)
            
            # Add empty cells for each process row - no padding for continuous display
            for row in range(1, len(self.gantt_cells) + 1):
                cell = ctk.CTkFrame(
                    self.gantt_content,
                    width=time_cell_width, 
                    height=row_height,
                    fg_color=DARK_BG,
                    border_width=1,
                    border_color=DARK_GRID,
                    corner_radius=0
                )
                cell.grid(row=row, column=i, sticky="nsew", padx=0, pady=0)
                
                # Make sure the cell doesn't expand internally
                cell.grid_propagate(False)
                
                # Store cell reference with proper tracking info
                self.gantt_cells[row][i] = {
                    'widget': cell,
                    'process': None,
                    'start': i,
                    'end': i + 1
                }
                
                # Bind hover events for tooltip with the same behavior
                cell.bind("<Enter>", lambda e, r=row, c=i: self._show_cell_tooltip(r, c, e))
                cell.bind("<Leave>", lambda e: self.tooltip.place_forget())
        
        # Update scroll region after expansion
        self.gantt_content.update_idletasks() # Ensure widgets are drawn
        self.gantt_canvas.configure(scrollregion=self.gantt_canvas.bbox("all"))

    def _expand_process_rows(self, num_processes):
        """Expand the timeline visualization to accommodate more processes."""
        current_rows = len(self.gantt_cells)
        if num_processes <= current_rows:
            return
            
        # Calculate dynamic cell width based on zoom
        time_cell_width = int(self.gantt_cell_width * self.gantt_zoom_level)
        row_height = int(self.gantt_row_height)
        process_col_width = 150
        
        # Get number of columns
        columns = len(self.gantt_content.grid_slaves(row=0))
        
        # Add new rows for processes
        for row in range(current_rows + 1, num_processes + 1):
            # Process name cell with improved styling - no padding for continuous display
            process_label = ctk.CTkLabel(
                self.gantt_content, 
                text="", 
                width=process_col_width, 
                height=row_height, 
                fg_color=DARK_GRID,
                text_color=DARK_FG,
                corner_radius=0
            )
            process_label.grid(row=row, column=0, sticky="nsew", padx=0, pady=0)
            
            # Empty cells for time units - no padding for continuous display
            self.gantt_cells[row] = {}
            for col in range(1, columns):
                # Create a cell with consistent styling
                cell = ctk.CTkFrame(
                    self.gantt_content,
                    width=time_cell_width, 
                    height=row_height,
                    fg_color=DARK_BG,
                    border_width=1,
                    border_color=DARK_GRID,
                    corner_radius=0
                )
                cell.grid(row=row, column=col, sticky="nsew", padx=0, pady=0)
                
                # Make sure the cell doesn't expand internally
                cell.grid_propagate(False)
                
                # Store cell reference with proper tracking info
                self.gantt_cells[row][col] = {
                    'widget': cell,
                    'process': None,
                    'start': col,
                    'end': col + 1
                }
                
                # Bind hover events for tooltip with the same behavior
                cell.bind("<Enter>", lambda e, r=row, c=col: self._show_cell_tooltip(r, c, e))
                cell.bind("<Leave>", lambda e: self.tooltip.place_forget())
        
        # Update scroll region after expansion
        self.gantt_content.update_idletasks() # Ensure widgets are drawn
        self.gantt_canvas.configure(scrollregion=self.gantt_canvas.bbox("all"))
    
    # --- Gantt Chart Scrolling and Zooming Methods ---

    def _scroll_left(self, event=None):
        """Scroll the Gantt chart view to the left."""
        self.gantt_canvas.xview_scroll(-1, "units")

    def _scroll_right(self, event=None):
        """Scroll the Gantt chart view to the right."""
        self.gantt_canvas.xview_scroll(1, "units")

    def _scroll_to_start(self, event=None):
        """Scroll the Gantt chart view to the beginning (time 0)."""
        self.gantt_canvas.xview_moveto(0)

    def _scroll_to_end(self, event=None):
        """Scroll the Gantt chart view to the end."""
        self.gantt_canvas.xview_moveto(1)

    def _center_time_marker(self, event=None):
        """Scroll the Gantt chart to center the current time marker."""
        if not self.current_time_marker:
            return

        # Get the column index of the time marker
        marker_info = self.current_time_marker.grid_info()
        if not marker_info: return
        
        col = marker_info.get('column', 0)
        if col == 0: return # Should not happen if marker exists

        # Calculate the total number of columns (time units + process name col)
        total_cols = len(self.gantt_content.grid_slaves(row=0))
        if total_cols <= 1: return

        # Calculate the fraction to move to, aiming to center the column
        # Get canvas width in pixels and estimate visible columns
        canvas_width_px = self.gantt_canvas.winfo_width()
        cell_width_px = int(self.gantt_cell_width * self.gantt_zoom_level)
        process_col_width = 150
        
        # Estimate visible time columns (excluding process name column)
        visible_time_cols = (canvas_width_px - process_col_width) / cell_width_px if cell_width_px > 0 else 1
        
        # Calculate the target starting column to center the marker column
        target_start_col = max(1, col - (visible_time_cols / 2))
        
        # Calculate the fraction based on the target start column and total columns
        # We need to account for the width of the process name column
        total_content_width = process_col_width + (total_cols - 1) * cell_width_px
        target_x_pos = process_col_width + (target_start_col - 1) * cell_width_px
        
        fraction = target_x_pos / total_content_width if total_content_width > 0 else 0
        fraction = max(0, min(1, fraction)) # Clamp between 0 and 1

        self.gantt_canvas.xview_moveto(fraction)

    def _on_mousewheel_y(self, event):
        """Handle vertical mouse wheel scrolling."""
        # Determine scroll direction and amount
        if event.num == 5 or event.delta < 0:  # Scroll down (Linux/Windows)
            self.gantt_canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta > 0:  # Scroll up (Linux/Windows)
            self.gantt_canvas.yview_scroll(-1, "units")

    def _on_mousewheel_x(self, event):
        """Handle horizontal mouse wheel scrolling (Shift + Wheel)."""
        # Determine scroll direction and amount
        if event.num == 5 or event.delta < 0:  # Scroll right (Linux/Windows)
            self.gantt_canvas.xview_scroll(2, "units") # Scroll faster horizontally
        elif event.num == 4 or event.delta > 0:  # Scroll left (Linux/Windows)
            self.gantt_canvas.xview_scroll(-2, "units") # Scroll faster horizontally

    def _start_drag_scroll(self, event):
        """Record the starting position for drag scrolling."""
        self.gantt_canvas.focus_set() # Ensure canvas has focus for keyboard events too
        self.gantt_canvas.scan_mark(event.x, event.y)
        self._drag_scroll_x = event.x
        self._drag_scroll_y = event.y

    def _do_drag_scroll(self, event):
        """Perform drag scrolling based on mouse movement."""
        self.gantt_canvas.scan_dragto(event.x, event.y, gain=1)

    def _redraw_gantt_after_zoom(self):
        """Redraws the Gantt chart elements after a zoom level change."""
        if not self.gantt_cells:
            return

        # Calculate new dimensions
        new_cell_width = int(self.gantt_cell_width * self.gantt_zoom_level)
        new_row_height = int(self.gantt_row_height) # Keep height constant
        process_col_width = 150

        # Update column configurations
        self.gantt_content.columnconfigure(0, minsize=process_col_width)
        num_cols = len(self.gantt_content.grid_slaves(row=0))
        for col in range(1, num_cols):
            self.gantt_content.columnconfigure(col, minsize=new_cell_width)
            # Update time labels
            time_label = self.gantt_content.grid_slaves(row=0, column=col)[0]
            time_label.configure(width=new_cell_width)

        # Update process header label width
        header_label = self.gantt_content.grid_slaves(row=0, column=0)[0]
        header_label.configure(width=process_col_width)

        # Update cell sizes and process labels
        num_rows = len(self.gantt_cells)
        for row in range(1, num_rows + 1):
            # Update process label
            process_label = self.gantt_content.grid_slaves(row=row, column=0)[0]
            process_label.configure(width=process_col_width, height=new_row_height)

            # Update time cells
            if row in self.gantt_cells:
                for col in range(1, num_cols):
                    if col in self.gantt_cells[row]:
                        cell_info = self.gantt_cells[row][col]
                        cell_widget = cell_info['widget']
                        cell_widget.configure(width=new_cell_width, height=new_row_height)
                        # Re-apply color if process exists
                        if cell_info['process']:
                            process_color = self.process_colors.get(cell_info['process'].pid, PROCESS_BASE_COLOR)
                            cell_widget.configure(fg_color=process_color)
                        else:
                            cell_widget.configure(fg_color=DARK_BG) # Reset empty cells

        # Update the current time marker position and size if it exists
        if self.current_time_marker:
            marker_info = self.current_time_marker.grid_info()
            if marker_info:
                col = marker_info.get('column', 0)
                # Recalculate horizontal position based on new cell width
                # Place it in the correct column position, centered within the cell
                x_offset = (new_cell_width - 3) // 2 # Center the 3px wide marker
                self.current_time_marker.grid_configure(padx=(x_offset, 0))


        # Crucially, update the scroll region after resizing everything
        self.gantt_content.update_idletasks() # Wait for geometry updates
        self.gantt_canvas.configure(scrollregion=self.gantt_canvas.bbox("all"))

    def _zoom_in_gantt(self):
        """Zoom in on the Gantt chart timeline."""
        self.gantt_zoom_level = min(3.0, self.gantt_zoom_level * 1.2) # Limit max zoom
        self._redraw_gantt_after_zoom()

    def _zoom_out_gantt(self):
        """Zoom out on the Gantt chart timeline."""
        self.gantt_zoom_level = max(0.2, self.gantt_zoom_level / 1.2) # Limit min zoom
        self._redraw_gantt_after_zoom()

    def _reset_zoom_gantt(self):
        """Reset the Gantt chart zoom level to default."""
        self.gantt_zoom_level = 1.0
        self._redraw_gantt_after_zoom()

    # --- End Gantt Chart Scrolling and Zooming Methods ---

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
                  background=[('selected', DARK_HIGHLIGHT)], # Use a highlight color
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

    def _generate_process_colors(self, processes):
        """Generate distinct colors for each process."""
        # Initialize colors for processes
        for process in processes:
            if process.pid not in self.process_colors:
                # Generate color based on PID using HSV to ensure good contrast
                hue = (process.pid * 0.618033988749895) % 1.0  # Golden ratio
                saturation = 0.8
                value = 0.95
                rgb = colorsys.hsv_to_rgb(hue, saturation, value)
                # Convert to hex
                hex_color = f"#{int(rgb[0]*255):02x}{int(rgb[1]*255):02x}{int(rgb[2]*255):02x}"
                self.process_colors[process.pid] = hex_color

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

        # Generate colors for processes
        self._generate_process_colors(scheduler.processes)
        
        # Update the process table initially
        self._update_process_table(scheduler.processes, 0)
        
        # Initialize the Gantt chart with process names
        self._setup_initial_gantt_processes(scheduler.processes)

        # Enable/disable controls
        self._update_controls()

    def _setup_initial_gantt_processes(self, processes):
        """Set up initial process rows in the Gantt chart."""
        if not processes:
            return
            
        # Sort processes by PID
        processes_sorted = sorted(processes, key=lambda p: p.pid)
        
        # Ensure we have enough rows
        self._expand_process_rows(len(processes_sorted))
        
        # Update process labels
        for i, process in enumerate(processes_sorted):
            row = i + 1
            
            # Update the process label
            process_label = self.gantt_content.grid_slaves(row=row, column=0)[0]
            process_label.configure(
                text=f"{process.name} (PID: {process.pid})",
                fg_color=self.process_colors.get(process.pid, DARK_BG),
                text_color="black",
                font=("Segoe UI", 10, "bold")
            )
        
        # Initialize the timeline entries list
        self.timeline_entries = []
            
        # Update the scroll region
        self.gantt_canvas.configure(scrollregion=self.gantt_canvas.bbox("all"))

    def _update_process_table(self, processes, current_time):
        """Update the process table with current process information."""
        # Clear current table
        for item in self.process_table.get_children():
            self.process_table.delete(item)

        # Add colors for any new processes
        self._generate_process_colors(processes)

        # Sort processes by PID
        processes_sorted = sorted(processes, key=lambda p: p.pid)

        # Update the table
        for process in processes_sorted:
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
        """Update the timeline visualization with the current simulation state."""
        if not self.simulation or not self.scheduler:
            return

        # Get all processes sorted by PID
        processes = sorted(self.scheduler.processes, key=lambda p: p.pid)
        
        # Ensure we have enough rows and columns, considering zoom
        self._expand_process_rows(len(processes))
        # Expand time slightly beyond current time + buffer
        required_time_units = int(current_time) + 15 
        self._expand_gantt_chart(required_time_units)
        
        # Get timeline entries from simulation
        new_entries = self.simulation.get_timeline_entries()
        
        # Calculate dynamic cell width based on zoom
        time_cell_width = int(self.gantt_cell_width * self.gantt_zoom_level)
        
        # Update process labels if needed (ensure width is correct after zoom)
        process_col_width = 150
        for i, process in enumerate(processes):
            row = i + 1
            process_label = self.gantt_content.grid_slaves(row=row, column=0)[0]
            process_color = self.process_colors.get(process.pid, PROCESS_BASE_COLOR)
            process_label_text = f"{process.name}"
            if len(process.name) < 10:
                process_label_text += f" (PID: {process.pid})"
            
            process_label.configure(
                text=process_label_text,
                fg_color=process_color,
                text_color="#000000",
                font=("Segoe UI", 10, "bold"),
                corner_radius=4,
                width=process_col_width # Ensure width is maintained
            )
                
        # Process timeline entries that are new since last update
        if len(new_entries) > len(self.timeline_entries):
            for entry in new_entries[len(self.timeline_entries):]:
                process, start_t, end_t = entry
                process_idx = next((i + 1 for i, p in enumerate(processes) if p.pid == process.pid), None)
                if process_idx is None: continue
                
                process_color = self.process_colors.get(process.pid, PROCESS_BASE_COLOR)
                
                # Update cells for this execution block
                # Ensure start_t and end_t are integers for range
                start_col = int(start_t) + 1
                end_col = int(end_t) + 1 # Range goes up to, but not including end_col
                
                for col in range(start_col, end_col):
                    if process_idx not in self.gantt_cells or col not in self.gantt_cells[process_idx]:
                        # This might happen if chart wasn't expanded enough initially
                        # Try expanding again just in case
                        self._expand_gantt_chart(col + 5)
                        if col not in self.gantt_cells[process_idx]:
                            print(f"Warning: Gantt cell not found for P{process.pid} at time {col-1}")
                            continue # Skip if still not found

                    cell_info = self.gantt_cells[process_idx][col]
                    cell = cell_info['widget']
                    
                    # Update cell appearance
                    cell.configure(
                        fg_color=process_color,
                        border_width=0,
                        width=time_cell_width # Ensure width matches zoom
                    )
                    
                    # Add process execution label (only once for the block)
                    if col == start_col and (end_t - start_t) > (1.5 / self.gantt_zoom_level): # Show label if block is wide enough
                        # Clear any existing labels first
                        for widget in cell.winfo_children():
                            widget.destroy()
                        
                        ctk.CTkLabel(
                            cell,
                            text=f"P{process.pid}",
                            font=("Segoe UI", 9, "bold"),
                            text_color="#000000",
                            fg_color="transparent"
                        ).place(relx=0.5, rely=0.5, anchor="center")
                    elif not cell.winfo_children() and (end_t - start_t) <= (1.5 / self.gantt_zoom_level):
                        # Clear labels if block becomes too small due to zoom
                         for widget in cell.winfo_children():
                            widget.destroy()

                    # Update cell info for tooltip
                    cell_info['process'] = process
                    cell_info['start'] = start_t
                    cell_info['end'] = end_t
            
            self.timeline_entries = new_entries[:]
        
        # Update current time marker
        if self.current_time_marker:
            self.current_time_marker.destroy()
            self.current_time_marker = None
            
        # Add new marker if within visible range (check against actual columns)
        num_cols = len(self.gantt_content.grid_slaves(row=0))
        col_time = int(current_time) + 1 # Column index corresponding to current time
        
        if col_time < num_cols:
            self.current_time_marker = ctk.CTkFrame(
                self.gantt_content, 
                width=3,
                fg_color=ACCENT_COLOR,
                corner_radius=0
            )
            
            # Calculate horizontal position based on zoom
            x_offset = (time_cell_width - 3) // 2 # Center the 3px marker in the cell
            
            self.current_time_marker.grid(
                row=0, column=col_time, 
                rowspan=len(processes) + 1,
                sticky="nsw", # Stick to top, left, bottom
                padx=(x_offset, 0) # Apply offset for centering
            )
            self.current_time_marker.lift()
            
            # Auto-scroll to keep the time marker visible (optional, can be annoying)
            # self._ensure_time_marker_visible(col_time) 

        # Update scroll region after all updates
        self.gantt_content.update_idletasks()
        self.gantt_canvas.configure(scrollregion=self.gantt_canvas.bbox("all"))

    def _ensure_time_marker_visible(self, marker_col):
        """Scrolls the canvas horizontally if the time marker is out of view."""
        # Get current horizontal view fractions
        xview = self.gantt_canvas.xview()
        view_start_fraction = xview[0]
        view_end_fraction = xview[1]

        # Calculate total content width and marker position
        process_col_width = 150
        cell_width_px = int(self.gantt_cell_width * self.gantt_zoom_level)
        total_cols = len(self.gantt_content.grid_slaves(row=0))
        total_content_width = process_col_width + (total_cols - 1) * cell_width_px
        
        if total_content_width == 0: return # Avoid division by zero

        # Calculate the start and end x-coordinates of the marker column
        marker_start_x = process_col_width + (marker_col - 1) * cell_width_px
        marker_end_x = marker_start_x + cell_width_px

        # Calculate marker position as fractions of total width
        marker_start_fraction = marker_start_x / total_content_width
        marker_end_fraction = marker_end_x / total_content_width

        # Check if marker is out of view
        scroll_needed = False
        new_fraction = view_start_fraction

        if marker_end_fraction > view_end_fraction: # Marker is off the right edge
            # Scroll right to bring the end of the marker into view
            new_fraction = marker_end_fraction - (view_end_fraction - view_start_fraction)
            scroll_needed = True
        elif marker_start_fraction < view_start_fraction: # Marker is off the left edge
            # Scroll left to bring the start of the marker into view
            new_fraction = marker_start_fraction
            scroll_needed = True

        if scroll_needed:
            # Add a small buffer so it's not exactly at the edge
            buffer_fraction = (cell_width_px / total_content_width) * 1.5 
            if marker_end_fraction > view_end_fraction:
                 new_fraction += buffer_fraction # Add buffer when scrolling right
            else:
                 new_fraction -= buffer_fraction # Subtract buffer when scrolling left

            new_fraction = max(0, min(1 - (view_end_fraction - view_start_fraction), new_fraction)) # Clamp fraction
            
            self.gantt_canvas.xview_moveto(new_fraction)


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

        # Clear the Gantt chart
        self._init_gantt_chart(time_units=20)
        
        # Reset timeline entries
        self.timeline_entries = []
        
        # Restore process names
        self._setup_initial_gantt_processes(self.scheduler.processes)
        
        # Reset process table
        self._update_process_table(self.scheduler.processes, 0)
        
        # Reset stats
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
                    
                    # Make sure the new process is visible in the Gantt chart
                    self._setup_initial_gantt_processes(self.scheduler.processes)
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
                    for process in sorted(self.scheduler.processes, key=lambda p: p.pid):
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

                    for process in sorted(self.scheduler.processes, key=lambda p: p.pid):
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

    def _show_cell_tooltip(self, row, col, event):
        """Display tooltip for a Gantt chart cell."""
        if row not in self.gantt_cells or col not in self.gantt_cells[row]:
            return

        cell_info = self.gantt_cells[row][col]
        process = cell_info.get('process')
        start_time = cell_info.get('start')
        end_time = cell_info.get('end')

        tooltip_text = f"Time: {col-1}-{col}" # Time unit is col-1
        if process:
            tooltip_text += f"\nProcess: {process.name} (PID: {process.pid})"
            tooltip_text += f"\nExecuting: {start_time}-{end_time}"
        else:
            # Find the process name associated with this row
            process_label = self.gantt_content.grid_slaves(row=row, column=0)[0]
            process_name_text = process_label.cget("text")
            if process_name_text:
                 tooltip_text += f"\nProcess Row: {process_name_text}"
            tooltip_text += "\nStatus: Idle"


        self.tooltip.configure(text=tooltip_text)
        
        # Position tooltip near the mouse pointer
        # Adjust position slightly to avoid covering the cell itself
        x = event.x_root + 10 
        y = event.y_root + 10
        
        # Ensure tooltip stays within screen bounds (basic check)
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        tooltip_width = self.tooltip.winfo_reqwidth()
        tooltip_height = self.tooltip.winfo_reqheight()

        if x + tooltip_width > screen_width:
            x = screen_width - tooltip_width - 5
        if y + tooltip_height > screen_height:
            y = screen_height - tooltip_height - 5
            
        self.tooltip.place(x=x, y=y)
        self.tooltip.lift() # Ensure tooltip is on top

    def _hide_tooltip(self, event=None):
        """Hide the tooltip."""
        self.tooltip.place_forget()