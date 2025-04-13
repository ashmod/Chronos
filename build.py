#!/usr/bin/env python3
import os
import sys
import shutil
import PyInstaller.__main__

def build_executable():
    """
    Build an executable file for the CPU Scheduler application.
    """
    print("Building CPU Scheduler executable...")
    
    # Clean up previous build if exists
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("CPU_Scheduler.spec"):
        os.remove("CPU_Scheduler.spec")
    
    # Build the executable
    PyInstaller.__main__.run([
        'main.py',
        '--name=CPU_Scheduler',
        '--onefile',
        '--windowed',
        '--icon=docs/icon.ico',  # You'll need to create an icon file
        '--add-data=src;src',
        '--clean',
    ])
    
    print("Build completed. Executable is in the 'dist' folder.")

if __name__ == "__main__":
    build_executable()