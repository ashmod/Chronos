#!/usr/bin/env python3
import sys
from PyQt5.QtWidgets import QApplication
from src.gui.main_window import MainWindow

def main():
    """Main entry point for the CPU Scheduler application."""
    app = QApplication(sys.argv)
    
    # Note: Meta-type registration for QVector<int> is removed
    # If signal/slot connection issues occur with collection types,
    # use a different approach like converting to Python lists
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()