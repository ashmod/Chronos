from collections import deque

class Scheduler:
    @staticmethod
    def fcfs(processes):
        if not processes:
            return []
        
        sorted_processes = sorted(processes, key=lambda x: (x[1], x[0]))  # Sort by arrival time, then PID
        current_time = 0
        timeline = []
        
        for pid, arrival, burst, _ in sorted_processes:
            start_time = max(current_time, arrival)
            end_time = start_time + burst
            timeline.append((pid, start_time, end_time))
            current_time = end_time
            
        return timeline
    
    @staticmethod
    def sjf(processes):
        if not processes:
            return []
        
        time = min(p[1] for p in processes) if processes else 0
        remaining = [(pid, arrival, burst, prio) for pid, arrival, burst, prio in processes]
        timeline = []
        
        while remaining:
            available = [(pid, burst) for pid, arrival, burst, _ in remaining if arrival <= time]
            if not available:
                time = min(arrival for _, arrival, _, _ in remaining)
                continue
                
            pid, burst = min(available, key=lambda x: x[1])
            timeline.append((pid, time, time + burst))
            time += burst
            remaining.remove(next(p for p in remaining if p[0] == pid))
            
        return timeline
    
    @staticmethod
    def priority(processes):
        if not processes:
            return []
        
        time = min(p[1] for p in processes) if processes else 0
        remaining = [(pid, arrival, burst, prio) for pid, arrival, burst, prio in processes]
        timeline = []
        
        while remaining:
            available = [(pid, prio) for pid, arrival, _, prio in remaining if arrival <= time]
            if not available:
                time = min(arrival for _, arrival, _, _ in remaining)
                continue
                
            pid, _ = min(available, key=lambda x: x[1])
            process = next(p for p in remaining if p[0] == pid)
            timeline.append((pid, time, time + process[2]))
            time += process[2]
            remaining.remove(process)
            
        return timeline
    
    @staticmethod
    def round_robin(processes, quantum):
        if not processes:
            return []
        
        time = min(p[1] for p in processes) if processes else 0
        queue = deque()
        remaining = {pid: burst for pid, _, burst, _ in processes}
        arrival_times = {pid: arrival for pid, arrival, _, _ in processes}
        timeline = []
        
        while remaining or queue:
            # Add newly arrived processes to queue
            for pid, arrival in arrival_times.items():
                if arrival <= time and pid in remaining:
                    if pid not in queue:
                        queue.append(pid)
            
            if not queue:
                time = min(t for t in arrival_times.values() if arrival_times[pid] > time)
                continue
            
            current_pid = queue.popleft()
            if current_pid in remaining:
                exec_time = min(quantum, remaining[current_pid])
                timeline.append((current_pid, time, time + exec_time))
                remaining[current_pid] -= exec_time
                time += exec_time
                
                if remaining[current_pid] > 0:
                    queue.append(current_pid)
                else:
                    del remaining[current_pid]
                    
        return timeline 