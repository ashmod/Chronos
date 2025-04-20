import os
from PyQt5.QtWidgets import (QMainWindow, QAction, QApplication, 
                           QToolBar, QToolButton, QMessageBox, 
                           QStyleFactory, QLabel, QWidget, QStyle)
from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QIcon, QPalette, QColor, QFont, QPixmap, QPainter, QBrush, QPen

from .scene_manager import SceneManager

class MainWindow(QMainWindow):
    """
    Main window implementation using the scene-based architecture.
    """
    
    def __init__(self):
        super().__init__()
        
        # Set the application name
        self.app_name = "ProcessPilot"
        
        # Initialize state
        self.dark_mode = True  # Default to dark mode
        
        # Setup UI
        self.setup_ui()
        
        # Start maximized
        self.showMaximized()
        
    def setup_ui(self):
        """Setup the main window UI."""
        # Set window properties
        self.setWindowTitle(f"{self.app_name} - CPU Scheduler Visualization")
        self.setMinimumSize(1200, 800)
        
        # Create logo icon (generated on the fly)
        self.app_icon = self.create_app_icon()
        self.setWindowIcon(self.app_icon)
        
        # Setup menu bar with enhanced styling
        self.setup_menu()
        
        # Setup toolbar with improved icons and animations
        self.setup_toolbar()
        
        # Create and set the scene manager as central widget
        self.scene_manager = SceneManager()
        self.setCentralWidget(self.scene_manager)
        
        # Setup enhanced status bar
        self.setup_status_bar()
        
        # Apply initial theme
        self.apply_styles(self.dark_mode)
    
    def create_app_icon(self, size=64):
        """Create an app icon programmatically."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Define colors
        primary_color = QColor("#4A90E2")
        secondary_color = QColor("#66BB6A")
        
        # Draw rounded square background
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(primary_color))
        painter.drawRoundedRect(2, 2, size-4, size-4, 12, 12)
        
        # Draw CPU square
        painter.setPen(QPen(QColor("#FFFFFF"), 2))
        painter.setBrush(QBrush(secondary_color))
        cpu_size = int(size * 0.6)  # Convert to integer
        cpu_x = int((size - cpu_size) / 2)  # Convert to integer
        cpu_y = int((size - cpu_size) / 2)  # Convert to integer
        painter.drawRoundedRect(cpu_x, cpu_y, cpu_size, cpu_size, 6, 6)
        
        # Draw CPU pins
        painter.setPen(QPen(QColor("#FFFFFF"), 2))
        pin_length = int(size * 0.12)  # Convert to integer
        
        # Top pins
        for i in range(3):
            x = int(cpu_x + cpu_size * (0.25 + i * 0.25))  # Convert to integer
            painter.drawLine(x, cpu_y, x, cpu_y - pin_length)
        
        # Bottom pins
        for i in range(3):
            x = int(cpu_x + cpu_size * (0.25 + i * 0.25))  # Convert to integer
            painter.drawLine(x, cpu_y + cpu_size, x, cpu_y + cpu_size + pin_length)
        
        # Left pins
        for i in range(3):
            y = int(cpu_y + cpu_size * (0.25 + i * 0.25))  # Convert to integer
            painter.drawLine(cpu_x, y, cpu_x - pin_length, y)
        
        # Right pins
        for i in range(3):
            y = int(cpu_y + cpu_size * (0.25 + i * 0.25))  # Convert to integer
            painter.drawLine(cpu_x + cpu_size, y, cpu_x + cpu_size + pin_length, y)
        
        # Draw 'P' letter in the center
        painter.setPen(QColor("#FFFFFF"))
        font = QFont("Arial", int(size * 0.4), QFont.Bold)
        painter.setFont(font)
        painter.drawText(int(size * 0.37), int(size * 0.62), "P")
        
        painter.end()
        return QIcon(pixmap)
        
    def setup_menu(self):
        """Setup the application menu with enhanced styling."""
        # Create menu bar
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: transparent;
                spacing: 5px;
                padding: 5px 10px;
                font-size: 10pt;
            }
            QMenuBar::item {
                background: transparent;
                padding: 5px 10px;
                border-radius: 4px;
                margin-right: 3px;
            }
            QMenuBar::item:selected {
                background-color: rgba(74, 144, 226, 0.2);
            }
            QMenuBar::item:pressed {
                background-color: rgba(74, 144, 226, 0.3);
            }
        """)
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # New simulation action
        new_action = QAction(self.style().standardIcon(QStyle.SP_FileIcon), "&New Simulation", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(lambda: self.scene_manager.show_scene("welcome"))
        file_menu.addAction(new_action)
        
        # Import processes action
        import_action = QAction(self.style().standardIcon(QStyle.SP_DialogOpenButton), "&Import Processes...", self)
        import_action.setShortcut("Ctrl+I")
        import_action.triggered.connect(lambda: self.scene_manager.show_scene("process_input", "load"))
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        # Export results action
        export_action = QAction(self.style().standardIcon(QStyle.SP_DialogSaveButton), "&Export Results...", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.on_export_results)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction(self.style().standardIcon(QStyle.SP_DialogCloseButton), "E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        # Toggle dark mode action
        self.dark_mode_action = QAction(self.style().standardIcon(QStyle.SP_DesktopIcon), "&Light Mode", self)
        self.dark_mode_action.setCheckable(True)
        self.dark_mode_action.toggled.connect(self.toggle_theme)
        view_menu.addAction(self.dark_mode_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        # About action
        about_action = QAction(self.style().standardIcon(QStyle.SP_MessageBoxInformation), "&About", self)
        about_action.triggered.connect(self.on_about)
        help_menu.addAction(about_action)
        
    def setup_toolbar(self):
        """Setup the application toolbar with enhanced styling."""
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(32, 32))
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        toolbar.setObjectName("mainToolbar")
        toolbar.setStyleSheet("""
            QToolBar {
                spacing: 10px;
                padding: 5px;
                border: none;
            }
            QToolButton {
                border-radius: 6px;
                padding: 6px;
                margin: 2px 5px;
                min-width: 80px;
            }
            QToolButton:hover {
                background-color: rgba(74, 144, 226, 0.2);
            }
            QToolButton:pressed {
                background-color: rgba(74, 144, 226, 0.3);
            }
        """)
        
        # Add logo to toolbar
        logo_label = QLabel()
        logo_pixmap = self.create_app_icon(48).pixmap(48, 48)
        logo_label.setPixmap(logo_pixmap)
        logo_label.setContentsMargins(10, 0, 10, 0)
        toolbar.addWidget(logo_label)
        
        # Add app name
        app_name_label = QLabel(f"<b>{self.app_name}</b>")
        app_name_label.setStyleSheet("font-size: 14pt; padding-right: 20px;")
        toolbar.addWidget(app_name_label)
        
        # Theme toggle button with custom styling
        self.theme_button = QToolButton()
        
        # Load icons from resources
        sun_icon_path = os.path.join(os.path.dirname(__file__), "resources", "sun.svg")
        moon_icon_path = os.path.join(os.path.dirname(__file__), "resources", "moon.svg")
        
        self.sun_icon = QIcon(sun_icon_path)
        self.moon_icon = QIcon(moon_icon_path)
        
        # Set initial icon based on theme - sun for dark mode, moon for light mode
        self.theme_button.setIcon(self.sun_icon if self.dark_mode else self.moon_icon)
        self.theme_button.setText("Light Mode" if self.dark_mode else "Dark Mode")
        self.theme_button.setIconSize(QSize(28, 28))
        self.theme_button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.theme_button.setCheckable(True)
        self.theme_button.setChecked(not self.dark_mode)
        self.theme_button.toggled.connect(self.toggle_theme)
        toolbar.addWidget(self.theme_button)
        
        toolbar.addSeparator()
        
        # Navigation buttons with improved icons
        welcome_action = QAction(self.style().standardIcon(QStyle.SP_DialogHelpButton), "Home", self)
        welcome_action.triggered.connect(lambda: self.scene_manager.show_scene("welcome"))
        toolbar.addAction(welcome_action)
        
        processes_action = QAction(self.style().standardIcon(QStyle.SP_FileDialogListView), "Processes", self)
        processes_action.triggered.connect(lambda: self.scene_manager.show_scene("process_input"))
        toolbar.addAction(processes_action)
        
        simulation_action = QAction(self.style().standardIcon(QStyle.SP_MediaPlay), "Simulation", self)
        simulation_action.triggered.connect(lambda: self.scene_manager.show_scene("simulation"))
        toolbar.addAction(simulation_action)
        
        results_action = QAction(self.style().standardIcon(QStyle.SP_FileDialogDetailedView), "Results", self)
        results_action.triggered.connect(lambda: self.scene_manager.show_scene("results"))
        toolbar.addAction(results_action)
    
    def setup_status_bar(self):
        """Setup enhanced status bar with app info and animations."""
        statusbar = self.statusBar()
        statusbar.setStyleSheet("""
            QStatusBar {
                border-top: 1px solid rgba(120, 120, 120, 0.2);
                padding: 3px;
                font-size: 9pt;
            }
            QStatusBar QLabel {
                padding: 0 10px;
            }
        """)
        statusbar.showMessage("Ready")
        
        # Add version and author info
        version_label = QLabel("v1.0.0")
        statusbar.addPermanentWidget(version_label)
        
        # Add CPU usage indicator (placeholder)
        cpu_label = QLabel("ASU OS Team")
        statusbar.addPermanentWidget(cpu_label)
    
    def toggle_theme(self, state):
        """Toggle between light and dark theme."""
        self.dark_mode = not state  # state is True for light mode, False for dark mode
        self.apply_styles(self.dark_mode)
        
        # Update the theme button
        self.theme_button.setIcon(self.sun_icon if self.dark_mode else self.moon_icon)
        self.theme_button.setText("Light Mode" if self.dark_mode else "Dark Mode")
        self.theme_button.setChecked(not self.dark_mode)
        
        # Update menu action text
        self.dark_mode_action.setText("&Light Mode" if self.dark_mode else "&Dark Mode")
        self.dark_mode_action.setChecked(not self.dark_mode)
        
        # Update scene manager dark mode
        self.scene_manager.set_dark_mode(self.dark_mode)
        
    def apply_styles(self, dark_mode):
        """Apply styling to the application based on the selected theme."""
        # Common font
        font = QFont("Segoe UI", 10) # Use a standard modern font
        QApplication.setFont(font)

        # Define color palettes with improved contrast
        dark_colors = {
            "window": "#1E1E1E",             # Darker background for better contrast
            "base": "#212121",               # Dark base
            "alternate_base": "#272727",     # Slightly lighter for alternating rows
            "button": "#3E3E3E",             # Dark buttons
            "button_hover": "#4A4A4A",       # Button hover state
            "button_pressed": "#353535",     # Button pressed state
            "text": "#F0F0F0",               # Brighter text for better readability
            "highlight": "#4A90E2",          # Blue highlight
            "highlighted_text": "#FFFFFF",   # White text on highlights
            "border": "#505050",             # Border color
            "group_bg": "#2F2F2F",           # Group background
            "group_title": "#77C6FF",        # Group title color
            "red": "#F44336",                # Brighter red for better visibility
            "red_hover": "#EF5350",          # Red hover
            "green": "#4CAF50",              # Brighter green
            "green_hover": "#66BB6A",        # Green hover
            "blue": "#2196F3",               # Brighter blue
            "blue_hover": "#42A5F5",         # Blue hover
            "amber": "#FFC107",              # Amber/yellow
            "amber_hover": "#FFCA28",        # Amber hover
            "purple": "#9C27B0",             # Brighter purple
            "purple_hover": "#AB47BC",       # Purple hover
            "slider_groove": "#404040",      # Slider track
            "slider_handle": "#77C6FF",      # Slider handle
            "slider_handle_border": "#4A90E2", # Slider handle border
            "table_header": "#3A3A3A",       # Table header
            "scrollbar_bg": "#333333",       # Scrollbar background
            "scrollbar_handle": "#555555",   # Scrollbar handle
            "scrollbar_handle_hover": "#666666", # Scrollbar hover
        }

        light_colors = {
            "window": "#F9F9F9",             # Very light background
            "base": "#FFFFFF",               # White base
            "alternate_base": "#F5F5F5",     # Slightly darker for alternating rows
            "button": "#E0E0E0",             # Light button
            "button_hover": "#D0D0D0",       # Button hover
            "button_pressed": "#C0C0C0",     # Button pressed
            "text": "#212121",               # Very dark text for better contrast
            "highlight": "#1976D2",          # Darker blue for better contrast on light
            "highlighted_text": "#FFFFFF",   # White text on highlights
            "border": "#BDBDBD",             # Border color
            "group_bg": "#FFFFFF",           # Group background
            "group_title": "#1565C0",        # Group title color
            "red": "#D32F2F",                # Darker red for better contrast on light
            "red_hover": "#C62828",          # Red hover
            "green": "#388E3C",              # Darker green
            "green_hover": "#2E7D32",        # Green hover
            "blue": "#1565C0",               # Darker blue
            "blue_hover": "#0D47A1",         # Blue hover
            "amber": "#F57C00",              # Darker amber for better contrast on light
            "amber_hover": "#EF6C00",        # Amber hover
            "purple": "#7B1FA2",             # Darker purple 
            "purple_hover": "#6A1B9A",       # Purple hover
            "slider_groove": "#E0E0E0",      # Slider track
            "slider_handle": "#1976D2",      # Slider handle
            "slider_handle_border": "#1565C0", # Slider border
            "table_header": "#EAEAEA",       # Table header
            "scrollbar_bg": "#F0F0F0",       # Scrollbar background
            "scrollbar_handle": "#BDBDBD",   # Scrollbar handle
            "scrollbar_handle_hover": "#9E9E9E", # Scrollbar hover
        }

        colors = dark_colors if dark_mode else light_colors
        # Ensure good contrast for text on colored buttons
        button_text_color = "#FFFFFF" # White generally works well on colored buttons
        # Amber/Yellow needs dark text in light mode for readability
        amber_button_text_color = "#FFFFFF" if dark_mode else "#212121"

        app = QApplication.instance()
        app.setStyle(QStyleFactory.create("Fusion"))

        # Apply palette colors
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(colors["window"]))
        palette.setColor(QPalette.WindowText, QColor(colors["text"]))
        palette.setColor(QPalette.Base, QColor(colors["base"]))
        palette.setColor(QPalette.AlternateBase, QColor(colors["alternate_base"]))
        palette.setColor(QPalette.ToolTipBase, QColor(colors["base"]))
        palette.setColor(QPalette.ToolTipText, QColor(colors["text"]))
        palette.setColor(QPalette.Text, QColor(colors["text"]))
        palette.setColor(QPalette.Button, QColor(colors["button"]))
        palette.setColor(QPalette.ButtonText, QColor(colors["text"]))
        palette.setColor(QPalette.BrightText, QColor(colors["red"]))
        palette.setColor(QPalette.Link, QColor(colors["highlight"]))
        palette.setColor(QPalette.Highlight, QColor(colors["highlight"]))
        palette.setColor(QPalette.HighlightedText, QColor(colors["highlighted_text"]))
        
        # Set disabled colors for better visibility
        disabled_text_color = QColor(colors["text"]).lighter(150) if dark_mode else QColor(colors["text"]).darker(150)
        disabled_button_color = QColor(colors["button"]).lighter(110) if dark_mode else QColor(colors["button"]).darker(110)
        palette.setColor(QPalette.Disabled, QPalette.Text, disabled_text_color)
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, disabled_text_color)
        palette.setColor(QPalette.Disabled, QPalette.Button, disabled_button_color)

        app.setPalette(palette)

        # Rest of the stylesheet remains the same
        app.setStyleSheet(f"""\
            QMainWindow, QDialog {{
                background-color: {colors["window"]};
                color: {colors["text"]};
            }}
            QWidget {{ /* Apply font size globally */
                font-size: 10pt; /* Base font size */
            }}
            QGroupBox {{
                border: 1px solid {colors["border"]};
                border-radius: 8px;
                padding-top: 20px;
                margin-top: 10px;
                background-color: {colors["group_bg"]};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px 10px;
                margin-left: 12px;
                background-color: {colors["group_bg"]};
                color: {colors["group_title"]};
                font-weight: bold;
                font-size: 11pt;
                border-radius: 4px;
            }}

            /* Base Button Styles */
            QPushButton {{
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                border: 1px solid {colors["border"]};
                color: {colors["text"]};
                background-color: {colors["button"]};
                min-height: 30px;
                min-width: 70px;
            }}
            QPushButton:hover {{
                background-color: {colors["button_hover"]};
                border-color: {QColor(colors["border"]).lighter(120).name() if dark_mode else QColor(colors["border"]).darker(120).name()};
            }}
            QPushButton:pressed {{ background-color: {colors["button_pressed"]}; }}
            QPushButton:disabled {{
                background-color: {palette.color(QPalette.Disabled, QPalette.Button).name()};
                color: {palette.color(QPalette.Disabled, QPalette.ButtonText).name()};
                border-color: {colors["border"]};
            }}

            /* Button Colors by Function */
            /* Add Process Button - Green */
            QPushButton#add_process_button {{ background-color: {colors["green"]}; color: {button_text_color}; border-color: {colors["green"]}; }}
            QPushButton#add_process_button:hover {{ background-color: {colors["green_hover"]}; border-color: {colors["green_hover"]}; }}

            /* Remove/Reset Button - Red/Amber */
            QPushButton#remove_all_button {{ background-color: {colors["red"]}; color: {button_text_color}; border-color: {colors["red"]}; }}
            QPushButton#remove_all_button:hover {{ background-color: {colors["red_hover"]}; border-color: {colors["red_hover"]}; }}
            QPushButton#reset_button {{ background-color: {colors["amber"]}; color: {amber_button_text_color}; border-color: {colors["amber"]}; }}
            QPushButton#reset_button:hover {{ background-color: {colors["amber_hover"]}; border-color: {colors["amber_hover"]}; }}
            QPushButton#import_button, QPushButton#export_button {{ background-color: {colors["blue"]}; color: {button_text_color}; border-color: {colors["blue"]}; }}
            QPushButton#import_button:hover, QPushButton#export_button:hover {{ background-color: {colors["blue_hover"]}; border-color: {colors["blue_hover"]}; }}
            QPushButton#start_button {{ background-color: {colors["green"]}; color: {button_text_color}; border-color: {colors["green"]}; }}
            QPushButton#start_button:hover {{ background-color: {colors["green_hover"]}; border-color: {colors["green_hover"]}; }}
            QPushButton#pause_resume_button {{ background-color: {colors["amber"]}; color: {amber_button_text_color}; border-color: {colors["amber"]}; }}
            QPushButton#pause_resume_button:hover {{ background-color: {colors["amber_hover"]}; border-color: {colors["amber_hover"]}; }}
            QPushButton#run_all_button {{ background-color: {colors["purple"]}; color: {button_text_color}; border-color: {colors["purple"]}; }}
            QPushButton#run_all_button:hover {{ background-color: {colors["purple_hover"]}; border-color: {colors["purple_hover"]}; }}
            QPushButton#reset_gantt_button {{ background-color: {colors["blue"]}; color: {button_text_color}; border-color: {colors["blue"]}; }}
            QPushButton#reset_gantt_button:hover {{ background-color: {colors["blue_hover"]}; border-color: {colors["blue_hover"]}; }}

            /* Form Elements */
            QComboBox, QSpinBox, QLineEdit {{
                border: 1px solid {colors["border"]};
                border-radius: 6px;
                padding: 6px 10px;
                background-color: {colors["base"]};
                color: {colors["text"]};
                selection-background-color: {colors["highlight"]};
                selection-color: {colors["highlighted_text"]};
                min-height: 28px;
            }}
            QComboBox:hover, QSpinBox:hover, QLineEdit:hover {{
                border-color: {QColor(colors["border"]).lighter(120).name() if dark_mode else QColor(colors["border"]).darker(120).name()};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid {colors["border"]};
                border-top-right-radius: 5px;
                border-bottom-right-radius: 5px;
            }}
            QComboBox:on {{ /* When the combobox is open */
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
            }}
            QComboBox::item {{
                padding: 6px 10px;
            }}
            QComboBox::item:selected {{
                background-color: {colors["highlight"]};
                color: {colors["highlighted_text"]};
            }}

            /* SpinBox buttons */
            QSpinBox::up-button, QSpinBox::down-button {{
                 border-left: 1px solid {colors["border"]};
                 background-color: {colors["button"]};
                 border-radius: 0px;
            }}
            QSpinBox::up-button {{ subcontrol-position: top right; border-top-right-radius: 6px; }}
            QSpinBox::down-button {{ subcontrol-position: bottom right; border-bottom-right-radius: 6px; }}
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {{ background-color: {colors["button_hover"]}; }}
            QSpinBox::up-arrow {{ width: 12px; height: 12px; }}
            QSpinBox::down-arrow {{ width: 12px; height: 12px; }}

            /* Tabs */
            QTabWidget::pane {{
                border: 1px solid {colors["border"]};
                background-color: {colors["base"]}; /* Pane background */
                border-radius: 8px;
                border-top-left-radius: 0px; /* Align with tabs */
                margin-top: -1px; /* Overlap with tab bar */
                padding: 12px;
            }}
            QTabBar {{
                qproperty-drawBase: 0; /* Remove the default base line under the tabs */
                margin-bottom: -1px; /* Ensure tabs slightly overlap the pane */
                alignment: Qt.AlignLeft; /* Align tabs to the left */
            }}
            QTabBar::tab {{
                background-color: transparent; /* Make inactive tabs transparent */
                color: {QColor(colors["text"]).darker(130).name() if not dark_mode else QColor(colors["text"]).lighter(130).name()}; /* Dim inactive tab text more */
                border: 1px solid transparent; /* Transparent border initially */
                border-bottom: 2px solid {colors["border"]}; /* Slightly thicker underline for inactive tabs */
                padding: 10px 25px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 5px;
                min-width: 140px;
                font-weight: normal;
                font-size: 11pt;
            }}
            QTabBar::tab:selected {{
                background-color: {colors["base"]}; /* Match the tab panel background */
                color: {colors["highlight"]}; /* Highlight color for active tab text */
                border: 1px solid {colors["border"]}; /* Visible border for active tab */
                border-bottom: 2px solid {colors["highlight"]}; /* Highlight color for active tab underline */
                font-weight: bold; /* Make selected tab bold */
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {QColor(colors["button_hover"]).lighter(105).name() if dark_mode else QColor(colors["button_hover"]).darker(105).name()}; /* Subtle hover background */
                color: {colors["text"]}; /* Full text color on hover */
                border: 1px solid transparent; /* Keep border transparent on hover */
                border-bottom: 2px solid {QColor(colors["border"]).lighter(110).name() if dark_mode else QColor(colors["border"]).darker(110).name()}; /* Slightly change underline on hover */
            }}
            QTabBar::tab:last {{
                margin-right: 0; /* No margin for the last tab */
            }}

            /* Scrollbars */
            QScrollBar:vertical {{
                background-color: {colors["scrollbar_bg"]};
                width: 12px;
                margin: 0px 0px 0px 0px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {colors["scrollbar_handle"]};
                min-height: 30px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {colors["scrollbar_handle_hover"]};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
                background: none;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
             QScrollBar:horizontal {{
                background-color: {colors["scrollbar_bg"]};
                height: 12px;
                margin: 0px 0px 0px 0px;
                border-radius: 6px;
            }}
            QScrollBar::handle:horizontal {{
                background-color: {colors["scrollbar_handle"]};
                min-width: 30px;
                border-radius: 6px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: {colors["scrollbar_handle_hover"]};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
                background: none;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: none;
            }}

            /* Slider */
            QSlider::groove:horizontal {{
                height: 8px;
                background: {colors["slider_groove"]};
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {colors["slider_handle"]};
                border: 1px solid {colors["slider_handle_border"]};
                width: 18px;
                height: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {QColor(colors["slider_handle"]).lighter(115).name()};
                border: 1px solid {QColor(colors["slider_handle_border"]).lighter(115).name()};
            }}

            /* Tables */
            QTableWidget {{
                gridline-color: transparent; /* Hide grid lines */
                background-color: {colors["base"]};
                alternate-background-color: {colors["alternate_base"]};
                border: 1px solid {colors["border"]};
                border-radius: 8px;
                padding: 0px; /* Remove padding around the table itself */
                selection-background-color: {colors["highlight"]}; /* Explicit selection color */
                selection-color: {colors["highlighted_text"]};
            }}
            QHeaderView::section {{ /* Style for both horizontal and vertical headers */
                background-color: {colors["table_header"]};
                color: {colors["text"]};
                padding: 10px 8px; /* Increased padding */
                border: none; /* Remove default borders */
                font-weight: bold;
                font-size: 10pt;
            }}
            QHeaderView::section:horizontal {{
                border-bottom: 2px solid {colors["highlight"]}; /* Highlight bottom border */
                border-right: 1px solid {colors["border"]}; /* Separator line */
            }}
            QHeaderView::section:horizontal:last {{
                border-right: none; /* No right border for the last header */
            }}
            QTableWidget::item {{ /* Style for individual cells */
                padding: 8px; /* Add padding to cells */
                border-bottom: 1px solid {colors["border"]}; /* Subtle separator */
            }}

            /* Status styling - Bold status text, colored for importance */
            QTableWidget QTableWidgetItem[userRole="Running"] {{
                background-color: {QColor(colors['green']).lighter(150).name() if dark_mode else QColor(colors['green']).lighter(180).name()};
                color: {'#000000' if dark_mode else '#000000'}; /* Ensure contrast */
                font-weight: bold;
            }}
            QTableWidget QTableWidgetItem[userRole="Completed"] {{
                background-color: {QColor(colors['border']).lighter(105).name() if dark_mode else QColor(colors['border']).lighter(140).name()};
                color: {QColor(colors['text']).darker(130).name() if dark_mode else QColor(colors['text']).darker(160).name()};
                font-style: italic;
            }}
            QTableWidget QTableWidgetItem[userRole="Waiting"] {{
                background-color: {QColor(colors['amber']).lighter(150).name() if dark_mode else QColor(colors['amber']).lighter(180).name()};
                color: {'#000000' if dark_mode else '#000000'}; /* Ensure contrast */
            }}
            QTableWidget QTableWidgetItem[userRole="Not Arrived"] {{
                background-color: transparent;
                color: {QColor(colors['text']).darker(140).name() if dark_mode else QColor(colors['text']).darker(170).name()};
                font-style: italic;
            }}
            /* Summary Row Styling - Clearer separation */
            QTableWidget QTableWidgetItem[userRole="summary_label"] {{
                background-color: {QColor(colors["table_header"]).lighter(110).name() if dark_mode else QColor(colors["table_header"]).darker(105).name()};
                color: {colors["text"]};
                padding-right: 15px;
                border-top: 1px solid {colors["highlight"]}; /* Separator line above */
                border-bottom: none;
            }}
             QTableWidget QTableWidgetItem[userRole="summary_value"] {{
                background-color: {QColor(colors["table_header"]).lighter(110).name() if dark_mode else QColor(colors["table_header"]).darker(105).name()};
                color: {colors["highlight"]};
                border-top: 1px solid {colors["highlight"]}; /* Separator line above */
                border-bottom: none;
            }}

            /* Progress Bar in Table - More refined look */
            QTableView QProgressBar {{
                border: 1px solid {colors["border"]};
                border-radius: 6px; /* Slightly less rounded */
                background-color: {colors["base"]};
                text-align: center;
                color: {colors["text"]};
                font-size: 9pt;
                height: 18px; /* Consistent height */
                margin: 2px 0; /* Add slight vertical margin */
            }}
            QTableView QProgressBar::chunk {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {QColor(colors['highlight']).lighter(115).name()}, stop:1 {colors['highlight']});
                border-radius: 6px;
                margin: 1px; /* Add margin to chunk for inset effect */
            }}

            /* Remove Button in Table - More visible hover/pressed */
            QPushButton#remove_table_button {{
                background-color: {colors['red']}; /* Red background */
                color: {button_text_color}; /* White text */
                border: none;
                border-radius: 4px; /* Match other buttons */
                padding: 5px; /* Increased padding */
                qproperty-iconSize: 20px 20px; /* Slightly larger icon */
                margin: 0; /* Remove any default margin */
            }}
            QPushButton#remove_table_button:hover {{
                background-color: {colors['red_hover']};
            }}
            QPushButton#remove_table_button:pressed {{
                background-color: {QColor(colors['red']).darker(110).name()};
            }}
            
            /* Summary Row Styling - More distinct */
            QTableWidget QTableWidgetItem[userRole="summary_label"] {{
                background-color: {QColor(colors["table_header"]).lighter(110).name() if dark_mode else QColor(colors["table_header"]).darker(105).name()};
                color: {colors["text"]};
                font-weight: bold;
                font-size: 10pt;
            }}
            QTableWidget QTableWidgetItem[userRole="summary_value"] {{
                background-color: {QColor(colors["table_header"]).lighter(110).name() if dark_mode else QColor(colors["table_header"]).darker(105).name()};
                color: {colors["highlight"]};
                font-weight: bold;
                font-size: 10pt;
                border-top: 1px solid {colors["highlight"]}; /* Separator line above */
                border-bottom: none;
            }}
            
            /* Enhanced tooltip styling */
            QToolTip {{
                background-color: {colors["base"]};
                color: {colors["text"]};
                border: 1px solid {colors["border"]};
                border-radius: 4px;
                padding: 4px;
                font-size: 9pt;
            }}
        """)
        
    def on_export_results(self):
        """Redirect to results export functionality in the results scene."""
        # Switch to results scene and trigger export
        self.scene_manager.show_scene("results")
        results_scene = self.scene_manager.scenes.get("results")
        if results_scene:
            results_scene._export_results()
    
    def on_about(self):
        """Show the about dialog."""
        QMessageBox.about(
            self,
            f"About {self.app_name}",
            f"""
            <div align="center">
                <h1>{self.app_name}</h1>
                <p style="font-size: 14pt;">Advanced CPU Scheduler Visualization</p>
                <p>A modern, interactive tool for learning and visualizing CPU scheduling algorithms</p>
            </div>
            <p><b>Algorithms implemented:</b></p>
            <ul>
                <li>First-Come, First-Served (FCFS)</li>
                <li>Shortest Job First (SJF) - Non-Preemptive</li>
                <li>Shortest Remaining Time First (SRTF) - Preemptive</li>
                <li>Priority Scheduling - Non-Preemptive</li>
                <li>Priority Scheduling - Preemptive</li>
                <li>Round Robin (RR) with configurable time quantum</li>
            </ul>
            <p>Created as part of ASU Senior Project for Operating Systems course.</p>
            <p>© 2025 ASU Operation Systems Team. All rights reserved.</p>
            <p><small>Version 1.0.0</small></p>
            """
        )
    
    def closeEvent(self, event):
        """Handle application close event."""
        # Check if a simulation is running and confirm exit
        simulation_scene = self.scene_manager.scenes.get("simulation")
        if simulation_scene and simulation_scene.simulation_thread and simulation_scene.simulation_thread.isRunning():
            reply = QMessageBox.question(
                self,
                "Confirm Exit",
                "A simulation is currently running. Are you sure you want to exit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                event.ignore()
                return
        
        # Accept the close event and exit
        event.accept()