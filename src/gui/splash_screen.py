from PyQt5.QtWidgets import QSplashScreen, QLabel, QVBoxLayout, QWidget, QProgressBar, QApplication
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSize, QRectF
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QLinearGradient, QPen, QBrush, QRadialGradient

class SplashScreen(QSplashScreen):
    """
    Enhanced splash screen with animated elements and progress indicator.
    """
    
    finished = pyqtSignal()
    
    def __init__(self, app_name="ProcessPilot", dark_mode=True):
        """
        Initialize the splash screen.
        
        Args:
            app_name (str): Application name to display
            dark_mode (bool): Whether to use dark mode styling
        """
        # Create a pixmap for the splash screen
        size = QSize(600, 400)
        self.pixmap = QPixmap(size)
        self.pixmap.fill(Qt.transparent)  # Start with transparent background
        
        # Initialize splash screen with the pixmap
        super().__init__(self.pixmap)
        
        # Set window flags for a borderless, always-on-top splash
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        
        # Store parameters
        self.app_name = app_name
        self.dark_mode = dark_mode
        self.progress = 0
        self.loading_text = "Loading..."
        
        # Configure animation timers
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_timer.start(15)  # Update every 15ms
        
        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self.update_progress)
        self.progress_timer.start(30)  # Update every 30ms
        
        # Initialize animation variables
        self.animation_step = 0
        self.cpu_angle = 0
        
        # Draw initial splash screen
        self.draw_splash()
    
    def draw_splash(self):
        """Draw the splash screen with current state."""
        # Create a new pixmap and painter
        self.pixmap = QPixmap(600, 400)
        self.pixmap.fill(Qt.transparent)
        
        painter = QPainter(self.pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Set colors based on theme
        bg_color = QColor("#1E1E1E") if self.dark_mode else QColor("#F0F0F0")
        text_color = QColor("#FFFFFF") if self.dark_mode else QColor("#333333")
        accent_color = QColor("#4A90E2")
        highlight_color = QColor("#66BB6A")
        
        # Draw background with rounded corners and gradient
        painter.setPen(Qt.NoPen)
        gradient = QLinearGradient(0, 0, 600, 400)
        if self.dark_mode:
            gradient.setColorAt(0, QColor("#2B2B2B"))
            gradient.setColorAt(1, QColor("#1A1A1A"))
        else:
            gradient.setColorAt(0, QColor("#F9F9F9"))
            gradient.setColorAt(1, QColor("#E0E0E0"))
        
        painter.setBrush(gradient)
        painter.drawRoundedRect(0, 0, 600, 400, 15, 15)
        
        # Draw app name with shadow
        app_name_font = QFont("Segoe UI", 36, QFont.Bold)
        painter.setFont(app_name_font)
        
        # Draw text shadow
        painter.setPen(QColor(0, 0, 0, 50))
        painter.drawText(52, 102, self.app_name)
        
        # Draw main text
        painter.setPen(accent_color)
        painter.drawText(50, 100, self.app_name)
        
        # Draw tagline
        tagline_font = QFont("Segoe UI", 14)
        painter.setFont(tagline_font)
        painter.setPen(text_color)
        painter.drawText(51, 130, "CPU Scheduler Visualization")
        
        # Draw CPU icon
        self.draw_cpu_icon(painter, 300, 200, 100, highlight_color, accent_color)
        
        # Draw progress bar
        self.draw_progress_bar(painter, 150, 320, 300, 15, self.progress, accent_color)
        
        # Draw loading text
        loading_font = QFont("Segoe UI", 10)
        painter.setFont(loading_font)
        painter.setPen(text_color)
        painter.drawText(150, 315, self.loading_text)
        
        # Draw version
        version_font = QFont("Segoe UI", 9)
        painter.setFont(version_font)
        painter.setPen(QColor(text_color.red(), text_color.green(), text_color.blue(), 180))
        painter.drawText(550, 380, "v1.0.0")
        
        painter.end()
        
        # Update the splash screen with the new pixmap
        self.setPixmap(self.pixmap)
    
    def draw_cpu_icon(self, painter, x, y, size, color1, color2):
        """Draw an animated CPU icon."""
        # Save the painter state
        painter.save()
        
        # Move to center position
        painter.translate(x, y)
        painter.rotate(self.cpu_angle)  # Rotate based on animation step
        
        # CPU body - using QRectF for drawing
        painter.setPen(QPen(color1.lighter(120), 2))
        painter.setBrush(QBrush(color1.darker(120)))
        # Convert floating point coordinates to integers
        half_size = int(size/2)
        painter.drawRoundedRect(-half_size, -half_size, size, size, 10, 10)
        
        # CPU inner square
        painter.setPen(QPen(color2, 2))
        painter.setBrush(QBrush(color2.darker(110)))
        inner_size = int(size * 0.6)
        inner_half = int(inner_size/2)
        painter.drawRoundedRect(-inner_half, -inner_half, inner_size, inner_size, 5, 5)
        
        # CPU pins (animated)
        painter.setPen(QPen(color1, 3))
        
        # Calculate pin length for animation effect
        pin_length = size * 0.2 + (size * 0.05) * abs(self.animation_step % 20 - 10) / 10.0
        pin_offset = size * 0.3
        
        # Draw pins on all sides with varying lengths for animation effect
        # Top pins
        for i in range(-2, 3):
            x_offset = int(i * pin_offset / 2)
            y_offset = int(-half_size - pin_length * (1 + 0.2 * abs(i)/2))
            painter.drawLine(x_offset, -half_size, x_offset, y_offset)
        
        # Bottom pins
        for i in range(-2, 3):
            x_offset = int(i * pin_offset / 2)
            y_offset = int(half_size + pin_length * (1 + 0.2 * abs(i)/2))
            painter.drawLine(x_offset, half_size, x_offset, y_offset)
        
        # Left pins
        for i in range(-2, 3):
            y_offset = int(i * pin_offset / 2)
            x_offset = int(-half_size - pin_length * (1 + 0.2 * abs(i)/2))
            painter.drawLine(-half_size, y_offset, x_offset, y_offset)
        
        # Right pins
        for i in range(-2, 3):
            y_offset = int(i * pin_offset / 2)
            x_offset = int(half_size + pin_length * (1 + 0.2 * abs(i)/2))
            painter.drawLine(half_size, y_offset, x_offset, y_offset)
        
        # Restore the painter state
        painter.restore()
    
    def draw_progress_bar(self, painter, x, y, width, height, progress, color):
        """Draw a progress bar with the given parameters."""
        # Draw background
        painter.setPen(Qt.NoPen)
        bg_color = QColor("#333333") if self.dark_mode else QColor("#E0E0E0")
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(x, y, width, height, height/2, height/2)
        
        # Draw progress
        if progress > 0:
            progress_width = int(width * progress / 100)
            gradient = QLinearGradient(x, y, x + progress_width, y)
            gradient.setColorAt(0, color.lighter(120))
            gradient.setColorAt(1, color)
            painter.setBrush(QBrush(gradient))
            painter.drawRoundedRect(x, y, progress_width, height, height/2, height/2)
    
    def update_animation(self):
        """Update animation parameters."""
        self.animation_step += 1
        self.cpu_angle = (self.cpu_angle + 0.5) % 360
        
        # Update loading text with animated dots
        dots = "." * ((self.animation_step // 10) % 4)
        self.loading_text = f"Loading{dots}"
        
        # Redraw splash
        self.draw_splash()
    
    def update_progress(self):
        """Update progress bar."""
        self.progress += 2  # Increase by 2%
        
        # When progress is complete, emit the finished signal
        if self.progress >= 100:
            self.progress = 100
            self.progress_timer.stop()
            self.animation_timer.stop()
            
            # Wait a moment at 100% before emitting finished
            QTimer.singleShot(500, self.finished.emit)
    
    def set_message(self, message):
        """Set a custom message in the splash screen."""
        self.loading_text = message
        self.draw_splash()
        QApplication.processEvents()