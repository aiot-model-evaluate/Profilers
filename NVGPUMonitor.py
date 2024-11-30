import pynvml
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
        pynvml.nvmlInit()
        print("Initialized pynvml")

    def write(self, message: str):
        if self.filename is not None:
            with open(self.filename, 'a') as f:
                f.write(message + '\n')
        else:
            print(message)
    
    def get_gpu_info(self):
        handle = pynvml.nvmlDeviceGetHandleByIndex(self.device_index)
        utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
        memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        power_usage = pynvml.nvmlDeviceGetPowerUsage(handle)
        temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
        timestamp = time.time()
        info = {
            'GPU Utilization (%)': utilization.gpu,
            'Memory Utilization (%)': utilization.memory,
            'Total Memory (bytes)': memory_info.total,
            'Used Memory (bytes)': memory_info.used,
            'Free Memory (bytes)': memory_info.free,
            'Power Usage (mW)': power_usage,
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
        pynvml.nvmlShutdown()
        print("Shutdown pynvml")
