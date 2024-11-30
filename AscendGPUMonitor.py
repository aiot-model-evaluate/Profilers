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
    
    # +------------------------------------------------------------------------------------------------+
    # | npu-smi 23.0.rc2                 Version: 23.0.rc2                                             |
    # +---------------------------+---------------+----------------------------------------------------+
    # | NPU   Name                | Health        | Power(W)    Temp(C)           Hugepages-Usage(page)|
    # | Chip                      | Bus-Id        | AICore(%)   Memory-Usage(MB)  HBM-Usage(MB)        |
    # +===========================+===============+====================================================+
    # | 3     910A                | OK            | 62.2        26                0    / 0             |
    # | 0                         | 0000:01:00.0  | 0           2280 / 15039      0    / 32768         |
    # +===========================+===============+====================================================+
    # +---------------------------+---------------+----------------------------------------------------+
    # | NPU     Chip              | Process id    | Process name             | Process memory(MB)      |
    # +===========================+===============+====================================================+
    # | No running processes found in NPU 3                                                            |
    # +===========================+===============+====================================================+

    def get_gpu_info(self):
        result = os.popen('npu-smi info')
        res = result.read()
        lines = res.splitlines()
        line1 = lines[6]
        line2 = lines[7]
        # ['3', '910', '62.5', '26', '0', '0']
        temp1 = re.findall(r'\d+\.?\d*', line1)
        # ['0', '0000', '01', '00.0', '0', '2280', '15039', '0', '32768']
        temp2 = re.findall(r'\d+\.?\d*', line2)
        
        power_usage = temp1[2]
        temperature = temp1[3]
        gpu_utilization = temp2[4]
        memory_used = temp2[7]
        memory_total = temp2[8]
        memory_free = str(int(memory_total) - int(memory_used))
        memory_util = (int(memory_used) / int(memory_total)) * 100
        
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