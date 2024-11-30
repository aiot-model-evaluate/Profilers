import asitop
import threading
import time
from typing import List
from asitop.utils import *

class GPUMonitor:
    def __init__(self, device_index:int=0, interval=1, filename:str = None):
        self.device_index = device_index
        self.interval = interval
        self.filename = filename
        self.__stop_event = threading.Event()
        self.__monitor_thread = None
        self.process_handle = None
        self.stop = True
        self.max_count = -1
        if self.filename is not None:  # 清空存储文件
            with open(filename, 'w') as f:
                f.write("")
        print("Initialized asitop")

    def write(self, message: str):
        if self.filename is not None:
            with open(self.filename, 'a') as f:
                f.write(message + '\n')
        else:
            print(message)
    
    def get_gpu_info(self, cpu_metrics_dict, gpu_metrics_dict, thermal_pressure, bandwidth_metrics, timestamp):
        mem_info = asitop.utils.get_ram_metrics_dict()
        info = {
            'GPU Utilization (%)': gpu_metrics_dict['active'],
            'Memory Utilization (%)': str((mem_info['used_GB'] / mem_info['total_GB']) * 100),
            'Total Memory (bytes)': str(mem_info['total_GB']*1024*1024*1024),
            'Used Memory (bytes)': str(mem_info['used_GB']*1024*1024*1024),
            'Free Memory (bytes)': str(mem_info['free_GB']*1024*1024*1024),
            'Power Usage (mW)': str(cpu_metrics_dict['package_W'] / self.interval),
        }
        # 将形如datetime.datetime()时间转换为time.time()格式的浮点数
        timestamp = time.mktime(timestamp.timetuple()) + 1e-6 * timestamp.microsecond
        return timestamp, info
    
    def monitor_gpu(self):
        timecode = str(int(time.time()))
        # 开启子进程
        powermetrics_process = run_powermetrics_process(timecode, interval=self.interval * 1000)

        print("\n[3/3] Waiting for first reading...\n")

        def get_reading(wait=0.1):
            ready = parse_powermetrics(timecode=timecode)
            while not ready:
                time.sleep(wait)
                ready = parse_powermetrics(timecode=timecode)
            return ready

        ready = get_reading()
        last_timestamp = ready[-1]

        while not self.__stop_event.is_set():
            ready = parse_powermetrics(timecode=timecode)
            if ready:
                cpu_metrics_dict, gpu_metrics_dict, thermal_pressure, bandwidth_metrics, timestamp = ready
                _timestamp, info = self.get_gpu_info(cpu_metrics_dict, gpu_metrics_dict, thermal_pressure, bandwidth_metrics, timestamp)
                self.write(f"{_timestamp}: {info}")
                
            time.sleep(self.interval)
        powermetrics_process.terminate()

    def start_monitoring(self):
        self.__monitor_thread = threading.Thread(target=self.monitor_gpu)
        self.__monitor_thread.start()
        print("Monitoring started")

    def stop_monitoring(self):
        self.__stop_event.set()
        self.__monitor_thread.join()
        print("Monitoring stopped")

    def cleanup(self):
        print("Shutdown asitop")
