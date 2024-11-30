import os
import re
import threading
import time
from typing import List

class GPUMonitor:
    def __init__(self, device_index:int=0, interval=1, filename:str = None):
        self.device_index = device_index
        self.interval = interval
        self.__stop_event = threading.Event()
        self.filename = filename
        self.__monitor_thread = None
        if self.filename is not None:  # 清空存储文件
            with open(filename, 'w') as f:
                f.write("")
        print("Initialized GPUMonitor")

    def write(self, message: str):
        if self.filename is not None:
            with open(self.filename, 'a') as f:
                f.write(message + '\n')
        else:
            print(message)
    
    def get_gpu_info(self):
        result = os.popen('ixsmi')
        res = result.read()
        lines = res.splitlines()
        device_line = 8 + self.device_index * 3
        data = lines[device_line]
        temp = re.findall(r'\d+', data)
        gpu_utilization = temp[7]
        memory_total = temp[6]
        memory_used = temp[5]
        memory_free = str(int(memory_total) - int(memory_used))
        power_usage = temp[3]
        memory_util = int(memory_used) / int(memory_total) * 100
        temperature = temp[1]
        timestamp = time.time()
        info = {
            'GPU Utilization (%)': gpu_utilization,
            'Memory Utilization (%)': memory_util,
            'Total Memory (MiB)': memory_total,
            'Used Memory (MiB)': memory_used,
            'Free Memory (MiB)': memory_free,
            'Power Usage (W)': power_usage,
            'Temperature (C)': temperature
        }
        return timestamp, info

    def monitor_gpu(self):
        _, base_info = self.get_gpu_info()
        self.write(f"Baseline: {base_info}")
        while not self.__stop_event.is_set():
            timestamp, info = self.get_gpu_info()
            self.write(f"{timestamp}: {info}")
            time.sleep(self.interval)

    def start_monitoring(self):
        self.__monitor_thread = threading.Thread(target=self.monitor_gpu)
        self.__monitor_thread.start()
        print("Monitoring started")

    def stop_monitoring(self):
        self.__stop_event.set()
        self.__monitor_thread.join()
        print("Monitoring stopped")

    def cleanup(self):
        print("Shutdown Monitor")