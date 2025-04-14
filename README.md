# CPU Scheduler Simulation

A desktop application that simulates various CPU scheduling algorithms with a live Gantt chart visualization.

## Features

- Supports multiple CPU scheduling algorithms:
  - First-Come, First-Served (FCFS)
  - Shortest Job First (Preemptive and Non-Preemptive)
  - Priority Scheduling (Preemptive and Non-Preemptive)
  - Round Robin
- Live visualization of the scheduling process
- Dynamic process addition during simulation
- Real-time statistics (average waiting time, average turnaround time)
- Process status tracking
- Interactive Gantt chart

## Requirements

- Python 3.6+
- PyQt5
- matplotlib

## Installation

1. Clone this repository
2. Install the required packages:
```
pip install -r requirements.txt
```

## Usage

### Running the Application

To run the application in development mode:
```
python main.py
```

### Building an Executable

To build a standalone executable:
```
python build.py
```
The executable will be created in the `dist` folder.

## How to Use

1. **Select a scheduling algorithm** from the dropdown menu
2. **Add processes** by specifying:
   - Process name
   - Arrival time
   - Burst time
   - Priority (for Priority scheduling)
3. **Control the simulation**:
   - Start: Begin the simulation
   - Pause/Resume: Control the simulation flow
   - Stop: End the simulation
   - Run All At Once: Complete the simulation instantly
   - Speed: Adjust simulation speed

## Screenshots

(Add screenshots here)

## Project Structure

- `src/models/`: Process model
- `src/core/`: Scheduler and simulation logic
- `src/algorithms/`: Different scheduling algorithms
- `src/gui/`: User interface components

## Team Members

- [Shehab Mahmoud](https://github.com/dizzydroid)
- [Abdelrahman Hany](https://github.com/DopeBiscuit)
- [Youssef Shahean](https://github.com/unauthorised-401)
- [Seif Ahmed](https://github.com/seifelwarwary)
- [Seif Tamer](https://github.com/SeifT101)
- [Omar Mamon](https://github.com/Spafic)

## License

[MIT License](./LICENSE)
